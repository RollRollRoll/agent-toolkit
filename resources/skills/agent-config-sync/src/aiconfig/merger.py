"""确定性深度合并与数组操作。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import ConfigError


DELETE = object()


def _operation(value: Any) -> tuple[str, Any] | None:
    if not isinstance(value, dict):
        return None
    keys = set(value)
    operators = keys & {"$append", "$prepend", "$delete"}
    if not operators:
        return None
    if len(keys) != 1 or len(operators) != 1:
        raise ConfigError("INVALID_ARRAY_OPERATION", "合并操作对象只能包含一个操作符。")
    key = next(iter(operators))
    return key, value[key]


def deep_merge(base: Any, overlay: Any, *, location: str = "") -> Any:
    operation = _operation(overlay)
    if operation:
        name, operand = operation
        if name == "$delete":
            if operand is not True:
                raise ConfigError("CONFIG_SCHEMA_INVALID", "$delete 的值必须为 true。", location=location)
            return DELETE
        if not isinstance(operand, list):
            raise ConfigError("INVALID_ARRAY_OPERATION", f"{name} 的值必须是数组。", location=location)
        if base is None:
            base = []
        if not isinstance(base, list):
            raise ConfigError("INVALID_ARRAY_OPERATION", f"{name} 只能用于数组字段。", location=location)
        return deepcopy(base + operand if name == "$append" else operand + base)

    if base is None and isinstance(overlay, dict):
        base = {}

    if isinstance(base, dict) and isinstance(overlay, dict):
        result = deepcopy(base)
        for key, value in overlay.items():
            child_location = f"{location}.{key}" if location else str(key)
            if key in result:
                merged = deep_merge(result[key], value, location=child_location)
            else:
                merged = deep_merge(None, value, location=child_location)
            if merged is DELETE:
                result.pop(key, None)
            else:
                result[key] = merged
        return result

    if base is not None:
        base_compound = isinstance(base, (dict, list))
        overlay_compound = isinstance(overlay, (dict, list))
        if (base_compound or overlay_compound) and type(base) is not type(overlay):
            raise ConfigError(
                "MERGE_TYPE_CONFLICT",
                f"不能把 {type(base).__name__} 隐式替换为 {type(overlay).__name__}。",
                location=location,
            )
    return deepcopy(overlay)


def merge_target(base: dict[str, Any], overlays: list[dict[str, Any]]) -> dict[str, Any]:
    # 先通过同一合并器规范化 base，确保其中不会残留合并操作符。
    result: Any = deep_merge({}, base, location="base")
    for overlay in overlays:
        result = deep_merge(result, overlay.get("set", {}), location=f"overlay:{overlay.get('name', '<unnamed>')}")
    if not isinstance(result, dict):
        raise ConfigError("MERGE_TYPE_CONFLICT", "目标配置合并后必须是对象。")
    return result
