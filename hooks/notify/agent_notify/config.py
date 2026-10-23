"""配置加载：环境变量优先，其次用户级 JSON 配置文件。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# 通知事件类型（与 GLOSSARY.md 一致）
TURN_COMPLETE = "回合完成"
WAITING_INPUT = "等待输入"
PERMISSION = "需要授权"
ERROR = "异常"
TURN_END_WAITING = "回合结束，等待输入"  # Codex 合并事件
TEST_NOTIFICATION = "测试通知"  # 测试命令与配置向导发送的通知

# 支持的 Agent 及其显示名
AGENT_LABELS = {"claude": "Claude", "codex": "Codex"}

# 配置文件里事件开关使用的英文键
EVENT_KEYS = {
    "turn_complete": (TURN_COMPLETE,),
    "waiting_input": (WAITING_INPUT,),
    "permission": (PERMISSION,),
    "error": (ERROR,),
}


@dataclass
class Config:
    telegram_token: str = ""
    telegram_chat_id: str = ""
    privacy: bool = False
    host_label: str = ""  # 用户设定的主机标签，已去掉首尾空白
    disabled_events: set = field(default_factory=set)
    channels: list = field(default_factory=lambda: ["telegram"])
    log_path: Path = Path()

    def event_enabled(self, event_type):
        return event_type not in self.disabled_events


def default_config_path(env):
    base = env.get("XDG_CONFIG_HOME") or str(Path(env.get("HOME", "~")).expanduser() / ".config")
    return Path(base) / "agent-notify" / "config.json"


def default_log_path(env):
    base = env.get("XDG_STATE_HOME") or str(Path(env.get("HOME", "~")).expanduser() / ".local" / "state")
    return Path(base) / "agent-notify" / "notify.log"


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def config_path(env):
    return Path(env.get("AGENT_NOTIFY_CONFIG") or default_config_path(env))


def read_config_file(path):
    """读取配置文件：返回 (配置字典, 是否损坏)；文件不存在视为空配置。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, False
    except (OSError, ValueError):
        return {}, True
    return (data, False) if isinstance(data, dict) else ({}, True)


def telegram_section(data):
    return data.get("telegram") if isinstance(data.get("telegram"), dict) else {}


def load_config(env):
    data, _ = read_config_file(config_path(env))
    telegram = telegram_section(data)

    # Codex 合并事件同时属于两类：只在 turn_complete 和 waiting_input 都关闭时才关闭
    events = data.get("events") if isinstance(data.get("events"), dict) else {}
    off = {k for k, v in events.items() if v is False}
    disabled = set()
    for key, types in EVENT_KEYS.items():
        if key in off:
            disabled.update(types)
    if {"turn_complete", "waiting_input"} <= off:
        disabled.add(TURN_END_WAITING)

    channels = data.get("channels")
    if not isinstance(channels, list) or not channels:
        channels = ["telegram"]

    privacy = env.get("AGENT_NOTIFY_PRIVACY")
    return Config(
        telegram_token=env.get("AGENT_NOTIFY_TELEGRAM_TOKEN") or str(telegram.get("token") or ""),
        telegram_chat_id=env.get("AGENT_NOTIFY_TELEGRAM_CHAT_ID") or str(telegram.get("chat_id") or ""),
        privacy=_truthy(privacy) if privacy is not None else bool(data.get("privacy", False)),
        host_label=str(data.get("host_label") or "").strip(),
        disabled_events=disabled,
        channels=[str(c) for c in channels],
        log_path=Path(env.get("AGENT_NOTIFY_LOG") or default_log_path(env)),
    )
