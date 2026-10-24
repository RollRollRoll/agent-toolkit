"""消息布局、主机与 HTML 发送（spec #19 三段式排版，spec #2 REQ-002、REQ-006 转义部分）。

第一部分是加粗的「图标 事件 · 项目 @ 主机」，第二部分一行一个「标签：值」
（Agent、分支、会话、标题、错误类别），第三部分是正文，部分之间空一行。
经 process 走完整链路，渠道用真实 TelegramChannel；先把请求体的 HTML 解析成
用户可见文本再比较布局，标签与转义只在少数测试里单独检查。
"""
from __future__ import annotations

import subprocess

import pytest

from conftest import http_error, send_once, telegram_channel, visible, with_config

pytestmark = pytest.mark.usefixtures("hostname")


def _repo(tmp_path, name, branch):
    path = tmp_path / name
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    return path


def _send(agent, payload, env):
    """返回 (请求体, 可见文本的各行)。"""
    [body] = send_once(agent, payload, env)
    return body, visible(body["text"]).split("\n")


def _stop(cwd, **extra):
    return {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e6f", "cwd": str(cwd),
            "last_assistant_message": "已完成重构", **extra}


def test_turn_complete_in_git_repo(env, tmp_path):
    # spec #19 SCN-001-A
    with_config(env, tmp_path, host_label="mbp")
    repo = _repo(tmp_path, "agent-toolkit", "main")
    body, lines = _send("claude", _stop(repo), env)
    # 三部分：标题行、一行一个标签的来源明细、正文，部分之间空一行
    assert lines == ["✅ 回合完成 · agent-toolkit @ mbp", "",
                     "Agent：Claude", "分支：main", "会话：1a2b3c4d", "", "已完成重构"]
    assert "<blockquote expandable>已完成重构</blockquote>" in body["text"]


def test_non_git_dir_has_no_branch_line(env, tmp_path):
    # spec #19 SCN-003-B
    d = tmp_path / "plain"
    d.mkdir()
    payload = {"hook_event_name": "Stop", "session_id": "c0dex999zzz", "cwd": str(d),
               "last_assistant_message": "done"}
    _, lines = _send("codex", payload, env)
    # 非 git 目录没有分支行，其余行顺序不变
    assert lines == ["✅ 回合结束 · plain @ box", "", "Agent：Codex", "会话：c0dex999", "", "done"]


def test_no_summary_means_no_blockquote_and_no_trailing_blank(env, tmp_path):
    # spec #19 SCN-001-B
    body, lines = _send("claude", _stop(tmp_path / "p", last_assistant_message=None), env)
    assert lines == ["✅ 回合完成 · p @ box", "", "Agent：Claude", "会话：1a2b3c4d"]
    assert "blockquote" not in body["text"] and not body["text"].endswith("\n")


def test_missing_session_id_omits_short_id(env, tmp_path):
    # spec #19 SCN-003-C
    payload = _stop(tmp_path / "p")
    del payload["session_id"]
    _, lines = _send("claude", payload, env)
    assert lines == ["✅ 回合完成 · p @ box", "", "Agent：Claude", "", "已完成重构"]


@pytest.mark.parametrize("agent,payload", [
    ("claude", {"hook_event_name": "Stop", "last_assistant_message": "\n \nhi\n\n"}),
    ("claude", {"hook_event_name": "Notification", "notification_type": "idle_prompt",
                "message": "\n\nhi\n"}),
    ("codex", {"hook_event_name": "PermissionRequest", "tool_name": "Bash",
               "tool_input": {"command": "\nhi\n\n"}}),
    ("claude", {"hook_event_name": "StopFailure", "error": "rate_limit",
                "error_details": "\n\nhi\n  \n"}),
])
def test_body_blank_lines_do_not_add_extra_spacing(env, tmp_path, agent, payload):
    # NEG-003：正文首尾的空行不会让部分之间多出空行，消息末尾也不留空行；纯文本回退同样如此
    full = {**payload, "session_id": "s" * 10, "cwd": str(tmp_path / "p")}
    html_body, plain_body = send_once(agent, full, env,
                                      outcomes=[http_error(400, "Bad Request: can't parse entities")])
    for text in (visible(html_body["text"]), plain_body["text"]):
        assert "\n\n\n" not in text and text == text.strip("\n")
        assert text.split("\n\n")[-1].split("\n")[-1].endswith("hi")


def test_session_title_and_error_kind_lines_in_order(env, tmp_path):
    payload = {"hook_event_name": "StopFailure", "error": "rate_limit",
               "error_details": "429 Too Many Requests", "session_id": "e" * 12,
               "cwd": str(tmp_path / "p"), "session_title": "重构登录"}
    _, lines = _send("claude", payload, env)
    # 会话标题用「标题」标签，和会话短 ID 区分开
    assert lines == ["❌ 异常 · p @ box", "", "Agent：Claude", "会话：eeeeeeee", "标题：重构登录",
                     "错误类别：rate_limit", "", "429 Too Many Requests"]


def test_error_without_details_has_no_body(env, tmp_path):
    # 错误类别已单独成行，正文只放错误详情（REQ-003）；没有详情时不出现引用块
    payload = {"hook_event_name": "StopFailure", "error": "rate_limit",
               "session_id": "e" * 12, "cwd": str(tmp_path / "p")}
    body, lines = _send("claude", payload, env)
    assert lines == ["❌ 异常 · p @ box", "", "Agent：Claude", "会话：eeeeeeee", "错误类别：rate_limit"]
    assert "blockquote" not in body["text"] and not body["text"].endswith("\n")


def test_short_id_is_monospace_and_first_line_bold(env, tmp_path):
    body, _ = _send("claude", _stop(tmp_path / "p"), env)
    assert body["text"].startswith("<b>✅ 回合完成 · p @ box</b>\n\n")
    assert "会话：<code>1a2b3c4d</code>" in body["text"]


@pytest.mark.parametrize("agent,payload,first,agent_line", [
    ("claude", {"hook_event_name": "Stop"}, "✅ 回合完成 · p @ box", "Agent：Claude"),
    ("codex", {"hook_event_name": "Stop"}, "✅ 回合结束 · p @ box", "Agent：Codex"),
    ("claude", {"hook_event_name": "Notification", "notification_type": "idle_prompt"},
     "💬 等待输入 · p @ box", "Agent：Claude"),
    ("claude", {"hook_event_name": "Notification", "notification_type": "permission_prompt"},
     "🔐 需要授权 · p @ box", "Agent：Claude"),
    ("codex", {"hook_event_name": "PermissionRequest", "tool_name": "Bash"},
     "🔐 需要授权 · p @ box", "Agent：Codex"),
    ("claude", {"hook_event_name": "StopFailure", "error": "unknown"},
     "❌ 异常 · p @ box", "Agent：Claude"),
])
def test_event_icons_and_display_names(env, tmp_path, agent, payload, first, agent_line):
    # 图标与事件显示名同在第一行；Agent 行在第二部分开头
    _, lines = _send(agent, {**payload, "session_id": "s" * 10, "cwd": str(tmp_path / "p")}, env)
    assert lines[:3] == [first, "", agent_line]


def test_test_notification_layout(env, tmp_path, monkeypatch):
    # 测试命令发出的测试通知同样在第一行显示主机
    import io
    from agent_notify import testcmd
    with_config(env, tmp_path, host_label="mbp")
    channel = telegram_channel()
    monkeypatch.setattr(testcmd, "build_channels", lambda config: [channel])
    assert testcmd.main(env, out=io.StringIO()) == 0
    lines = visible(channel.opener.texts()[0]).split("\n")
    # 测试通知没有 Agent、分支、会话，第一行之后空一行就是正文
    assert lines == ["🔔 测试通知 · agent-notify @ mbp", "", "如果你看到这条消息，说明配置正确。"]


def test_test_notification_without_host_omits_host():
    # 没有主机时第一行省略 @ 和主机
    from agent_notify.testcmd import make_test_notification
    channel = telegram_channel()
    channel.send(make_test_notification())
    assert visible(channel.opener.texts()[0]).split("\n") == [
        "🔔 测试通知 · agent-notify", "", "如果你看到这条消息，说明配置正确。"]


def test_configured_host_label(env, tmp_path):
    # spec #2 SCN-002-A：配置值优先于机器名，首尾空白去掉
    with_config(env, tmp_path, host_label="  home-linux  ")
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[0] == "✅ 回合完成 · p @ home-linux"


@pytest.mark.parametrize("label", [None, "", "   "])
def test_blank_host_label_falls_back_to_short_hostname(env, tmp_path, hostname, label):
    # spec #2 SCN-002-B
    hostname["value"] = "chenjinfans-MacBook-Pro.local"
    data = {} if label is None else {"host_label": label}
    with_config(env, tmp_path, **data)
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[0] == "✅ 回合完成 · p @ chenjinfans-MacBook-Pro"


def test_long_host_truncated_to_32_chars(env, tmp_path, hostname):
    hostname["value"] = "a" * 40 + ".example.com"
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[0] == "✅ 回合完成 · p @ " + "a" * 32 + "…"


def test_host_without_project_keeps_at_sign(env, tmp_path):
    # cwd 为根目录时没有项目名；主机前保留 @，不会被误认成项目
    _, lines = _send("claude", _stop("/"), env)
    assert lines[0] == "✅ 回合完成 · @ box"


def test_host_omitted_when_unavailable(env, tmp_path, hostname):
    hostname["value"] = ""
    _, lines = _send("claude", _stop(tmp_path / "p"), env)
    assert lines[0] == "✅ 回合完成 · p"


def test_special_characters_shown_verbatim(env, tmp_path):
    # spec #19 SCN-003-H（spec #2 SCN-006-A）：所有字段值先转义，解析后的可见文本与原文一致
    with_config(env, tmp_path, host_label="h<1>&")
    repo = _repo(tmp_path, "a&b", "fix/<x>")
    payload = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb2",
               "cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": 'echo "<a>" && ls'},
               "session_title": "<t>&"}
    body, lines = _send("codex", payload, env)
    assert body["parse_mode"] == "HTML"
    assert lines == ["🔐 需要授权 · a&b @ h<1>&", "", "Agent：Codex", "分支：fix/<x>",
                     "会话：bbbbbbbb", "标题：<t>&", "", 'Bash: echo "<a>" && ls']
    assert "&lt;a&gt;" in body["text"] and "&amp;&amp;" in body["text"]
