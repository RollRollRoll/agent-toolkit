"""通知渠道。每个渠道实现 send(notification)，失败时抛异常。"""
from __future__ import annotations

import html
import json
import time
import urllib.error
import urllib.request

from .config import (AGENT_LABELS, ERROR, PERMISSION, TEST_NOTIFICATION, TURN_COMPLETE,
                     TURN_END_WAITING, WAITING_INPUT)

TOTAL_TIMEOUT = 10.0
MAX_RETRIES = 2
FALLBACK = "fallback"  # send() 的返回值：以纯文本回退送达


class ChannelError(Exception):
    """渠道失败；kind 是写入日志 error= 的错误类型。"""

    def __init__(self, message, kind="channel"):
        super().__init__(message)
        self.kind = kind


class TelegramAPIError(ChannelError):
    """Bot API 返回 HTTP 错误；保留状态码与响应体供重试判断。"""

    def __init__(self, code, description, body):
        super().__init__(f"Telegram HTTP {code}: {description}", kind="api")
        self.code = code
        self.body = body


class TelegramResponseError(ChannelError):
    """HTTP 200 但响应体无法解析：请求已被 Telegram 接收。"""


def telegram_call(token, method, params=None, opener=urllib.request.urlopen, timeout=TOTAL_TIMEOUT):
    """单次调用 Bot API，返回 result 字段；HTTP 错误抛 TelegramAPIError，网络错误抛 ChannelError。"""
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(params or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        body = _payload(exc)
        raise TelegramAPIError(exc.code, body.get("description", exc.reason), body) from None
    except (urllib.error.URLError, OSError) as exc:
        raise ChannelError(f"网络错误: {getattr(exc, 'reason', exc)}", kind="network") from None
    # 解析放在网络调用之外：200 已代表请求被接收，解析失败不能被当成网络失败重试
    try:
        data = json.loads(raw.decode("utf-8", "replace") or "{}")
    except ValueError:
        raise TelegramResponseError("Telegram 返回了无法解析的响应") from None
    return data.get("result") if isinstance(data, dict) else None


class TelegramChannel:
    name = "telegram"

    def __init__(self, token, chat_id, opener=urllib.request.urlopen, timeout=TOTAL_TIMEOUT):
        self.token = token
        self.chat_id = chat_id
        self.opener = opener
        self.timeout = timeout

    def send(self, notification):
        """发送一条通知；以纯文本回退送达时返回 FALLBACK，否则返回 None。"""
        if not self.token or not self.chat_id:
            raise ChannelError("缺少 Telegram token 或 chat_id", kind="config")
        params = {"chat_id": self.chat_id, "text": render_html(notification), "parse_mode": "HTML"}
        # 富文本请求、重试与纯文本回退共用同一个 request_timeout 总时限（REQ-011）：每次请求只拿剩余时间
        deadline = time.monotonic() + self.timeout
        result = None
        last_error = None
        attempts = 0
        while attempts <= MAX_RETRIES:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                telegram_call(self.token, "sendMessage", params, self.opener, remaining)
                return result
            except TelegramResponseError:
                # HTTP 200 已送达，不重试，避免重复发送
                return result
            except TelegramAPIError as exc:
                last_error = exc
                if result is None and _is_parse_error(exc):
                    # REQ-006：HTML 被拒，用同一组字段排版成纯文本补发一次；补发不计入重试次数
                    params = {"chat_id": self.chat_id, "text": render_plain(notification)}
                    result = FALLBACK
                    continue
                if exc.code == 429:
                    wait = _retry_after(exc.body)
                    if wait >= deadline - time.monotonic():
                        break
                    time.sleep(wait)
                    attempts += 1
                    continue
                if exc.code < 500:
                    # 4xx（token 或 chat_id 错误、补发仍被拒）重试无意义
                    break
            except ChannelError as exc:
                last_error = exc
            attempts += 1
        raise last_error or ChannelError("发送超时", kind="timeout")


def _is_parse_error(exc):
    """Telegram 拒绝解析 HTML：400 且描述包含 can't parse entities。"""
    return exc.code == 400 and "can't parse entities" in str(exc.body.get("description", ""))


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


# 通知事件 → (图标, 显示名)，见 spec #2 REQ-001 表格
EVENT_DISPLAY = {
    TURN_COMPLETE: ("✅", "回合完成"),
    TURN_END_WAITING: ("✅", "回合结束"),
    WAITING_INPUT: ("💬", "等待输入"),
    PERMISSION: ("🔐", "需要授权"),
    ERROR: ("❌", "异常"),
    TEST_NOTIFICATION: ("🔔", "测试通知"),
}


def _layout(notification, esc, bold, code, quote):
    """按 REQ-001 布局逐行拼接；缺失字段整项省略。各渠道格式由传入的函数决定。"""
    icon, label = EVENT_DISPLAY.get(notification.event_type, ("", notification.event_type))
    title = " · ".join(p for p in (f"{icon} {label}".strip(), notification.project) if p)
    meta = [esc(p) for p in (AGENT_LABELS.get(notification.agent, ""),
                             notification.host, notification.branch) if p]
    if notification.session_id:
        meta.append(code(esc(notification.session_id)))
    lines = [bold(esc(title))]
    if meta:
        lines.append(" · ".join(meta))
    if notification.session_title:
        lines.append(esc(f"会话：{notification.session_title}"))
    if notification.error_kind:
        lines.append(esc(f"错误类别：{notification.error_kind}"))
    if notification.body:
        lines.append(quote(esc(notification.body)))
    return "\n".join(lines)


def render_html(notification):
    """Telegram HTML 排版：字段值先转义，标题加粗、会话短 ID 等宽、正文放折叠引用块。"""
    return _layout(notification, lambda t: html.escape(t, quote=False),
                   lambda t: f"<b>{t}</b>", lambda t: f"<code>{t}</code>",
                   lambda t: f"<blockquote expandable>{t}</blockquote>")


def render_plain(notification):
    """同一布局的纯文本形式，不含标签（供纯文本发送使用）。"""
    same = lambda t: t  # noqa: E731
    return _layout(notification, same, same, same, same)


def build_channels(config, opener=urllib.request.urlopen):
    channels = []
    for name in config.channels:
        if name == "telegram":
            channels.append(TelegramChannel(config.telegram_token, config.telegram_chat_id,
                                            opener=opener, timeout=config.request_timeout))
    return channels
