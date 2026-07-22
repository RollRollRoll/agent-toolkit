#!/usr/bin/env python3
"""以可移植、可恢复审计的方式驱动 Claude Code headless 会话。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_TOOLS = "Skill,Read,Write,Edit,Glob,Grep"
SAFE_DEFAULT_TOOLS = {"Skill", "Read", "Write", "Edit", "Glob", "Grep"}
FAIL_CLOSED_FLAGS = (
    ("--tools",),
    ("--allowedTools", "--allowed-tools"),
    ("--permission-mode",),
    ("--setting-sources",),
    ("--strict-mcp-config",),
    ("--mcp-config",),
    ("--settings",),
    ("--output-format",),
    ("--verbose",),
    ("--resume",),
)


class RunnerError(RuntimeError):
    """表示运行前即可确定的配置或状态错误。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RunnerError(f"缺少运行文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f"运行文件不是有效 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RunnerError(f"运行文件顶层必须是对象：{path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _resolve_executable(command: str) -> str:
    if os.sep in command:
        path = Path(command).expanduser().resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RunnerError(f"Claude CLI 不可执行：{path}")
        return str(path)
    resolved = shutil.which(command)
    if not resolved:
        raise RunnerError(f"找不到 Claude CLI：{command}")
    return resolved


def _run_probe(executable: str, argument: str) -> str:
    try:
        result = subprocess.run(
            [executable, argument],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RunnerError(f"Claude CLI 预检失败（{argument}）：{exc}") from exc
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RunnerError(
            f"Claude CLI 预检失败（{argument}，退出码 {result.returncode}）：{output}"
        )
    return output


def _probe_cli(command: str) -> dict[str, Any]:
    executable = _resolve_executable(command)
    version = _run_probe(executable, "--version")
    help_text = _run_probe(executable, "--help")
    # Claude Code 官方说明 `--help` 不保证列出全部参数，因此这里只记录可见性，
    # 不把“帮助文本没出现”误判为“不支持”。真正运行时仍带齐 fail-closed 参数；
    # 旧 CLI 若不支持会在发起模型请求前解析失败，且不得降级重试。
    missing = [
        "/".join(group)
        for group in FAIL_CLOSED_FLAGS
        if not any(flag in help_text for flag in group)
    ]
    allowed_flag = (
        "--allowed-tools"
        if "--allowed-tools" in help_text and "--allowedTools" not in help_text
        else "--allowedTools"
    )
    return {
        "executable": executable,
        "version": version,
        "allowed_tools_flag": allowed_flag,
        "flags_not_listed_by_help": missing,
    }


def _split_csv(raw: str, label: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise RunnerError(f"{label} 不得为空")
    if len(values) != len(set(values)):
        raise RunnerError(f"{label} 不得包含重复项")
    return values


def _validate_permissions(
    skill_name: str, tools_raw: str, allowed_raw: str | None
) -> tuple[list[str], list[str]]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", skill_name):
        raise RunnerError("skill 名只允许小写字母、数字和连字符，且最长 64 个字符")

    tools = _split_csv(tools_raw, "--tools")
    invalid_tools = [name for name in tools if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name)]
    if invalid_tools:
        raise RunnerError("--tools 只能填写工具名，不能填写权限模式：" + "、".join(invalid_tools))
    if "Skill" not in tools:
        raise RunnerError("--tools 必须包含 Skill，否则无法加载被测 skill")

    if allowed_raw is None:
        unexpected = sorted(set(tools) - SAFE_DEFAULT_TOOLS)
        if unexpected:
            raise RunnerError(
                "启用默认集合之外的工具时必须显式填写 --allowed-tools："
                + "、".join(unexpected)
            )
        allowed = [f"Skill({skill_name})"]
        if "Read" in tools:
            allowed.append("Read(/**)")
        if "Write" in tools:
            allowed.append("Write(/**)")
        if "Edit" in tools:
            allowed.append("Edit(/**)")
    else:
        allowed = _split_csv(allowed_raw, "--allowed-tools")
    roots: list[str] = []
    for rule in allowed:
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*)(?:\(.*\))?", rule)
        if not match:
            raise RunnerError(f"无效权限规则：{rule}")
        roots.append(match.group(1))

    outside = sorted(set(roots) - set(tools))
    if outside:
        raise RunnerError("预授权规则引用了未启用工具：" + "、".join(outside))
    if f"Skill({skill_name})" not in allowed:
        raise RunnerError(f"必须精确预授权 Skill({skill_name})")
    if any(rule == "Skill" or rule == "Skill(*)" for rule in allowed):
        raise RunnerError("禁止预授权任意 Skill；必须只授权被测 skill")
    if any(rule in {"Read", "Write", "Edit"} for rule in allowed):
        raise RunnerError("文件工具必须限定为沙箱项目路径，例如 Read(/**) / Edit(/**)")
    if any(
        rule in {"Bash", "Bash(*)", "Bash(git:*)", "Bash(git *)"}
        for rule in allowed
    ):
        raise RunnerError("禁止无边界预授权 Bash / git；请填写只读的精确命令规则")
    return tools, allowed


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _load_run(run_dir_raw: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(run_dir_raw).expanduser().resolve()
    config = _read_json(run_dir / "run-config.json")
    state = _read_json(run_dir / "run-state.json")
    if config.get("schema_version") != SCHEMA_VERSION or state.get("schema_version") != SCHEMA_VERSION:
        raise RunnerError("运行目录版本不受当前 runner 支持")
    configured_run_dir = config.get("run_dir")
    if not isinstance(configured_run_dir, str) or Path(configured_run_dir).resolve() != run_dir:
        raise RunnerError("run-config.json 与 --run-dir 不匹配")
    sandbox_raw = config.get("sandbox")
    report_dir_raw = config.get("report_dir")
    if not isinstance(sandbox_raw, str) or not isinstance(report_dir_raw, str):
        raise RunnerError("run-config.json 缺少有效的 sandbox / report_dir")
    sandbox = Path(sandbox_raw).resolve()
    report_dir = Path(report_dir_raw).resolve()
    if sandbox == run_dir or sandbox.parent != run_dir.parent or not sandbox.is_dir():
        raise RunnerError("run-config.json 中的沙箱路径无效")
    if _is_within(report_dir, sandbox) or _is_within(report_dir, run_dir):
        raise RunnerError("run-config.json 中的报告目录破坏了零侵入边界")
    for key in ("session_id_file", "transcript_file", "stderr_file"):
        value = state.get(key)
        if not isinstance(value, str) or not _is_within(Path(value).resolve(), run_dir):
            raise RunnerError(f"run-state.json 中 {key} 必须位于编排目录内")
    return run_dir, config, state


def _command_doctor(args: argparse.Namespace) -> int:
    print(json.dumps(_probe_cli(args.claude), ensure_ascii=False, indent=2))
    return 0


def _command_init(args: argparse.Namespace) -> int:
    tools, allowed = _validate_permissions(args.skill_name, args.tools, args.allowed_tools)
    probe = _probe_cli(args.claude)

    sandbox = Path(args.sandbox).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    report_dir = Path(args.report_dir).expanduser().resolve()
    if sandbox == run_dir or sandbox.parent != run_dir.parent:
        raise RunnerError("沙箱与编排目录必须是同一父目录下的两个不同目录")
    if _is_within(report_dir, sandbox) or _is_within(report_dir, run_dir):
        raise RunnerError("持久报告目录不得位于沙箱或编排目录内")
    if sandbox.exists() or run_dir.exists():
        raise RunnerError("沙箱或编排目录已存在；为避免串跑，请换用新的目录名")
    if args.timeout < 1 or args.max_turns < 1:
        raise RunnerError("超时秒数和最大轮数都必须大于 0")

    sandbox.parent.mkdir(parents=True, exist_ok=True)
    sandbox.mkdir()
    run_dir.mkdir()
    created_at = _utc_now()
    config: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex[:12],
        "created_at": created_at,
        "platform": "claude-code",
        "sandbox": str(sandbox),
        "run_dir": str(run_dir),
        "report_dir": str(report_dir),
        "skill_name": args.skill_name,
        "claude": probe,
        "timeout_seconds": args.timeout,
        "max_turns": args.max_turns,
        "tools": tools,
        "allowed_tools": allowed,
        "bash_sandbox_required": "Bash" in tools,
        "setting_sources": ["project"],
        "mcp_servers": {},
    }
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "turns": [],
        "session_id_file": str(run_dir / "session-id"),
        "transcript_file": str(run_dir / "transcript-run.jsonl"),
        "stderr_file": str(run_dir / "stderr.log"),
    }
    _write_json(run_dir / "run-config.json", config)
    _write_json(run_dir / "run-state.json", state)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


def _read_prompt(path_raw: str, run_dir: Path) -> tuple[str, str]:
    path = Path(path_raw).expanduser().resolve()
    if not _is_within(path, run_dir):
        raise RunnerError("prompt 文件必须位于编排目录内")
    try:
        prompt = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RunnerError(f"prompt 文件不存在：{path}") from exc
    if not prompt.strip():
        raise RunnerError("prompt 不得为空")
    if "\0" in prompt:
        raise RunnerError("prompt 不得包含 NUL 字符")
    return prompt, hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _session_ids(path: Path, start: int) -> list[str]:
    values: list[str] = []
    if not path.exists():
        return values
    with path.open("rb") as stream:
        stream.seek(start)
        for raw in stream:
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(event, dict) and isinstance(event.get("session_id"), str):
                values.append(event["session_id"])
    return values


def _append_runner_error(stderr_path: Path, message: str) -> None:
    with stderr_path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n[test-skill-runner] {message}\n")


def _invoke(args: argparse.Namespace, mode: str) -> int:
    run_dir, config, state = _load_run(args.run_dir)
    turns = state.get("turns")
    if not isinstance(turns, list):
        raise RunnerError("run-state.json 中 turns 必须是数组")
    if mode == "start" and turns:
        raise RunnerError("首轮已经执行；不得重复 start 或向旧记录追加新会话")
    if mode == "resume":
        if not turns:
            raise RunnerError("尚未执行首轮，不能 resume")
        if not turns[-1].get("success"):
            raise RunnerError("上一轮失败；为避免不确定状态，不得继续该会话")
        if len(turns) >= int(config["max_turns"]):
            raise RunnerError("已达到配置的最大轮数")

    prompt, prompt_hash = _read_prompt(args.prompt_file, run_dir)
    transcript_path = Path(state["transcript_file"])
    stderr_path = Path(state["stderr_file"])
    transcript_start = transcript_path.stat().st_size if transcript_path.exists() else 0
    stderr_start = stderr_path.stat().st_size if stderr_path.exists() else 0

    command = [config["claude"]["executable"], "-p"]
    expected_session: str | None = None
    if mode == "resume":
        session_path = Path(state["session_id_file"])
        try:
            expected_session = session_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise RunnerError("缺少 session-id 文件，不能 resume") from exc
        if not expected_session:
            raise RunnerError("session-id 文件为空，不能 resume")
        command.extend(["--resume", expected_session])
    command.extend(
        [
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "dontAsk",
            "--tools",
            ",".join(config["tools"]),
            config["claude"]["allowed_tools_flag"],
        ]
    )
    command.extend(config["allowed_tools"])
    command.extend(
        [
            "--setting-sources",
            "project",
            "--strict-mcp-config",
            "--mcp-config",
            json.dumps({"mcpServers": {}}, separators=(",", ":")),
        ]
    )
    if "Bash" in config["tools"]:
        bash_sandbox = {
            "sandbox": {
                "enabled": True,
                "failIfUnavailable": True,
                "autoAllowBashIfSandboxed": False,
                "allowUnsandboxedCommands": False,
                "filesystem": {
                    "denyRead": ["~/", config["run_dir"], config["report_dir"]],
                    "allowRead": [config["sandbox"]],
                    "denyWrite": [config["run_dir"], config["report_dir"]],
                },
            }
        }
        command.extend(
            ["--settings", json.dumps(bash_sandbox, separators=(",", ":"))]
        )
    # `--` 终止参数解析，prompt 始终作为一个独立位置参数传递；其中的引号、换行、
    # `$()` 或以 `--` 开头的文本都不会被 shell 执行，也不会被误认成 CLI 选项。
    command.extend(["--", prompt])

    started_at = _utc_now()
    started = time.monotonic()
    timed_out = False
    process_exit = 127
    with transcript_path.open("ab") as stdout_stream, stderr_path.open("ab") as stderr_stream:
        try:
            result = subprocess.run(
                command,
                cwd=config["sandbox"],
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                check=False,
                timeout=int(config["timeout_seconds"]),
            )
            process_exit = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            process_exit = 124
        except OSError as exc:
            _append_runner_error(stderr_path, f"启动 Claude CLI 失败：{exc}")

    duration = round(time.monotonic() - started, 3)
    transcript_end = transcript_path.stat().st_size
    stderr_end = stderr_path.stat().st_size
    observed_sessions = _session_ids(transcript_path, transcript_start)
    unique_sessions = set(observed_sessions)
    observed_session = observed_sessions[0] if observed_sessions else None
    runner_exit = process_exit if 0 < process_exit < 126 else (124 if timed_out else 1)
    error: str | None = None
    success = process_exit == 0 and not timed_out
    if success and len(unique_sessions) > 1:
        success = False
        runner_exit = 67
        error = "本轮输出包含多个不同的 session_id"
    if mode == "start" and success and not observed_session:
        success = False
        runner_exit = 65
        error = "首轮输出中没有 session_id"
    if mode == "resume" and success:
        if not observed_session:
            success = False
            runner_exit = 65
            error = "续轮输出中没有 session_id"
        elif observed_session != expected_session:
            success = False
            runner_exit = 66
            error = "续轮返回了不同的 session_id"
    if timed_out:
        error = f"超过 {config['timeout_seconds']} 秒，进程已终止"
    elif process_exit != 0:
        error = f"Claude CLI 退出码为 {process_exit}"

    record = {
        "turn": len(turns) + 1,
        "mode": mode,
        "started_at": started_at,
        "duration_seconds": duration,
        "prompt_file": str(Path(args.prompt_file).expanduser().resolve()),
        "prompt_sha256": prompt_hash,
        "process_exit_code": process_exit,
        "runner_exit_code": 0 if success else runner_exit,
        "timed_out": timed_out,
        "success": success,
        "error": error,
        "transcript_bytes": [transcript_start, transcript_end],
        "stderr_bytes": [stderr_start, stderr_end],
    }
    turns.append(record)
    state["updated_at"] = _utc_now()
    _write_json(run_dir / "run-state.json", state)

    if mode == "start" and success and observed_session:
        Path(state["session_id_file"]).write_text(observed_session + "\n", encoding="utf-8")
    if error:
        _append_runner_error(stderr_path, error)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if success else runner_exit


def _command_status(args: argparse.Namespace) -> int:
    _, config, state = _load_run(args.run_dir)
    print(json.dumps({"config": config, "state": state}, ensure_ascii=False, indent=2))
    return 0


def _command_report_path(args: argparse.Namespace) -> int:
    run_dir, config, state = _load_run(args.run_dir)
    existing = state.get("report_path")
    if existing:
        if not isinstance(existing, str):
            raise RunnerError("run-state.json 中 report_path 必须是字符串")
        existing_path = Path(existing).resolve()
        report_dir = Path(config["report_dir"]).resolve()
        if existing_path.parent != report_dir or not existing_path.is_file():
            raise RunnerError("run-state.json 中 report_path 无效或文件已丢失")
        print(existing_path)
        return 0
    report_dir = Path(config["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.fromisoformat(config["created_at"]).strftime("%Y-%m-%d-%H%M%S")
    path = report_dir / f"test-report-{created}-{config['run_id']}.md"
    try:
        path.touch(exist_ok=False)
    except FileExistsError as exc:
        raise RunnerError(f"报告路径冲突：{path}") from exc
    state["report_path"] = str(path)
    state["updated_at"] = _utc_now()
    _write_json(run_dir / "run-state.json", state)
    print(path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="只做 CLI 能力预检")
    doctor.add_argument("--claude", default="claude", help="Claude CLI 命令或绝对路径")
    doctor.set_defaults(handler=_command_doctor)

    init = subparsers.add_parser("init", help="创建隔离沙箱和持久运行配置")
    init.add_argument("--sandbox", required=True)
    init.add_argument("--run-dir", required=True)
    init.add_argument("--report-dir", required=True)
    init.add_argument("--skill-name", required=True)
    init.add_argument("--claude", default="claude")
    init.add_argument("--timeout", type=int, default=600)
    init.add_argument("--max-turns", type=int, default=10)
    init.add_argument("--tools", default=DEFAULT_TOOLS)
    init.add_argument("--allowed-tools")
    init.set_defaults(handler=_command_init)

    for name, handler in (("start", lambda value: _invoke(value, "start")), ("resume", lambda value: _invoke(value, "resume"))):
        command = subparsers.add_parser(name, help=f"执行{name}轮")
        command.add_argument("--run-dir", required=True)
        command.add_argument("--prompt-file", required=True)
        command.set_defaults(handler=handler)

    status = subparsers.add_parser("status", help="输出配置与逐轮状态")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(handler=_command_status)

    report_path = subparsers.add_parser("report-path", help="原子预留并输出唯一报告路径")
    report_path.add_argument("--run-dir", required=True)
    report_path.set_defaults(handler=_command_report_path)
    return parser


def main() -> int:
    try:
        args = _parser().parse_args()
        return int(args.handler(args))
    except RunnerError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
