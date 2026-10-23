"""本地日志：单文件追加，超过大小上限时轮转一份，写入前经过 REQ-005 遮蔽。"""
from __future__ import annotations

import time

from . import redaction

MAX_BYTES = 512 * 1024


def redact(config, text):
    """按 REQ-005 的同一套规则遮蔽消息，并替换当前配置的 token。"""
    return redaction.redact(text, config.telegram_token)


def write_log(config, message):
    message = redact(config, message)
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {message}\n"
    path = config.log_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > MAX_BYTES:
            path.replace(path.with_name(path.name + ".1"))
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        # 日志写不了也不能影响 Agent
        pass
