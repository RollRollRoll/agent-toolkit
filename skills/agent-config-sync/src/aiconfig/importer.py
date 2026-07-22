"""从多份现有配置生成可审阅的导入计划和声明。"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import tomlkit
import yaml

from .errors import ConfigError
from .state import hash_file
from .validator import load_rejected_claude_fields, scan_secrets


PLAN_VERSION = 1
TARGET_OUTPUTS = {
    "codex": "~/.codex/config.toml",
    "claude": "~/.claude/settings.json",
}


def parse_source_spec(value: str) -> tuple[str, Path]:
    target, separator, raw_path = value.partition("=")
    if not separator or target not in TARGET_OUTPUTS or not raw_path:
        raise ConfigError(
            "IMPORT_SOURCE_INVALID",
            "来源必须写成 codex=<path> 或 claude=<path>。",
            location=value,
        )
    return target, Path(raw_path).expanduser().resolve()


def parse_exclude_spec(value: str) -> tuple[str, str]:
    target, separator, pointer = value.partition("=")
    if not separator or target not in TARGET_OUTPUTS or (pointer and not pointer.startswith("/")):
        raise ConfigError(
            "IMPORT_DECISION_INVALID",
            "剔除项必须写成 codex=/json/pointer 或 claude=/json/pointer。",
            location=value,
        )
    _pointer_parts(pointer)
    return target, pointer


def _read_source(target: str, path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError("IMPORT_SOURCE_NOT_FOUND", "导入来源不存在。", location=str(path)) from exc
    except OSError as exc:
        raise ConfigError("IMPORT_SOURCE_NOT_FOUND", f"无法读取导入来源：{exc}", location=str(path)) from exc

    try:
        if target == "codex":
            data = tomlkit.parse(content).unwrap()
        else:
            data = json.loads(content)
    except Exception as exc:
        raise ConfigError("IMPORT_SOURCE_INVALID", f"无法解析 {target} 配置：{exc}", location=str(path)) from exc
    if not isinstance(data, dict):
        raise ConfigError("IMPORT_SOURCE_INVALID", "配置文件顶层必须是对象。", location=str(path))
    return data


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_child(parent: str, key: str) -> str:
    return f"{parent}/{_escape_pointer(key)}"


def _pointer_parts(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ConfigError("IMPORT_DECISION_INVALID", "配置项路径必须是 JSON Pointer。", location=str(pointer))
    parts: list[str] = []
    for raw in pointer[1:].split("/"):
        index = 0
        decoded = ""
        while index < len(raw):
            if raw[index] != "~":
                decoded += raw[index]
                index += 1
                continue
            if index + 1 >= len(raw) or raw[index + 1] not in {"0", "1"}:
                raise ConfigError("IMPORT_DECISION_INVALID", "JSON Pointer 包含无效转义。", location=pointer)
            decoded += "~" if raw[index + 1] == "0" else "/"
            index += 2
        parts.append(decoded)
    return parts


def _value_key(value: Any) -> str:
    try:
        return yaml.safe_dump(value, allow_unicode=True, sort_keys=True)
    except yaml.YAMLError as exc:
        raise ConfigError("IMPORT_SOURCE_INVALID", f"配置值无法规范化：{exc}") from exc


def _group_values(values: list[tuple[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    indexes: dict[str, int] = {}
    for source_id, value in values:
        key = _value_key(value)
        if key in indexes:
            groups[indexes[key]]["sources"].append(source_id)
            continue
        indexes[key] = len(groups)
        groups.append({"sources": [source_id], "value": deepcopy(value)})
    return groups


def _is_out_of_scope(target: str, pointer: str, rejected_claude_fields: set[str]) -> bool:
    parts = _pointer_parts(pointer)
    return target == "claude" and bool(parts) and parts[0] in rejected_claude_fields


def _append_item(
    items: list[dict[str, Any]],
    target: str,
    pointer: str,
    values: list[tuple[str, Any]],
    rejected_claude_fields: set[str],
) -> None:
    source_ids = [source_id for source_id, _ in values]
    if _is_out_of_scope(target, pointer, rejected_claude_fields):
        items.append(
            {"path": pointer, "status": "out-of-scope", "sources": source_ids, "action": "exclude"}
        )
        return
    if any(scan_secrets(value, location=pointer) for _, value in values):
        items.append({"path": pointer, "status": "sensitive", "sources": source_ids, "action": "exclude"})
        return

    groups = _group_values(values)
    if len(groups) == 1:
        group = groups[0]
        items.append(
            {
                "path": pointer,
                "status": "duplicate" if len(group["sources"]) > 1 else "unique",
                "sources": group["sources"],
                "value": group["value"],
                "action": "keep",
            }
        )
        return
    items.append({"path": pointer, "status": "conflict", "candidates": groups, "action": "unresolved"})


def _reconcile_node(
    values: list[tuple[str, Any]],
    *,
    target: str,
    pointer: str,
    items: list[dict[str, Any]],
    rejected_claude_fields: set[str],
) -> None:
    if values and all(isinstance(value, dict) for _, value in values):
        keys: list[str] = []
        seen: set[str] = set()
        for _, value in values:
            for key in value:
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        if not keys and pointer:
            _append_item(items, target, pointer, values, rejected_claude_fields)
            return
        for key in keys:
            children = [(source_id, value[key]) for source_id, value in values if key in value]
            _reconcile_node(
                children,
                target=target,
                pointer=_pointer_child(pointer, key),
                items=items,
                rejected_claude_fields=rejected_claude_fields,
            )
        return
    _append_item(items, target, pointer, values, rejected_claude_fields)


def build_import_plan(source_specs: Iterable[tuple[str, Path]]) -> dict[str, Any]:
    grouped: dict[str, list[tuple[str, Path, dict[str, Any]]]] = {"codex": [], "claude": []}
    counters = {"codex": 0, "claude": 0}
    for target, raw_path in source_specs:
        if target not in TARGET_OUTPUTS:
            raise ConfigError("IMPORT_SOURCE_INVALID", f"不支持的导入目标：{target}")
        path = Path(raw_path).expanduser().resolve()
        counters[target] += 1
        source_id = f"{target}-{counters[target]}"
        grouped[target].append((source_id, path, _read_source(target, path)))
    if not any(grouped.values()):
        raise ConfigError("IMPORT_SOURCE_INVALID", "至少需要一个导入来源。")

    rejected = load_rejected_claude_fields()
    targets: dict[str, Any] = {}
    for target in ("codex", "claude"):
        sources = grouped[target]
        if not sources:
            continue
        items: list[dict[str, Any]] = []
        _reconcile_node(
            [(source_id, data) for source_id, _, data in sources],
            target=target,
            pointer="",
            items=items,
            rejected_claude_fields=rejected,
        )
        targets[target] = {
            "output": TARGET_OUTPUTS[target],
            "sources": [
                {"id": source_id, "path": str(path), "hash": hash_file(path)}
                for source_id, path, _ in sources
            ],
            "excludes": [],
            "items": items,
        }
    return {"version": PLAN_VERSION, "targets": targets}


def dump_import_plan(plan: dict[str, Any]) -> str:
    return yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, default_flow_style=False)


def load_import_plan(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError("IMPORT_PLAN_NOT_FOUND", "导入计划不存在。", location=str(path)) from exc
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError("IMPORT_PLAN_INVALID", f"无法读取导入计划：{exc}", location=str(path)) from exc
    if (
        not isinstance(value, dict)
        or value.get("version") != PLAN_VERSION
        or not isinstance(value.get("targets"), dict)
    ):
        raise ConfigError("IMPORT_PLAN_INVALID", "导入计划结构或版本无效。", location=str(path))
    return value


def _is_excluded(pointer: str, excludes: Iterable[str]) -> bool:
    for excluded in excludes:
        _pointer_parts(excluded)
        if excluded == "" or pointer == excluded or pointer.startswith(excluded + "/"):
            return True
    return False


def _select_candidate(item: dict[str, Any]) -> Any:
    source = item.get("source")
    if not isinstance(source, str):
        raise ConfigError("IMPORT_DECISION_INVALID", "take 决策必须指定 source。", location=item.get("path"))
    candidates = item.get("candidates")
    if not isinstance(candidates, list):
        raise ConfigError("IMPORT_PLAN_INVALID", "冲突候选必须是数组。", location=item.get("path"))
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("sources"), list):
            raise ConfigError("IMPORT_PLAN_INVALID", "冲突候选结构无效。", location=item.get("path"))
        if source in candidate["sources"]:
            if "value" not in candidate:
                raise ConfigError("IMPORT_PLAN_INVALID", "冲突候选缺少 value。", location=item.get("path"))
            return deepcopy(candidate["value"])
    raise ConfigError("IMPORT_DECISION_INVALID", f"来源 {source} 不属于该配置项。", location=item.get("path"))


def _union_candidates(item: dict[str, Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    candidates = item.get("candidates")
    if not isinstance(candidates, list) or not candidates or any(
        not isinstance(candidate, dict) or not isinstance(candidate.get("value"), list)
        for candidate in candidates
    ):
        raise ConfigError(
            "IMPORT_DECISION_INVALID",
            "union 只能用于存在冲突的数组。",
            location=item.get("path"),
        )
    for candidate in candidates:
        for value in candidate["value"]:
            key = _value_key(value)
            if key not in seen:
                seen.add(key)
                result.append(deepcopy(value))
    return result


def _resolved_value(item: dict[str, Any]) -> Any:
    action = item.get("action")
    if action == "keep":
        if item.get("status") not in {"unique", "duplicate"} or "value" not in item:
            raise ConfigError(
                "IMPORT_DECISION_INVALID",
                "keep 只能用于无冲突配置项。",
                location=item.get("path"),
            )
        return deepcopy(item["value"])
    if action == "take":
        return _select_candidate(item)
    if action == "union":
        return _union_candidates(item)
    if action == "set":
        if "selectedValue" not in item:
            raise ConfigError(
                "IMPORT_DECISION_INVALID",
                "set 决策必须提供 selectedValue。",
                location=item.get("path"),
            )
        return deepcopy(item["selectedValue"])
    raise ConfigError("IMPORT_DECISION_INVALID", f"不支持的导入决策：{action!r}", location=item.get("path"))


def validate_import_item_decision(item: dict[str, Any]) -> None:
    """校验单个导入项决策，供命令行与本地 UI 共用。"""

    action = item.get("action")
    status = item.get("status")
    if status in {"sensitive", "out-of-scope"}:
        if action != "exclude":
            raise ConfigError("IMPORT_DECISION_INVALID", "敏感或越界字段只能剔除。", location=item.get("path"))
        return
    if action == "exclude":
        return
    if action == "unresolved" and status == "conflict":
        return
    _resolved_value(item)


def _set_pointer(root: dict[str, Any], pointer: str, value: Any) -> None:
    parts = _pointer_parts(pointer)
    if not parts:
        if value != {}:
            raise ConfigError("IMPORT_PLAN_INVALID", "目标配置顶层必须是对象。", location=pointer)
        return
    current = root
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise ConfigError("IMPORT_PLAN_INVALID", "导入计划包含重叠的配置项路径。", location=pointer)
        current = child
    if parts[-1] in current:
        raise ConfigError("IMPORT_PLAN_INVALID", "导入计划包含重复的配置项路径。", location=pointer)
    current[parts[-1]] = value


def declaration_from_import_plan(
    plan: dict[str, Any],
    *,
    additional_excludes: Iterable[tuple[str, str]] = (),
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or plan.get("version") != PLAN_VERSION
        or not isinstance(plan.get("targets"), dict)
    ):
        raise ConfigError("IMPORT_PLAN_INVALID", "导入计划结构或版本无效。")

    excludes_by_target: dict[str, list[str]] = {"codex": [], "claude": []}
    for target, pointer in additional_excludes:
        if target not in excludes_by_target:
            raise ConfigError("IMPORT_DECISION_INVALID", f"不支持的目标：{target}")
        _pointer_parts(pointer)
        excludes_by_target[target].append(pointer)

    declaration: dict[str, Any] = {"apiVersion": "agent-config/v1", "targets": {}}
    unresolved: list[str] = []
    for target in ("codex", "claude"):
        target_plan = plan["targets"].get(target)
        if target_plan is None:
            continue
        if not isinstance(target_plan, dict) or not isinstance(target_plan.get("items"), list):
            raise ConfigError("IMPORT_PLAN_INVALID", "目标导入计划结构无效。", location=f"targets.{target}")
        configured_excludes = target_plan.get("excludes", [])
        if not isinstance(configured_excludes, list) or not all(isinstance(item, str) for item in configured_excludes):
            raise ConfigError(
                "IMPORT_PLAN_INVALID",
                "excludes 必须是 JSON Pointer 数组。",
                location=f"targets.{target}.excludes",
            )
        excludes = [*configured_excludes, *excludes_by_target[target]]
        base: dict[str, Any] = {}
        for item in target_plan["items"]:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise ConfigError(
                    "IMPORT_PLAN_INVALID",
                    "导入配置项结构无效。",
                    location=f"targets.{target}.items",
                )
            pointer = item["path"]
            _pointer_parts(pointer)
            if _is_excluded(pointer, excludes) or item.get("action") == "exclude":
                continue
            if item.get("status") in {"sensitive", "out-of-scope"}:
                raise ConfigError("IMPORT_DECISION_INVALID", "敏感或越界字段只能剔除。", location=pointer)
            if item.get("action") == "unresolved":
                unresolved.append(f"{target}:{pointer}")
                continue
            _set_pointer(base, pointer, _resolved_value(item))
        declaration["targets"][target] = {
            "output": target_plan.get("output", TARGET_OUTPUTS[target]),
            "base": base,
            "overlays": [],
        }
    if unresolved:
        raise ConfigError(
            "IMPORT_CONFLICT_UNRESOLVED",
            "仍有未解决的导入冲突：" + ", ".join(unresolved),
        )
    if not declaration["targets"]:
        raise ConfigError("IMPORT_PLAN_INVALID", "导入计划没有目标。")
    return declaration


def dump_declaration(declaration: dict[str, Any]) -> str:
    return yaml.safe_dump(declaration, sort_keys=False, allow_unicode=True, default_flow_style=False)
