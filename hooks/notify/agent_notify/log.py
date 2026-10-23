"""本地日志：单文件追加，超过大小上限时轮转一份，写入前经过 REQ-005 遮蔽。"""
from __future__ import annotations

import json
import re
import time

from . import redaction

MAX_BYTES = 512 * 1024

# 日志级别从低到高；配置的级别决定最多记录到哪一级
LEVELS = ("error", "info", "debug")
_NEEDS_QUOTE = re.compile(r'[\s"=]')


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


def log_event(config, level, **fields):
    """按级别过滤后写一行 `时间 level=… key=value …`；空字段省略。"""
    configured = getattr(config, "log_level", "info")
    if LEVELS.index(level) > LEVELS.index(configured if configured in LEVELS else "info"):
        return
    pairs = {"level": level, **fields}
    write_log(config, " ".join(f"{k}={_value(v)}" for k, v in pairs.items() if v not in (None, "")))


def _value(value):
    # 含空白、引号或等号的值用 JSON 字符串引起来，保证一行一条且可解析
    text = str(value)
    return json.dumps(text, ensure_ascii=False) if _NEEDS_QUOTE.search(text) else text
