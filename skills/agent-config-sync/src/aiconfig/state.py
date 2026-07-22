"""状态文件与内容哈希。"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ConfigError


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def hash_text(value: str) -> str:
    return hash_bytes(value.encode("utf-8"))


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())


def data_dir(home: str | Path) -> Path:
    return Path(home) / ".config" / "aiconfig"


def state_path(home: str | Path) -> Path:
    return data_dir(home) / "state.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "targets": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError("CONFIG_SCHEMA_INVALID", f"状态文件无效：{exc}", location=str(path)) from exc
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("targets"), dict):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "状态文件结构无效。", location=str(path))
    return value


def save_state(path: Path, value: dict[str, Any]) -> None:
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    temp_name: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        json.loads(Path(temp_name).read_text(encoding="utf-8"))
        os.replace(temp_name, path)
    except OSError as exc:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise ConfigError("TARGET_WRITE_FAILED", f"无法写入状态文件：{exc}", location=str(path)) from exc


def classify_status(
    target_path: Path,
    desired_content: str,
    state_record: dict[str, Any] | None,
    *,
    source_is_current: bool,
    parse_current,
) -> str:
    if not target_path.exists():
        return "missing"
    try:
        parse_current(target_path.read_text(encoding="utf-8"))
    except Exception:
        return "invalid"
    current_hash = hash_file(target_path)
    if not state_record:
        return "outdated"
    if current_hash != state_record.get("generatedHash"):
        return "modified"
    if current_hash != hash_text(desired_content) or not source_is_current:
        return "outdated"
    return "synced"
