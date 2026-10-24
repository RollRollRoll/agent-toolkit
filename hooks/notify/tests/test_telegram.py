from __future__ import annotations

import io
import json
import urllib.error

import pytest

from agent_notify.channels import ChannelError, TelegramChannel
from agent_notify.hook import Notification


def _n():
    return Notification("claude", "回合完成", project="p", session_id="12345678", body="a<b>*")


class Opener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return io.BytesIO(b'{"ok":true}')


def _http(code, body):
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(json.dumps(body).encode()))


def test_sends_plain_text_to_chat():
    opener = Opener([None])
    TelegramChannel("T", "42", opener=opener).send(_n())
    body = json.loads(opener.requests[0].data)
    # HTML 模式：字段值转义后嵌入
    assert body == {"chat_id": "42", "parse_mode": "HTML",
                    "text": "<b>✅ p</b>\n回合完成 · Claude · <code>12345678</code>\n"
                            "<blockquote expandable>a&lt;b&gt;*</blockquote>"}


def test_network_error_retries_twice_then_raises():
    opener = Opener([urllib.error.URLError("down")] * 3)
    with pytest.raises(ChannelError, match="网络错误"):
        TelegramChannel("T", "42", opener=opener).send(_n())
    assert len(opener.requests) == 3


def test_4xx_not_retried_and_reports_description():
    opener = Opener([_http(401, {"ok": False, "description": "Unauthorized"})])
    with pytest.raises(ChannelError, match="Unauthorized"):
        TelegramChannel("T", "42", opener=opener).send(_n())
    assert len(opener.requests) == 1


def test_429_waits_retry_after_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    opener = Opener([_http(429, {"ok": False, "description": "Too Many",
                                 "parameters": {"retry_after": 1}}), None])
    TelegramChannel("T", "42", opener=opener).send(_n())
    assert len(opener.requests) == 2


def test_http_200_with_unparseable_body_counts_as_delivered():
    class Garbled(Opener):
        def __call__(self, request, timeout):
            self.requests.append(request)
            return io.BytesIO(b"<html>proxy page</html>")

    opener = Garbled([])
    TelegramChannel("T", "42", opener=opener).send(_n())
    assert len(opener.requests) == 1
