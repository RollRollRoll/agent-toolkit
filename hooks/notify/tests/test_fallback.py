"""纯文本回退与 4096 兜底（spec #2 REQ-006 回退部分、REQ-007）。"""
from __future__ import annotations

import io
import json
import urllib.error

import pytest

from conftest import TOKEN, RecordingOpener, process, telegram_channel, visible

from agent_notify.channels import ChannelError
from agent_notify.hook import Notification

PARSE_ERROR = "Bad Request: can't parse entities: Unsupported start tag \"x\" at byte offset 3"


@pytest.fixture(autouse=True)
def hostname(monkeypatch):
    monkeypatch.setattr("socket.gethostname", lambda: "box.local")


def _http(code, description):
    body = {"ok": False, "error_code": code, "description": description}
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(json.dumps(body).encode()))


def _n(**fields):
    base = dict(project="p", host="box", session_id="12345678", body="a<b>&c")
    base.update(fields)
    return Notification("claude", "回合完成", **base)


def test_parse_error_resends_once_as_plain_text():
    # SCN-006-B：HTML 被拒后补发一次纯文本，用户只收到这一条
    ch = telegram_channel(outcomes=[_http(400, PARSE_ERROR)])
    ch.send(_n())
    first, second = ch.opener.requests
    assert first.body["parse_mode"] == "HTML"
    assert second.body == {"chat_id": "42",
                           "text": "✅ 回合完成 · p\nClaude · box · 12345678\na<b>&c"}


def test_fallback_is_logged_without_body_or_token(env, tmp_path):
    # VAL-008：经主 seam 投递，日志记录 result=fallback，不含正文和 token
    payload = {"hook_event_name": "Stop", "session_id": "abcdef1234567890",
               "cwd": str(tmp_path / "proj"), "last_assistant_message": "SECRET-BODY-TEXT"}
    ch = telegram_channel(outcomes=[_http(400, PARSE_ERROR)])
    process("claude", payload, env, channels=[ch])
    assert len(ch.opener.requests) == 2
    log = (tmp_path / "notify.log").read_text()
    [line] = log.splitlines()
    fields = dict(p.split("=", 1) for p in line.split()[1:])
    assert fields["level"] == "info" and fields["result"] == "fallback"
    assert fields["channel"] == "telegram" and fields["session"] == "abcdef12"
    assert "SECRET-BODY-TEXT" not in log and TOKEN not in log


def test_fallback_shares_request_timeout_with_first_attempt(env, tmp_path, monkeypatch):
    # REQ-011：回退请求只拿总时限的剩余时间，不重新计时
    clock = {"now": 100.0}
    monkeypatch.setattr("agent_notify.channels.time.monotonic", lambda: clock["now"])

    class SlowOpener(RecordingOpener):
        def __call__(self, request, timeout):
            clock["now"] += 2.0  # 每次请求耗时 2 秒
            return super().__call__(request, timeout)

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"request_timeout": 3}))
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    ch = telegram_channel(env=env, opener=SlowOpener([_http(400, PARSE_ERROR)]))
    assert ch.send(_n()) == "fallback"
    assert [r.timeout for r in ch.opener.requests] == [3.0, 1.0]


def test_normal_delivery_writes_no_fallback_log(env, tmp_path):
    payload = {"hook_event_name": "Stop", "session_id": "abcdef1234567890",
               "cwd": str(tmp_path / "proj"), "last_assistant_message": "ok"}
    process("claude", payload, env, channels=[telegram_channel()])
    log = tmp_path / "notify.log"
    assert not log.exists() or "result=fallback" not in log.read_text()


def _utf16(text):
    return len(text.encode("utf-16-le")) // 2


def _long_payload(tmp_path, env):
    """SCN-007-A：summary_max_chars 3500，正文全是 & 和 emoji，长项目名和会话标题。"""
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"summary_max_chars": 3500}))
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    project = tmp_path / ("项目&<" * 40)
    project.mkdir()
    return {"hook_event_name": "Stop", "session_id": "abcdef1234567890", "cwd": str(project),
            "session_title": "标题&😀" * 60, "last_assistant_message": "&😀" * 1750}


def test_long_html_message_fits_4096_and_keeps_first_two_lines(env, tmp_path):
    ch = telegram_channel()
    process("claude", _long_payload(tmp_path, env), env, channels=[ch])
    [text] = ch.opener.texts()
    assert _utf16(text) <= 4096
    lines = visible(text).splitlines()
    assert lines[0].startswith("✅ 回合完成 · 项目&<项目&<")
    assert lines[1] == "Claude · box · abcdef12"
    assert lines[-1].endswith("…")
    assert set(lines[-1][:-1]) <= {"&", "😀"}


def test_plain_fallback_request_also_fits_4096(env, tmp_path):
    ch = telegram_channel(outcomes=[_http(400, PARSE_ERROR)])
    process("claude", _long_payload(tmp_path, env), env, channels=[ch])
    html_text, plain_text = ch.opener.texts()
    assert "parse_mode" not in ch.opener.requests[1].body
    assert _utf16(plain_text) <= 4096
    lines = plain_text.splitlines()
    assert lines[1] == "Claude · box · abcdef12"
    assert lines[-1].endswith("…")


def test_other_400_does_not_fall_back():
    ch = telegram_channel(outcomes=[_http(400, "Bad Request: chat not found")])
    with pytest.raises(ChannelError, match="chat not found"):
        ch.send(_n())
    assert len(ch.opener.requests) == 1


def test_failed_fallback_is_ordinary_failure_without_second_fallback():
    ch = telegram_channel(outcomes=[_http(400, PARSE_ERROR), _http(400, PARSE_ERROR)])
    with pytest.raises(ChannelError, match="can't parse entities"):
        ch.send(_n())
    assert len(ch.opener.requests) == 2
