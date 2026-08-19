"""备份、本地修改保护与原子写入。"""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .errors import ConfigError
from .state import hash_file


def ensure_not_modified(target_name: str, path: Path, state: dict[str, Any], *, force: bool) -> None:
    record = state.get("targets", {}).get(target_name)
    if not path.exists() or not record:
        return
    if hash_file(path) != record.get("generatedHash") and not force:
        raise ConfigError(
            "TARGET_FILE_MODIFIED",
            "目标文件在上次应用后被手工修改；审阅差异后使用 --force 才能覆盖。",
            location=str(path),
        )


def backup_file(target_name: str, path: Path, backup_root: Path) -> Path | None:
    if not path.exists():
        return None
    directory = backup_root / target_name
    try:
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        candidate = directory / f"{timestamp}-{path.name}"
        suffix = 1
        while candidate.exists():
            candidate = directory / f"{timestamp}-{suffix}-{path.name}"
            suffix += 1
        shutil.copy2(path, candidate)
        return candidate
    except OSError as exc:
        raise ConfigError("BACKUP_FAILED", f"无法备份目标文件：{exc}", location=str(path)) from exc


def atomic_write(path: Path, content: str, validate: Callable[[str], Any]) -> None:
    temp_name: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        previous_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, newline="\n") as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        validate(Path(temp_name).read_text(encoding="utf-8"))
        if previous_mode is not None:
            os.chmod(temp_name, previous_mode)
        os.replace(temp_name, path)
    except ConfigError:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise
    except Exception as exc:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise ConfigError("TARGET_WRITE_FAILED", f"无法原子写入目标文件：{exc}", location=str(path)) from exc


def apply_content(
    target_name: str,
    path: Path,
    content: str,
    state: dict[str, Any],
    backup_root: Path,
    validate: Callable[[str], Any],
    *,
    force: bool,
) -> Path | None:
    ensure_not_modified(target_name, path, state, force=force)
    backup = backup_file(target_name, path, backup_root)
    atomic_write(path, content, validate)
    return backup
