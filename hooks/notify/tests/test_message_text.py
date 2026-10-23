"""锁定 Telegram 实际收到的请求体 text：经 process 走完整链路，渠道用真实 TelegramChannel。

期望值是 1.4.3 发出的原文，手写字面量，重构不得改变。
"""
from __future__ import annotations

import json
import subprocess

from conftest import TOKEN, process, telegram_channel


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


def _texts(agent, payload, env):
    channel = telegram_channel()
    process(agent, payload, env, channels=[channel])
    return channel.opener.texts()


def test_turn_complete_text(env, tmp_path):
    repo = _repo(tmp_path)
    (repo / "src").mkdir()
    assert _texts("claude", _claude_stop(repo / "src"), env) == [
        "[Claude] myrepo · 12345678\n事件：回合完成\n分支：feat/x\n会话：重构登录\n\n已完成重构"]


def test_codex_turn_end_text(env, tmp_path):
    payload = {"hook_event_name": "Stop", "session_id": "c0dex999zzz",
               "cwd": str(tmp_path / "svc"), "last_assistant_message": "done", "turn_id": "t1"}
    assert _texts("codex", payload, env) == ["[Codex] svc · c0dex999\n事件：回合结束，等待输入\n\ndone"]


def test_waiting_input_text(env, tmp_path):
    payload = {"hook_event_name": "Notification", "notification_type": "idle_prompt",
               "session_id": "s1234567xx", "cwd": str(tmp_path / "p"),
               "message": "Claude is waiting for your input"}
    assert _texts("claude", payload, env) == [
        "[Claude] p · s1234567\n事件：等待输入\n\nClaude is waiting for your input"]


def test_permission_texts(env, tmp_path):
    cwd = str(tmp_path / "p")
    assert _texts("claude", {**CLAUDE_PERMISSION, "cwd": cwd}, env) == [
        "[Claude] p · aaaaaaaa\n事件：需要授权\n\nClaude needs your permission to use Bash"]
    assert _texts("codex", {**CODEX_PERMISSION, "cwd": cwd}, env) == [
        "[Codex] p · bbbbbbbb\n事件：需要授权\n\nBash: rm -rf build"]


def test_error_text(env, tmp_path):
    assert _texts("claude", {**CLAUDE_ERROR, "cwd": str(tmp_path / "p")}, env) == [
        "[Claude] p · eeeeeeee\n事件：异常\n错误类别：rate_limit\n\nrate_limit · 429 Too Many Requests"]


def test_missing_session_id_and_long_summary_text(env, tmp_path):
    payload = {"hook_event_name": "Stop", "cwd": str(tmp_path / "p"),
               "last_assistant_message": "汉" * 1000}
    assert _texts("claude", payload, env) == ["[Claude] p · \n事件：回合完成\n\n" + "汉" * 300 + "…"]


def test_privacy_mode_texts(env, tmp_path):
    env["AGENT_NOTIFY_PRIVACY"] = "1"
    repo = _repo(tmp_path)
    cwd = str(tmp_path / "p")
    assert _texts("claude", _claude_stop(repo), env) == ["[Claude] myrepo · 12345678\n事件：回合完成"]
    assert _texts("codex", {**CODEX_PERMISSION, "cwd": cwd}, env) == ["[Codex] p · bbbbbbbb\n事件：需要授权"]
    assert _texts("claude", {**CLAUDE_ERROR, "cwd": cwd}, env) == ["[Claude] p · eeeeeeee\n事件：异常"]


def test_test_notification_text():
    from agent_notify.testcmd import make_test_notification
    channel = telegram_channel()
    channel.send(make_test_notification())
    assert channel.opener.texts() == ["[agent-notify] 测试通知\n事件：测试通知\n\n如果你看到这条消息，说明配置正确。"]


def test_request_records_method_body_and_timeout(env, tmp_path):
    channel = telegram_channel()
    process("claude", _claude_stop(tmp_path / "p"), env, channels=[channel])
    [request] = channel.opener.requests
    assert request.method == "sendMessage"
    assert set(request.body) == {"chat_id", "text"} and request.body["chat_id"] == "42"
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
    assert channel.opener.texts() == ["[Codex] p · bbbbbbbb\n事件：需要授权"]
