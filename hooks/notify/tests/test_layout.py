"""新消息布局、主机与 HTML 发送（spec #2 REQ-001、REQ-002、REQ-006 转义部分）。

经 process 走完整链路，渠道用真实 TelegramChannel；先把请求体的 HTML 解析成
用户可见文本再比较布局，标签与转义只在少数测试里单独检查。
"""
from __future__ import annotations

import json
import subprocess

import pytest

from conftest import process, telegram_channel, visible


@pytest.fixture(autouse=True)
def hostname(monkeypatch):
    """默认机器名固定为 box.local；个别测试再改。"""
    names = {"value": "box.local"}
    monkeypatch.setattr("socket.gethostname", lambda: names["value"])
    return names


def _config(env, tmp_path, **data):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(data))
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    return env


def _repo(tmp_path, name, branch):
    path = tmp_path / name
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    return path


def _send(agent, payload, env):
    """返回 (请求体, 可见文本的各行)。"""
    channel = telegram_channel()
    process(agent, payload, env, channels=[channel])
    [request] = channel.opener.requests
    return request.body, visible(request.body["text"]).split("\n")


def _stop(cwd, **extra):
    return {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e6f", "cwd": str(cwd),
            "last_assistant_message": "已完成重构", **extra}


def test_turn_complete_in_git_repo(env, tmp_path):
    # SCN-001-A
    _config(env, tmp_path, host_label="mbp")
    repo = _repo(tmp_path, "agent-toolkit", "main")
    body, lines = _send("claude", _stop(repo), env)
    assert lines == ["✅ 回合完成 · agent-toolkit", "Claude · mbp · main · 1a2b3c4d", "已完成重构"]
    assert "<blockquote expandable>已完成重构</blockquote>" in body["text"]


def test_non_git_dir_has_no_branch_and_no_double_separator(env, tmp_path):
    # SCN-001-B
    d = tmp_path / "plain"
    d.mkdir()
    payload = {"hook_event_name": "Stop", "session_id": "c0dex999zzz", "cwd": str(d),
               "last_assistant_message": "done"}
    body, lines = _send("codex", payload, env)
    assert lines[:2] == ["✅ 回合结束 · plain", "Codex · box · c0dex999"]
    assert "· ·" not in visible(body["text"])


def test_no_summary_means_no_blockquote_and_no_trailing_blank(env, tmp_path):
    # SCN-001-C
    body, lines = _send("claude", _stop(tmp_path / "p", last_assistant_message=None), env)
    assert lines == ["✅ 回合完成 · p", "Claude · box · 1a2b3c4d"]
    assert "blockquote" not in body["text"] and not body["text"].endswith("\n")


def test_missing_session_id_omits_short_id(env, tmp_path):
    # SCN-001-D
    payload = _stop(tmp_path / "p")
    del payload["session_id"]
    _, lines = _send("claude", payload, env)
    assert lines[:2] == ["✅ 回合完成 · p", "Claude · box"]


def test_session_title_and_error_kind_lines_in_order(env, tmp_path):
    payload = {"hook_event_name": "StopFailure", "error": "rate_limit",
               "error_details": "429 Too Many Requests", "session_id": "e" * 12,
               "cwd": str(tmp_path / "p"), "session_title": "重构登录"}
    _, lines = _send("claude", payload, env)
    assert lines == ["❌ 异常 · p", "Claude · box · eeeeeeee", "会话：重构登录",
                     "错误类别：rate_limit", "rate_limit · 429 Too Many Requests"]


def test_short_id_is_monospace_and_title_bold(env, tmp_path):
    body, _ = _send("claude", _stop(tmp_path / "p"), env)
    assert body["text"].startswith("<b>✅ 回合完成 · p</b>\n")
    assert "<code>1a2b3c4d</code>" in body["text"]


@pytest.mark.parametrize("agent,payload,first", [
    ("claude", {"hook_event_name": "Stop"}, "✅ 回合完成 · p"),
    ("codex", {"hook_event_name": "Stop"}, "✅ 回合结束 · p"),
    ("claude", {"hook_event_name": "Notification", "notification_type": "idle_prompt"},
     "💬 等待输入 · p"),
    ("claude", {"hook_event_name": "Notification", "notification_type": "permission_prompt"},
     "🔐 需要授权 · p"),
    ("codex", {"hook_event_name": "PermissionRequest", "tool_name": "Bash"}, "🔐 需要授权 · p"),
    ("claude", {"hook_event_name": "StopFailure", "error": "unknown"}, "❌ 异常 · p"),
])
def test_event_icons_and_display_names(env, tmp_path, agent, payload, first):
    _, lines = _send(agent, {**payload, "session_id": "s" * 10, "cwd": str(tmp_path / "p")}, env)
    assert lines[0] == first


def test_test_notification_layout(env, tmp_path, monkeypatch):
    # 测试命令发出的测试通知同样显示主机
    import io
    from agent_notify import testcmd
    _config(env, tmp_path, host_label="mbp")
    channel = telegram_channel()
    monkeypatch.setattr(testcmd, "build_channels", lambda config: [channel])
    assert testcmd.main(env, out=io.StringIO()) == 0
    lines = visible(channel.opener.texts()[0]).split("\n")
    assert lines == ["🔔 测试通知 · agent-notify", "mbp", "如果你看到这条消息，说明配置正确。"]


def test_test_notification_without_host_skips_second_line():
    from agent_notify.testcmd import make_test_notification
    channel = telegram_channel()
    channel.send(make_test_notification())
    assert visible(channel.opener.texts()[0]).split("\n") == [
        "🔔 测试通知 · agent-notify", "如果你看到这条消息，说明配置正确。"]


def test_configured_host_label(env, tmp_path):
    # SCN-002-A：配置值优先于机器名，首尾空白去掉
    _config(env, tmp_path, host_label="  home-linux  ")
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[1] == "Claude · home-linux · 1a2b3c4d"


@pytest.mark.parametrize("label", [None, "", "   "])
def test_blank_host_label_falls_back_to_short_hostname(env, tmp_path, hostname, label):
    # SCN-002-B
    hostname["value"] = "chenjinfans-MacBook-Pro.local"
    data = {} if label is None else {"host_label": label}
    _config(env, tmp_path, **data)
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[1] == "Claude · chenjinfans-MacBook-Pro · 1a2b3c4d"


def test_long_host_truncated_to_32_chars(env, tmp_path, hostname):
    hostname["value"] = "a" * 40 + ".example.com"
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[1] == "Claude · " + "a" * 32 + "… · 1a2b3c4d"


def test_host_omitted_when_unavailable(env, tmp_path, hostname):
    hostname["value"] = ""
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[1] == "Claude · 1a2b3c4d"


def test_special_characters_shown_verbatim(env, tmp_path):
    # SCN-006-A：所有字段值先转义，解析后的可见文本与原文一致
    _config(env, tmp_path, host_label="h<1>&")
    repo = _repo(tmp_path, "a&b", "fix/<x>")
    payload = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb2",
               "cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": 'echo "<a>" && ls'}}
    body, lines = _send("codex", payload, env)
    assert body["parse_mode"] == "HTML"
    assert lines == ["🔐 需要授权 · a&b", "Codex · h<1>& · fix/<x> · bbbbbbbb",
                     'Bash: echo "<a>" && ls']
    assert "&lt;a&gt;" in body["text"] and "&amp;&amp;" in body["text"]
