"""aiconfig 命令行入口。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable

import tomlkit
import yaml

from .detect import detect_context
from .differ import diff_content
from .errors import ConfigError
from .importer import (
    build_import_plan,
    declaration_from_import_plan,
    dump_declaration,
    dump_import_plan,
    load_import_plan,
    parse_exclude_spec,
    parse_source_spec,
)
from .loader import find_config, load_config
from .renderer import output_path_for
from .state import classify_status, data_dir, hash_file, hash_text, load_state, save_state, state_path
from .validator import validate_declaration, validate_schema
from .writer import apply_content, atomic_write, backup_file, ensure_not_modified


SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = SKILL_ROOT / "assets"


def _add_context_arguments(parser: argparse.ArgumentParser, *, include_config: bool = True) -> None:
    if include_config:
        parser.add_argument("--config", type=Path, help="声明文件路径；默认向上查找 agent-config.yaml")
    parser.add_argument("--context", type=Path, help="本地上下文路径")
    parser.add_argument("--profile", help="覆盖本地 profile")
    parser.add_argument("--tag", action="append", help="覆盖本地 tags；可重复传入")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiconfig", description="声明式管理 Codex 与 Claude Code 用户配置")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="创建声明示例和本地上下文示例")
    init_parser.add_argument("--directory", type=Path, default=Path.cwd(), help="初始化目录")

    detect_parser = subparsers.add_parser("detect", help="检测当前机器上下文")
    _add_context_arguments(detect_parser, include_config=False)
    detect_parser.add_argument("--json", action="store_true", help="输出 JSON")

    for name, help_text in (
        ("validate", "校验声明和生成结果"),
        ("render", "渲染到 .agent-config/generated"),
        ("plan", "显示匹配、路径与差异"),
        ("status", "检查同步状态"),
    ):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.add_argument("target", nargs="?", choices=("codex", "claude"))
        _add_context_arguments(command_parser)
        if name == "render":
            command_parser.add_argument("--output-dir", type=Path, help="渲染目录")

    apply_parser = subparsers.add_parser("apply", help="备份并原子应用配置")
    apply_parser.add_argument("target", nargs="?", choices=("codex", "claude"))
    _add_context_arguments(apply_parser)
    apply_parser.add_argument("--force", action="store_true", help="覆盖上次应用后被手工修改的目标")

    import_parser = subparsers.add_parser("import", help="从现有配置生成可审阅的事实导入计划")
    import_subparsers = import_parser.add_subparsers(dest="import_command", required=True)
    inspect_parser = import_subparsers.add_parser("inspect", help="归并来源并生成导入计划")
    inspect_parser.add_argument(
        "--source",
        action="append",
        required=True,
        metavar="TARGET=PATH",
        help="配置来源；TARGET 为 codex 或 claude，可重复传入",
    )
    inspect_parser.add_argument(
        "--plan",
        type=Path,
        default=Path(".agent-config/import-plan.yaml"),
        help="导入计划路径",
    )
    inspect_parser.add_argument("--force", action="store_true", help="覆盖已有导入计划")

    generate_parser = import_subparsers.add_parser("generate", help="根据已确认的计划生成事实文件")
    generate_parser.add_argument(
        "--plan",
        type=Path,
        default=Path(".agent-config/import-plan.yaml"),
        help="导入计划路径",
    )
    generate_parser.add_argument("--output", type=Path, default=Path("agent-config.yaml"), help="事实文件路径")
    generate_parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="TARGET=/POINTER",
        help="额外剔除字段或子树，可重复传入",
    )
    generate_parser.add_argument("--force", action="store_true", help="备份并覆盖已有事实文件")

    ui_parser = subparsers.add_parser("ui", help="在本地浏览器中审阅导入计划")
    ui_parser.add_argument(
        "--plan",
        type=Path,
        default=Path(".agent-config/import-plan.yaml"),
        help="导入计划路径",
    )
    ui_parser.add_argument("--output", type=Path, default=Path("agent-config.yaml"), help="事实文件路径")
    ui_parser.add_argument("--port", type=int, default=8765, help="本地监听端口；0 表示自动分配")
    ui_parser.add_argument("--open", action="store_true", help="启动后打开默认浏览器")
    return parser


def _context_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return detect_context(
        context_file=args.context.resolve() if getattr(args, "context", None) else None,
        profile=getattr(args, "profile", None),
        tags=getattr(args, "tag", None),
    )


def _config_path(args: argparse.Namespace) -> Path:
    configured = getattr(args, "config", None)
    return configured.resolve() if configured else find_config()


def _target_names(declaration: dict[str, Any], requested: str | None) -> list[str]:
    if requested:
        if requested not in declaration["targets"]:
            raise ConfigError("CONFIG_SCHEMA_INVALID", f"声明中不存在目标：{requested}", location=f"targets.{requested}")
        return [requested]
    return [name for name in ("codex", "claude") if name in declaration["targets"]]


def _load_and_prepare(args: argparse.Namespace):
    config_path = _config_path(args)
    declaration = load_config(config_path)
    context = _context_from_args(args)
    targets = _target_names(declaration, getattr(args, "target", None))
    prepared, warnings = validate_declaration(declaration, context, targets)
    return config_path, declaration, context, targets, prepared, warnings


def _print_warnings(warnings: Iterable[str]) -> None:
    for warning in warnings:
        print(warning, file=sys.stderr)


def command_init(args: argparse.Namespace) -> int:
    directory = args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "agent-config.yaml"
    context_path = directory / ".agent-config" / "context.example.yaml"
    created: list[Path] = []
    for source, destination in (
        (ASSETS_DIR / "agent-config.example.yaml", config_path),
        (ASSETS_DIR / "context.example.yaml", context_path),
    ):
        if destination.exists():
            print(f"保留已有文件：{destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        created.append(destination)
        print(f"已创建：{destination}")

    context = detect_context()
    for label, path in (
        ("Codex", Path(context["home"]) / ".codex" / "config.toml"),
        ("Claude Code", Path(context["home"]) / ".claude" / "settings.json"),
    ):
        print(f"检测到已有 {label} 配置：{'是' if path.exists() else '否'} ({path})")
    return 0 if created or config_path.exists() else 1


def command_detect(args: argparse.Namespace) -> int:
    context = _context_from_args(args)
    if args.json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
        return 0
    for key in ("os", "runtime", "hostname", "user", "home", "profile"):
        print(f"{key}: {context.get(key)}")
    print("tags: " + (", ".join(context["tags"]) if context["tags"] else "[]"))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    _, _, _, targets, _, warnings = _load_and_prepare(args)
    _print_warnings(warnings)
    print("校验通过：" + ", ".join(targets))
    return 0


def _validate_rendered(target_name: str, content: str) -> Any:
    return tomlkit.parse(content) if target_name == "codex" else json.loads(content)


def command_render(args: argparse.Namespace) -> int:
    config_path, _, _, targets, prepared, warnings = _load_and_prepare(args)
    _print_warnings(warnings)
    output_dir = (args.output_dir or (config_path.parent / ".agent-config" / "generated")).resolve()
    filenames = {"codex": "config.toml", "claude": "settings.json"}
    for target_name in targets:
        destination = output_dir / filenames[target_name]
        content = prepared[target_name][2]
        atomic_write(destination, content, lambda text, name=target_name: _validate_rendered(name, text))
        print(f"已渲染 {target_name}：{destination}")
    return 0


def _print_context(context: dict[str, Any]) -> None:
    print("Context:")
    for key in ("os", "runtime", "hostname", "user", "home", "profile"):
        print(f"  {key}: {context.get(key)}")
    print("  tags: " + (", ".join(context["tags"]) if context["tags"] else "[]"))


def _manual_modification(target_name: str, path: Path, state: dict[str, Any]) -> str:
    record = state.get("targets", {}).get(target_name)
    if not path.exists() or not record:
        return "unknown"
    return "yes" if hash_file(path) != record.get("generatedHash") else "no"


def command_plan(args: argparse.Namespace) -> int:
    _, declaration, context, targets, prepared, warnings = _load_and_prepare(args)
    _print_warnings(warnings)
    current_state = load_state(state_path(context["home"]))
    _print_context(context)
    for target_name in targets:
        _, overlays, content = prepared[target_name]
        path = output_path_for(declaration, target_name, context)
        print(f"\nTarget: {target_name}")
        print(f"  output: {path}")
        print("  matched overlays: " + (" -> ".join(item["name"] for item in overlays) if overlays else "[]"))
        print(f"  local modification: {_manual_modification(target_name, path, current_state)}")
        print(f"  backup on apply: {'yes' if path.exists() else 'no'}")
        difference = diff_content(path, content)
        print("  diff: unchanged" if not difference else "  diff:\n" + difference.rstrip("\n"))
    return 0


def command_apply(args: argparse.Namespace) -> int:
    config_path, declaration, context, targets, prepared, warnings = _load_and_prepare(args)
    _print_warnings(warnings)
    state_file = state_path(context["home"])
    current_state = load_state(state_file)

    # 先检查全部目标，避免可预见冲突造成部分写入。
    for target_name in targets:
        path = output_path_for(declaration, target_name, context)
        ensure_not_modified(target_name, path, current_state, force=args.force)

    current_state.update(
        {
            "version": 1,
            "sourceFile": str(config_path),
            "sourceHash": hash_file(config_path),
        }
    )
    for target_name in targets:
        path = output_path_for(declaration, target_name, context)
        content = prepared[target_name][2]
        difference = diff_content(path, content)
        print(f"\nTarget: {target_name}\nPath: {path}")
        print("Diff: unchanged" if not difference else difference.rstrip("\n"))
        backup = apply_content(
            target_name,
            path,
            content,
            current_state,
            data_dir(context["home"]) / "backups",
            lambda text, name=target_name: _validate_rendered(name, text),
            force=args.force,
        )
        current_state.setdefault("targets", {})[target_name] = {
            "path": str(path),
            "generatedHash": hash_text(content),
        }
        # 每个目标成功后立即落状态，后续目标失败时也能准确识别已写入文件。
        save_state(state_file, current_state)
        print(f"已应用：{path}")
        print(f"备份：{backup}" if backup else "备份：无需创建（目标原先不存在）")

    print(f"状态：{state_file}")
    return 0


def command_status(args: argparse.Namespace) -> int:
    config_path, declaration, context, targets, prepared, warnings = _load_and_prepare(args)
    _print_warnings(warnings)
    current_state = load_state(state_path(context["home"]))
    source_is_current = current_state.get("sourceHash") == hash_file(config_path)
    for target_name in targets:
        path = output_path_for(declaration, target_name, context)
        status = classify_status(
            path,
            prepared[target_name][2],
            current_state.get("targets", {}).get(target_name),
            source_is_current=source_is_current,
            parse_current=lambda text, name=target_name: _validate_rendered(name, text),
        )
        print(f"{target_name}: {status} ({path})")
    return 0


def _yaml_parse(text: str) -> Any:
    return yaml.safe_load(text)


def _declaration_parse_and_validate(text: str) -> Any:
    value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "生成的事实文件顶层必须是对象。")
    validate_schema(value)
    return value


def command_import(args: argparse.Namespace) -> int:
    if args.import_command == "inspect":
        plan_path = args.plan.resolve()
        if plan_path.exists() and not args.force:
            raise ConfigError(
                "IMPORT_PLAN_EXISTS",
                "导入计划已存在；先审阅现有计划，明确同意后再使用 --force 覆盖。",
                location=str(plan_path),
            )
        plan = build_import_plan(parse_source_spec(source) for source in args.source)
        content = dump_import_plan(plan)
        backup = None
        if plan_path.exists():
            backup = backup_file("import-plan", plan_path, plan_path.parent / "backups")
        atomic_write(plan_path, content, _yaml_parse)
        print(f"已生成导入计划：{plan_path}")
        if backup:
            print(f"备份：{backup}")
        for target, target_plan in plan["targets"].items():
            counts: dict[str, int] = {}
            for item in target_plan["items"]:
                status = item["status"]
                counts[status] = counts.get(status, 0) + 1
            summary = ", ".join(f"{name}={count}" for name, count in counts.items())
            print(f"{target}: {summary or '无配置项'}")
        return 0

    if args.import_command == "generate":
        plan_path = args.plan.resolve()
        output_path = args.output.resolve()
        if output_path.exists() and not args.force:
            raise ConfigError(
                "IMPORT_OUTPUT_EXISTS",
                "事实文件已存在；先审阅现有文件，明确同意后再使用 --force 覆盖。",
                location=str(output_path),
            )
        plan = load_import_plan(plan_path)
        declaration = declaration_from_import_plan(
            plan,
            additional_excludes=[parse_exclude_spec(value) for value in args.exclude],
        )
        targets = [target for target in ("codex", "claude") if target in declaration["targets"]]
        validate_declaration(declaration, detect_context(), targets)
        content = dump_declaration(declaration)
        backup = None
        if output_path.exists():
            backup = backup_file("declaration", output_path, output_path.parent / ".agent-config" / "backups")
        atomic_write(output_path, content, _declaration_parse_and_validate)
        print(f"已生成事实文件：{output_path}")
        if backup:
            print(f"备份：{backup}")
        return 0

    raise ConfigError("IMPORT_PLAN_INVALID", f"未知导入命令：{args.import_command}")


def command_ui(args: argparse.Namespace) -> int:
    if not 0 <= args.port <= 65535:
        raise ConfigError("UI_SERVER_FAILED", "端口必须在 0 到 65535 之间。")
    from .webui import serve_ui

    serve_ui(args.plan.resolve(), args.output.resolve(), port=args.port, open_browser=args.open)
    return 0


COMMANDS = {
    "init": command_init,
    "detect": command_detect,
    "validate": command_validate,
    "render": command_render,
    "plan": command_plan,
    "apply": command_apply,
    "status": command_status,
    "import": command_import,
    "ui": command_ui,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except ConfigError as exc:
        print(exc.format(), file=sys.stderr)
        return 2
    except OSError as exc:
        print(ConfigError("TARGET_WRITE_FAILED", str(exc)).format(), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("操作已取消。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
