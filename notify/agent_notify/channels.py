"""通知渠道。每个渠道实现 send(notification)，失败时抛异常。"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

TOTAL_TIMEOUT = 10.0
MAX_RETRIES = 2


class ChannelError(Exception):
    pass


class TelegramChannel:
    name = "telegram"

    def __init__(self, token, chat_id, render, opener=urllib.request.urlopen):
        self.token = token
        self.chat_id = chat_id
        self.render = render
        self.opener = opener

    def send(self, notification):
        if not self.token or not self.chat_id:
            raise ChannelError("缺少 Telegram token 或 chat_id")
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        # 纯文本发送，不设 parse_mode，避免特殊字符导致解析失败
        body = json.dumps({"chat_id": self.chat_id, "text": self.render(notification)}).encode()
        deadline = time.monotonic() + TOTAL_TIMEOUT
        last_error = None
        for _ in range(MAX_RETRIES + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            request = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}
            )
            try:
                with self.opener(request, timeout=remaining) as resp:
                    resp.read()
                return
            except urllib.error.HTTPError as exc:
                body_json = _payload(exc)
                description = body_json.get("description", exc.reason)
                last_error = ChannelError(f"Telegram HTTP {exc.code}: {description}")
                if exc.code == 429:
                    wait = _retry_after(body_json)
                    if wait >= deadline - time.monotonic():
                        break
                    time.sleep(wait)
                    continue
                if exc.code < 500:
                    # 4xx（token 或 chat_id 错误）重试无意义
                    break
            except (urllib.error.URLError, OSError) as exc:
                last_error = ChannelError(f"网络错误: {getattr(exc, 'reason', exc)}")
        raise last_error or ChannelError("发送超时")


def _payload(exc):
    try:
        return json.loads(exc.read().decode("utf-8", "replace"))
    except (ValueError, OSError):
        return {}


def _retry_after(body_json):
    params = body_json.get("parameters") or {}
    try:
        return float(params.get("retry_after", 1))
    except (TypeError, ValueError):
        return 1.0


def build_channels(config, render):
    channels = []
    for name in config.channels:
        if name == "telegram":
            channels.append(TelegramChannel(config.telegram_token, config.telegram_chat_id, render))
    return channels
