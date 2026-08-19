"""声明文件查找与加载。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError


def find_config(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / "agent-config.yaml"
        if candidate.is_file():
            return candidate
    raise ConfigError("CONFIG_FILE_NOT_FOUND", "从当前目录向上未找到 agent-config.yaml。")


def load_config(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError("CONFIG_FILE_NOT_FOUND", "声明文件不存在。", location=str(path)) from exc
    except yaml.YAMLError as exc:
        raise ConfigError("CONFIG_YAML_INVALID", f"声明 YAML 无效：{exc}", location=str(path)) from exc
    except OSError as exc:
        raise ConfigError("CONFIG_FILE_NOT_FOUND", f"无法读取声明文件：{exc}", location=str(path)) from exc
    if not isinstance(value, dict):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "声明文件顶层必须是对象。", location=str(path))
    if value.get("apiVersion") != "agent-config/v1":
        raise ConfigError(
            "UNSUPPORTED_API_VERSION",
            f"不支持 apiVersion：{value.get('apiVersion')!r}，当前仅支持 agent-config/v1。",
            location="apiVersion",
        )
    return value

