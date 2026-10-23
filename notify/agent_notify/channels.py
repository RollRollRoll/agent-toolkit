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


class TelegramAPIError(ChannelError):
    """Bot API 返回 HTTP 错误；保留状态码与响应体供重试判断。"""

    def __init__(self, code, description, body):
        super().__init__(f"Telegram HTTP {code}: {description}")
        self.code = code
        self.body = body


def telegram_call(token, method, params=None, opener=urllib.request.urlopen, timeout=TOTAL_TIMEOUT):
    """单次调用 Bot API，返回 result 字段；HTTP 错误抛 TelegramAPIError，网络错误抛 ChannelError。"""
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(params or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as exc:
        body = _payload(exc)
        raise TelegramAPIError(exc.code, body.get("description", exc.reason), body) from None
    except (urllib.error.URLError, OSError) as exc:
        raise ChannelError(f"网络错误: {getattr(exc, 'reason', exc)}") from None
    except ValueError:
        raise ChannelError("Telegram 返回了无法解析的响应") from None
    return data.get("result")


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
        # 纯文本发送，不设 parse_mode，避免特殊字符导致解析失败
        params = {"chat_id": self.chat_id, "text": self.render(notification)}
        deadline = time.monotonic() + TOTAL_TIMEOUT
        last_error = None
        for _ in range(MAX_RETRIES + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                telegram_call(self.token, "sendMessage", params, self.opener, remaining)
                return
            except TelegramAPIError as exc:
                last_error = exc
                if exc.code == 429:
                    wait = _retry_after(exc.body)
                    if wait >= deadline - time.monotonic():
                        break
                    time.sleep(wait)
                    continue
                if exc.code < 500:
                    # 4xx（token 或 chat_id 错误）重试无意义
                    break
            except ChannelError as exc:
                last_error = exc
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
