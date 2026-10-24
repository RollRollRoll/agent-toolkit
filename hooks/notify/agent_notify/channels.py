"""通知渠道。每个渠道实现 send(notification)，失败时抛异常。"""
from __future__ import annotations

import dataclasses
import html
import json
import time
import urllib.error
import urllib.request

from .config import (AGENT_LABELS, DEFAULT_REQUEST_TIMEOUT, ERROR, PERMISSION, TEST_NOTIFICATION,
                     TURN_COMPLETE, TURN_END_WAITING, WAITING_INPUT, truncate)

TOTAL_TIMEOUT = DEFAULT_REQUEST_TIMEOUT
MAX_RETRIES = 2
MAX_TEXT_UTF16 = 4096  # Telegram 单条消息上限，按 UTF-16 码元计（REQ-007）
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
        params = {"chat_id": self.chat_id, "text": fit_text(render_html, notification), "parse_mode": "HTML"}
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
            except ChannelError as exc:
                if result == FALLBACK:
                    # 纯文本补发只发 1 次：任何失败都按普通失败处理，不重试（spec #2 §3.4）
                    raise
                if not isinstance(exc, TelegramAPIError):
                    last_error = exc
                    attempts += 1
                    continue
                last_error = exc
                if _is_parse_error(exc):
                    # REQ-006：HTML 被拒，用同一组字段排版成纯文本补发一次；补发不计入重试次数
                    params = {"chat_id": self.chat_id, "text": fit_text(render_plain, notification)}
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
                    # 4xx（token 或 chat_id 错误）重试无意义
                    break
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


def _layout(notification, esc, bold, code, quote, body=None):
    """按 REQ-001 布局逐行拼接；缺失字段整项省略。各渠道格式由传入的函数决定。

    第一行只放图标、项目和主机，系统弹窗里一眼看出来源；
    第二行依次是事件名、Agent、分支、会话短 ID。
    body 用来排版正文，默认与其他字段一样只做转义。
    """
    icon, label = EVENT_DISPLAY.get(notification.event_type, ("", notification.event_type))
    source = " @ ".join(p for p in (notification.project, notification.host) if p)
    title = " ".join(p for p in (icon, source or label) if p)
    meta = [esc(p) for p in (label if source else "", AGENT_LABELS.get(notification.agent, ""),
                             notification.branch) if p]
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
        lines.append(quote((body or esc)(notification.body)))
    return "\n".join(lines)


def _utf16_len(text):
    return len(text.encode("utf-16-le")) // 2


def fit_text(render, notification):
    """REQ-007：渲染结果超过 4096 个 UTF-16 码元时只截短正文并以 … 结尾。

    每次截短后都重新渲染（重新转义）再计数，二分出能放下的最长正文；
    标题行与第二行不参与截短，始终完整。
    """
    text = render(notification)
    if _utf16_len(text) <= MAX_TEXT_UTF16 or not notification.body:
        return text
    body = notification.body

    def attempt(keep):
        # keep 始终小于正文长度，truncate 一定会截短并补 …
        return render(dataclasses.replace(notification, body=truncate(body, keep)))

    low, high = 0, len(body) - 1  # 至少截掉一个字符
    while low < high:
        mid = (low + high + 1) // 2
        if _utf16_len(attempt(mid)) <= MAX_TEXT_UTF16:
            low = mid
        else:
            high = mid - 1
    return attempt(low)


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
