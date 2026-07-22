"""运行环境与本地上下文检测。"""

from __future__ import annotations

import getpass
import os
import platform
import socket
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from .errors import ConfigError


def detect_os(system: str | None = None) -> str:
    value = (system or platform.system()).lower()
    if value == "windows":
        return "windows"
    if value == "darwin":
        return "macos"
    return "linux"


def detect_runtime(
    environ: Mapping[str, str] | None = None,
    read_text: Callable[[Path], str] | None = None,
) -> str:
    env = os.environ if environ is None else environ
    if env.get("WSL_DISTRO_NAME"):
        return "wsl"

    reader = read_text or (lambda path: path.read_text(encoding="utf-8"))
    for path in (Path("/proc/version"), Path("/proc/sys/kernel/osrelease")):
        try:
            if "microsoft" in reader(path).lower():
                return "wsl"
        except (OSError, UnicodeError):
            continue
    return "native"


def default_context_path(home: str | Path | None = None) -> Path:
    base = Path(home) if home is not None else Path.home()
    return base / ".config" / "aiconfig" / "context.yaml"


def load_local_context(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError("CONFIG_YAML_INVALID", f"本地上下文 YAML 无效：{exc}", location=str(path)) from exc
    except OSError as exc:
        raise ConfigError("CONFIG_FILE_NOT_FOUND", f"无法读取本地上下文：{exc}", location=str(path)) from exc
    if not isinstance(value, dict):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "本地上下文必须是对象。", location=str(path))
    tags = value.get("tags", [])
    if tags is not None and (not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags)):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "context.yaml 的 tags 必须是字符串数组。", location="tags")
    return value


def detect_context(
    *,
    context_file: Path | None = None,
    profile: str | None = None,
    tags: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    system: str | None = None,
    hostname: str | None = None,
    user: str | None = None,
    home: str | None = None,
    read_text: Callable[[Path], str] | None = None,
) -> dict[str, Any]:
    detected_home = home or str(Path.home())
    context: dict[str, Any] = {
        "os": detect_os(system),
        "runtime": detect_runtime(environ, read_text),
        "hostname": hostname or socket.gethostname(),
        "user": user or getpass.getuser(),
        "home": detected_home,
        "profile": None,
        "tags": [],
    }
    local_path = context_file or default_context_path(detected_home)
    context.update(load_local_context(local_path))
    if profile is not None:
        context["profile"] = profile
    if tags is not None:
        context["tags"] = tags
    context["tags"] = list(dict.fromkeys(context.get("tags") or []))
    return context

