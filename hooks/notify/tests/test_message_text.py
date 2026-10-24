"""锁定 Telegram 实际收到的请求体 text：经 process 走完整链路，渠道用真实 TelegramChannel。

期望值是「图标 项目 @ 主机」布局的手写字面量（取代 1.4.3 原文与 spec #2 REQ-001 原定布局）；截断长度与隐私模式按 #6
（REQ-003、REQ-004）更新。多数测试比较 HTML 解析后的可见文本；完整 HTML 只在少数测试里锁定。
"""
from __future__ import annotations

import json
import subprocess

import pytest

from conftest import TOKEN, process, telegram_channel, visible


pytestmark = pytest.mark.usefixtures("hostname")


def _repo(tmp_path, name="myrepo", branch="feat/x"):
    path = tmp_path / name
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    return path


def _claude_stop(cwd, **extra):
    return {"hook_event_name": "Stop", "session_id": "1234567890ab", "cwd": str(cwd),
            "session_title": "重构登录", "last_assistant_message": "已完成重构", **extra}


CLAUDE_PERMISSION = {"hook_event_name": "Notification", "notification_type": "permission_prompt",
                     "session_id": "aaaaaaaa1", "message": "Claude needs your permission to use Bash"}
CODEX_PERMISSION = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb2",
                    "tool_name": "Bash", "tool_input": {"command": "rm -rf build"}}
CLAUDE_ERROR = {"hook_event_name": "StopFailure", "error": "rate_limit",
                "error_details": "429 Too Many Requests", "session_id": "e" * 12}


def _html(agent, payload, env):
    channel = telegram_channel()
    process(agent, payload, env, channels=[channel])
    return channel.opener.texts()


def _texts(agent, payload, env):
    """可见文本。"""
    return [visible(t) for t in _html(agent, payload, env)]


def test_turn_complete_text(env, tmp_path):
    repo = _repo(tmp_path)
    (repo / "src").mkdir()
    assert _html("claude", _claude_stop(repo / "src"), env) == [
        "<b>✅ myrepo @ box</b>\n回合完成 · Claude · feat/x · <code>12345678</code>\n"
        "会话：重构登录\n<blockquote expandable>已完成重构</blockquote>"]


def test_codex_turn_end_text(env, tmp_path):
    payload = {"hook_event_name": "Stop", "session_id": "c0dex999zzz",
               "cwd": str(tmp_path / "svc"), "last_assistant_message": "done", "turn_id": "t1"}
    assert _texts("codex", payload, env) == ["✅ svc @ box\n回合结束 · Codex · c0dex999\ndone"]


def test_waiting_input_text(env, tmp_path):
    payload = {"hook_event_name": "Notification", "notification_type": "idle_prompt",
               "session_id": "s1234567xx", "cwd": str(tmp_path / "p"),
               "message": "Claude is waiting for your input"}
    assert _texts("claude", payload, env) == [
        "💬 p @ box\n等待输入 · Claude · s1234567\nClaude is waiting for your input"]


def test_permission_texts(env, tmp_path):
    cwd = str(tmp_path / "p")
    assert _texts("claude", {**CLAUDE_PERMISSION, "cwd": cwd}, env) == [
        "🔐 p @ box\n需要授权 · Claude · aaaaaaaa\nClaude needs your permission to use Bash"]
    assert _texts("codex", {**CODEX_PERMISSION, "cwd": cwd}, env) == [
        "🔐 p @ box\n需要授权 · Codex · bbbbbbbb\nBash: rm -rf build"]


def test_error_text(env, tmp_path):
    assert _texts("claude", {**CLAUDE_ERROR, "cwd": str(tmp_path / "p")}, env) == [
        "❌ p @ box\n异常 · Claude · eeeeeeee\n错误类别：rate_limit\n429 Too Many Requests"]


def test_missing_session_id_and_long_summary_text(env, tmp_path):
    payload = {"hook_event_name": "Stop", "cwd": str(tmp_path / "p"),
               "last_assistant_message": "汉" * 1500}
    assert _texts("claude", payload, env) == ["✅ p @ box\n回合完成 · Claude\n" + "汉" * 1000 + "…"]


def test_privacy_mode_texts(env, tmp_path):
    env["AGENT_NOTIFY_PRIVACY"] = "1"
    repo = _repo(tmp_path)
    cwd = str(tmp_path / "p")
    # 隐私模式只关正文和会话标题，分支和错误类别照常发送（REQ-004）
    assert _texts("claude", _claude_stop(repo), env) == [
        "✅ myrepo @ box\n回合完成 · Claude · feat/x · 12345678"]
    assert _texts("codex", {**CODEX_PERMISSION, "cwd": cwd}, env) == ["🔐 p @ box\n需要授权 · Codex · bbbbbbbb"]
    assert _texts("claude", {**CLAUDE_ERROR, "cwd": cwd}, env) == [
        "❌ p @ box\n异常 · Claude · eeeeeeee\n错误类别：rate_limit"]


def test_test_notification_text():
    from agent_notify.testcmd import make_test_notification
    channel = telegram_channel()
    channel.send(make_test_notification("mbp"))
    assert channel.opener.texts() == [
        "<b>🔔 agent-notify @ mbp</b>\n测试通知\n"
        "<blockquote expandable>如果你看到这条消息，说明配置正确。</blockquote>"]


def test_request_records_method_body_and_timeout(env, tmp_path):
    channel = telegram_channel()
    process("claude", _claude_stop(tmp_path / "p"), env, channels=[channel])
    [request] = channel.opener.requests
    assert request.method == "sendMessage"
    assert set(request.body) == {"chat_id", "text", "parse_mode"}
    assert (request.body["chat_id"], request.body["parse_mode"]) == ("42", "HTML")
    assert 0 < request.timeout <= 10


def test_143_config_file_still_works(tmp_path):
    from agent_notify.channels import build_channels
    from agent_notify.config import load_config
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"telegram": {"token": TOKEN, "chat_id": "7"}, "privacy": True,
                               "events": {"error": False}}))
    env = {"AGENT_NOTIFY_CONFIG": str(cfg), "AGENT_NOTIFY_LOG": str(tmp_path / "n.log")}
    [built] = build_channels(load_config(env))
    assert (built.token, built.chat_id) == (TOKEN, "7")
    channel = telegram_channel(token=built.token, chat_id=built.chat_id)
    cwd = str(tmp_path / "p")
    process("claude", {**CLAUDE_ERROR, "cwd": cwd}, env, channels=[channel])
    process("codex", {**CODEX_PERMISSION, "cwd": cwd}, env, channels=[channel])
    assert [visible(t) for t in channel.opener.texts()] == ["🔐 p @ box\n需要授权 · Codex · bbbbbbbb"]
