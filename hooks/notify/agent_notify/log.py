"""本地日志：单文件追加，超过大小上限时轮转一份，写入前对 token 脱敏。"""
from __future__ import annotations

import time

MAX_BYTES = 512 * 1024


def redact(config, text):
    """把消息里的 token 替换为 ***。"""
    return text.replace(config.telegram_token, "***") if config.telegram_token else text


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
