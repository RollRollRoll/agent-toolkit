"""从官方 JSON Schema 查询配置项说明，并在本地缓存结果。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from .errors import ConfigError
from .writer import atomic_write


SCHEMA_SOURCES = {
    "codex": "https://developers.openai.com/codex/config-schema.json",
    "claude": "https://json.schemastore.org/claude-code-settings.json",
}
SCHEMA_KINDS = {"codex": "official-schema", "claude": "published-schema"}
CACHE_VERSION = 1


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "agent-config-sync/0.1"})
    with urlopen(request, timeout=10) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Schema 顶层不是对象")
    return value


def _pointer_parts(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ConfigError("DOC_PATH_INVALID", "配置项路径必须是 JSON Pointer。", location=str(pointer))
    result: list[str] = []
    for raw in pointer[1:].split("/"):
        result.append(raw.replace("~1", "/").replace("~0", "~"))
    return result


def _resolve_pointer(root: dict[str, Any], pointer: str) -> Any:
    current: Any = root
    for part in _pointer_parts(pointer):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _schema_view(root: dict[str, Any], value: Any, seen: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    reference = value.get("$ref")
    visited = set() if seen is None else set(seen)
    if isinstance(reference, str) and reference.startswith("#/") and reference not in visited:
        visited.add(reference)
        resolved = _resolve_pointer(root, reference[1:])
        result.update(_schema_view(root, resolved, visited))
    for key in ("allOf", "oneOf", "anyOf"):
        choices = value.get(key)
        if isinstance(choices, list):
            for choice in choices:
                result.update(_schema_view(root, choice, visited))
    result.update({key: child for key, child in value.items() if key not in {"$ref", "allOf", "oneOf", "anyOf"}})
    return result


def _field_schema(root: dict[str, Any], pointer: str) -> dict[str, Any] | None:
    current = _schema_view(root, root)
    for part in _pointer_parts(pointer):
        properties = current.get("properties")
        if isinstance(properties, dict) and part in properties:
            current = _schema_view(root, properties[part])
            continue
        additional = current.get("additionalProperties")
        if isinstance(additional, dict):
            current = _schema_view(root, additional)
            continue
        return None
    return current


def _type_name(root: dict[str, Any], schema: dict[str, Any]) -> str | None:
    raw_type = schema.get("type")
    if isinstance(raw_type, list):
        raw_type = " | ".join(str(item) for item in raw_type)
    if raw_type != "array":
        return str(raw_type) if raw_type is not None else None
    item_schema = _schema_view(root, schema.get("items"))
    item_type = item_schema.get("type")
    return f"array<{item_type}>" if isinstance(item_type, str) else "array"


class ConfigDocsResolver:
    """解析官方 Schema，并以目标为粒度缓存。"""

    def __init__(
        self,
        cache_path: Path,
        *,
        fetch_json: Callable[[str], dict[str, Any]] | None = None,
        ttl: timedelta = timedelta(hours=24),
        now: Callable[[], datetime] | None = None,
    ):
        self.cache_path = Path(cache_path)
        self.fetch_json = fetch_json or _fetch_json
        self.ttl = ttl
        self.now = now or (lambda: datetime.now(timezone.utc))

    def _read_cache(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {"version": CACHE_VERSION, "sources": {}}
        try:
            value = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"version": CACHE_VERSION, "sources": {}}
        if not isinstance(value, dict) or not isinstance(value.get("sources"), dict):
            return {"version": CACHE_VERSION, "sources": {}}
        return value

    def _write_cache(self, value: dict[str, Any]) -> None:
        content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        atomic_write(self.cache_path, content, json.loads)

    def _load_schema(self, target: str, *, refresh: bool) -> tuple[dict[str, Any], str, bool]:
        if target not in SCHEMA_SOURCES:
            raise ConfigError("DOC_TARGET_INVALID", f"不支持的说明目标：{target}")
        cache = self._read_cache()
        cached = cache["sources"].get(target)
        now = self.now()
        fresh = False
        if isinstance(cached, dict) and isinstance(cached.get("schema"), dict):
            try:
                fetched_at = datetime.fromisoformat(str(cached["fetchedAt"]))
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                fresh = now - fetched_at <= self.ttl
            except (KeyError, TypeError, ValueError):
                fresh = False
        if cached and fresh and not refresh:
            return cached["schema"], str(cached["fetchedAt"]), False

        url = SCHEMA_SOURCES[target]
        try:
            schema = self.fetch_json(url)
            if not isinstance(schema, dict):
                raise ValueError("Schema 顶层不是对象")
            fetched_at = now.isoformat()
            cache["sources"][target] = {"url": url, "fetchedAt": fetched_at, "schema": schema}
            self._write_cache(cache)
            return schema, fetched_at, False
        except Exception as exc:
            if isinstance(exc, ConfigError) and exc.code == "TARGET_WRITE_FAILED":
                raise
            if isinstance(cached, dict) and isinstance(cached.get("schema"), dict):
                return cached["schema"], str(cached.get("fetchedAt", "")), True
            raise ConfigError(
                "DOC_LOOKUP_FAILED",
                f"无法获取官方配置说明：{exc}",
                location=url,
            ) from exc

    def resolve(self, target: str, path: str, *, refresh: bool = False) -> dict[str, Any]:
        schema, fetched_at, stale = self._load_schema(target, refresh=refresh)
        field = _field_schema(schema, path)
        return {
            "target": target,
            "path": path,
            "found": field is not None,
            "description": field.get("description") if field else None,
            "type": _type_name(schema, field) if field else None,
            "allowedValues": list(field.get("enum", [])) if field and isinstance(field.get("enum"), list) else [],
            "default": field.get("default") if field else None,
            "sourceUrl": SCHEMA_SOURCES[target],
            "sourceKind": SCHEMA_KINDS[target],
            "fetchedAt": fetched_at,
            "stale": stale,
        }
