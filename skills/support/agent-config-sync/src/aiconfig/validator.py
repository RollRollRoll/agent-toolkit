"""声明、生成结果、字段范围与秘密提示校验。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

import jsonschema

from .errors import ConfigError
from .renderer import prepare_target, render_target


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = SKILL_ROOT / "schemas" / "agent-config.schema.json"
CLAUDE_REFERENCE_PATH = SKILL_ROOT / "references" / "claude-settings.md"
SECRET_PATTERNS = ("sk-ant-", "sk-proj-", "github_pat_", "ghp_", "Bearer")


def _format_json_path(parts: Iterable[Any]) -> str:
    result = ""
    for part in parts:
        result += f"[{part}]" if isinstance(part, int) else (f".{part}" if result else str(part))
    return result or "<root>"


def validate_schema(declaration: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(declaration), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        raise ConfigError("CONFIG_SCHEMA_INVALID", error.message, location=_format_json_path(error.absolute_path))


def validate_condition_values(declaration: dict[str, Any]) -> None:
    allowed = {
        "os": {"windows", "linux", "macos"},
        "runtime": {"native", "wsl", "container"},
    }
    for target_name, target in declaration["targets"].items():
        for index, overlay in enumerate(target.get("overlays", [])):
            for key, choices in allowed.items():
                if key not in overlay["when"]:
                    continue
                raw = overlay["when"][key]
                values = raw if isinstance(raw, list) else [raw]
                invalid = [value for value in values if value not in choices]
                if invalid:
                    raise ConfigError(
                        "INVALID_CONDITION",
                        f"{key} 包含不支持的值：{', '.join(invalid)}",
                        location=f"targets.{target_name}.overlays[{index}].when.{key}",
                    )


def load_rejected_claude_fields(path: Path = CLAUDE_REFERENCE_PATH) -> set[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<!-- rejected-fields:start -->(.*?)<!-- rejected-fields:end -->", text, re.DOTALL)
    if not match:
        raise ConfigError("CONFIG_SCHEMA_INVALID", "Claude 拒绝字段清单缺失。", location=str(path))
    return set(re.findall(r"^- `([^`]+)`$", match.group(1), re.MULTILINE))


def validate_claude_scope(data: dict[str, Any]) -> None:
    rejected = sorted(set(data) & load_rejected_claude_fields())
    if rejected:
        field = rejected[0]
        raise ConfigError(
            "CLAUDE_FIELD_OUT_OF_SCOPE",
            f"字段 {field} 不属于 ~/.claude/settings.json；本 Skill 不管理 ~/.claude.json。",
            location=f"targets.claude.{field}",
        )


def scan_secrets(value: Any, *, location: str = "") -> list[str]:
    warnings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else str(key)
            warnings.extend(scan_secrets(child, location=child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            warnings.extend(scan_secrets(child, location=f"{location}[{index}]"))
    elif isinstance(value, str) and any(pattern in value for pattern in SECRET_PATTERNS):
        warnings.append(f"WARNING [POSSIBLE_SECRET_FOUND] possible secret found at {location}")
    return warnings


def validate_declaration(
    declaration: dict[str, Any],
    context: dict[str, Any],
    targets: Iterable[str],
    environ: Mapping[str, str] | None = None,
) -> tuple[dict[str, tuple[dict[str, Any], list[dict[str, Any]], str]], list[str]]:
    validate_schema(declaration)
    validate_condition_values(declaration)
    prepared: dict[str, tuple[dict[str, Any], list[dict[str, Any]], str]] = {}
    for target_name in targets:
        data, overlays = prepare_target(declaration, target_name, context, environ)
        if target_name == "claude":
            validate_claude_scope(data)
        content = render_target(target_name, data)
        prepared[target_name] = (data, overlays, content)
    return prepared, scan_secrets(declaration)
