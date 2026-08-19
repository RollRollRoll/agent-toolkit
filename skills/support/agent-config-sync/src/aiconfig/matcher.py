"""Overlay 条件匹配。"""

from __future__ import annotations

from typing import Any, Iterable

from .errors import ConfigError


SUPPORTED_KEYS = {"os", "runtime", "hostname", "profile", "tags"}


def _matches_value(actual: Any, expected: Any, *, ignore_case: bool = False) -> bool:
    choices = expected if isinstance(expected, list) else [expected]
    if ignore_case:
        actual = str(actual).casefold()
        choices = [str(choice).casefold() for choice in choices]
    return actual in choices


def matches(when: dict[str, Any], context: dict[str, Any]) -> bool:
    unknown = set(when) - SUPPORTED_KEYS
    if unknown:
        raise ConfigError("INVALID_CONDITION", f"不支持的条件：{', '.join(sorted(unknown))}")

    for key, expected in when.items():
        if key == "tags":
            if not isinstance(expected, dict) or set(expected) != {"contains"}:
                raise ConfigError("INVALID_CONDITION", "tags 条件必须使用 contains。")
            required = expected["contains"]
            actual_tags = set(context.get("tags") or [])
            if not all(tag in actual_tags for tag in required):
                return False
            continue
        if not _matches_value(context.get(key), expected, ignore_case=key == "hostname"):
            return False
    return True


def matched_overlays(overlays: Iterable[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    return [overlay for overlay in overlays if matches(overlay.get("when", {}), context)]

