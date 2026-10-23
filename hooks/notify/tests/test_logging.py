"""日志分级（REQ-010、NEG-005）：经主 seam 驱动，读取日志文件断言。"""
from __future__ import annotations

import json
import re

import pytest

from conftest import FakeChannel, process, telegram_channel


def _stop(tmp_path, msg="完成了", session="abcdefgh12345"):
    return {"hook_event_name": "Stop", "session_id": session,
            "cwd": str(tmp_path / "proj"), "last_assistant_message": msg}


def _with_config(env, tmp_path, **data):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps(data))
    return {**env, "AGENT_NOTIFY_CONFIG": str(cfg)}


def _log_lines(tmp_path):
    log = tmp_path / "notify.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def test_default_level_logs_success_with_integer_duration(env, tmp_path):
    env = _with_config(env, tmp_path, host_label="devbox")
    process("claude", _stop(tmp_path), env, channels=[telegram_channel()])
    [line] = _log_lines(tmp_path)
    assert re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d level=info agent=claude host=devbox "
                    r"session=abcdefgh event=回合完成 channel=telegram result=ok "
                    r"duration_ms=\d+$", line)


def _http(code, description):
    import io
    import urllib.error
    body = json.dumps({"ok": False, "description": description}).encode()
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(body))


def test_rejected_request_logs_fail_line_with_api_error_type(env, tmp_path):
    env = _with_config(env, tmp_path, host_label="devbox")
    channel = telegram_channel([_http(401, "Unauthorized")])
    process("claude", _stop(tmp_path), env, channels=[channel])
    [line] = _log_lines(tmp_path)
    assert re.search(r" level=error agent=claude host=devbox session=abcdefgh event=回合完成 "
                     r"channel=telegram result=fail duration_ms=\d+ error=api status=401 "
                     r'detail="Telegram HTTP 401: Unauthorized"$', line)


def test_unreachable_network_logs_fail_line_with_network_error_type(env, tmp_path):
    import urllib.error
    channel = telegram_channel([urllib.error.URLError("down")] * 3)
    process("claude", _stop(tmp_path), env, channels=[channel])
    [line] = _log_lines(tmp_path)
    assert " result=fail " in line and " error=network " in line


def test_error_level_skips_success_but_still_logs_failure(env, tmp_path):
    env = _with_config(env, tmp_path, log_level="error")
    process("claude", _stop(tmp_path), env, channels=[telegram_channel()])
    assert _log_lines(tmp_path) == []
    process("claude", _stop(tmp_path), env, channels=[telegram_channel([_http(401, "x")])])
    [line] = _log_lines(tmp_path)
    assert " result=fail " in line


def test_invalid_level_is_treated_as_info(env, tmp_path):
    for value in ("verbose", 3):
        (tmp_path / "notify.log").unlink(missing_ok=True)
        env2 = _with_config(env, tmp_path, log_level=value)
        process("claude", _stop(tmp_path), env2, channels=[telegram_channel()])
        [line] = _log_lines(tmp_path)
        assert " level=info " in line and " result=ok " in line


def test_debug_logs_skip_reason_when_turn_complete_disabled(env, tmp_path):
    env = _with_config(env, tmp_path, log_level="debug", events={"turn_complete": False},
                       host_label="devbox")
    fake = FakeChannel()
    process("claude", _stop(tmp_path), env, channels=[fake])
    assert fake.sent == []
    [line] = _log_lines(tmp_path)
    assert re.search(r" level=debug agent=claude host=devbox session=abcdefgh hook=Stop "
                     r"event=回合完成 "
                     r"result=skip reason=event_disabled$", line)


def test_debug_logs_subagent_and_unsupported_skips(env, tmp_path):
    env = _with_config(env, tmp_path, log_level="debug", host_label="devbox")
    process("claude", {**_stop(tmp_path), "agent_id": "sub1"}, env, channels=[FakeChannel()])
    process("codex", {"hook_event_name": "SessionStart", "session_id": "zz"}, env,
            channels=[FakeChannel()])
    first, second = _log_lines(tmp_path)
    assert " hook=Stop result=skip reason=subagent" in first
    assert (" agent=codex host=devbox session=zz hook=SessionStart result=skip "
            "reason=unsupported") in second


def test_skips_are_not_logged_at_info(env, tmp_path):
    env = _with_config(env, tmp_path, events={"turn_complete": False})
    process("claude", _stop(tmp_path), env, channels=[FakeChannel()])
    assert _log_lines(tmp_path) == []


def test_debug_log_never_contains_summary_command_or_title(env, tmp_path):
    from conftest import TOKEN
    marker = "ZQX-UNIQUE-MARKER-7731"
    env = _with_config(env, tmp_path, log_level="debug", events={"waiting_input": False})
    stop = {**_stop(tmp_path, f"摘要 {marker}"), "session_title": f"标题 {marker}"}
    permission = {"hook_event_name": "PermissionRequest", "session_id": "perm1234",
                  "cwd": str(tmp_path), "tool_name": "Bash",
                  "tool_input": {"command": f"echo {marker} {TOKEN}"}}
    idle = {"hook_event_name": "Notification", "notification_type": "idle_prompt",
            "session_id": "idle1234", "message": f"等待 {marker}"}
    process("claude", stop, env, channels=[telegram_channel()])
    process("codex", permission, env, channels=[telegram_channel([_http(400, "Bad Request")])])
    process("claude", idle, env, channels=[telegram_channel()])
    log = (tmp_path / "notify.log").read_text(encoding="utf-8")
    assert len(log.splitlines()) == 3
    assert marker not in log and TOKEN not in log


@pytest.mark.parametrize("configured, effective",
                         [(30, 30), (0, 1), ("x", 10), (120, 60), (None, 10)])
def test_request_timeout_is_normalized_and_passed_to_opener(env, tmp_path, configured,
                                                            effective):
    data = {} if configured is None else {"request_timeout": configured}
    channel = telegram_channel(env=_with_config(env, tmp_path, **data))
    process("claude", _stop(tmp_path), env, channels=[channel])
    [request] = channel.opener.requests
    assert request.timeout == pytest.approx(effective, abs=0.5)


def test_retries_share_the_remaining_time_budget(env, tmp_path, monkeypatch):
    import urllib.error
    from conftest import RecordingOpener

    clock = [1000.0]
    monkeypatch.setattr("agent_notify.channels.time.monotonic", lambda: clock[0])

    class SlowOpener(RecordingOpener):
        """每次请求耗时 12 秒后失败。"""

        def __call__(self, request, timeout):
            clock[0] += 12
            return super().__call__(request, timeout)

    opener = SlowOpener([urllib.error.URLError("slow")] * 3)
    channel = telegram_channel(env=_with_config(env, tmp_path, request_timeout=30),
                               opener=opener)
    process("claude", _stop(tmp_path), env, channels=[channel])
    assert [r.timeout for r in opener.requests] == [30, 18, 6]


def test_invalid_payload_logs_key_value_fail_line(env, tmp_path):
    from agent_notify.hook import run
    assert run("claude", "not json{", env, spawn=False) == 0
    [line] = _log_lines(tmp_path)
    assert re.search(r" level=error agent=claude result=fail error=invalid_payload$", line)


def test_debug_logs_missing_credentials_skip(tmp_path):
    from agent_notify.hook import run
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"log_level": "debug", "host_label": "devbox"}))
    env = {"AGENT_NOTIFY_CONFIG": str(cfg), "AGENT_NOTIFY_LOG": str(tmp_path / "notify.log"),
           "HOME": str(tmp_path)}
    run("claude", json.dumps(_stop(tmp_path)), env, spawn=False)
    [line] = _log_lines(tmp_path)
    assert re.search(r" level=debug agent=claude host=devbox session=abcdefgh event=回合完成 "
                     r"channel=telegram result=skip reason=missing_credentials$", line)
