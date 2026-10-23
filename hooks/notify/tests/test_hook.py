from __future__ import annotations

from conftest import process

from agent_notify.channels import render_plain


def _title(notification):
    """消息前两行：标题行与 Agent · 主机 · 分支 · 会话短 ID 行。"""
    return render_plain(notification).splitlines()[:2]


def test_claude_stop_sends_turn_complete(env, fake, tmp_path):
    payload = {"hook_event_name": "Stop", "session_id": "abcdef1234567890",
               "cwd": str(tmp_path / "proj"), "last_assistant_message": "完成了"}
    process("claude", payload, env, channels=[fake])
    assert len(fake.sent) == 1
    n = fake.sent[0]
    assert n.event_type == "回合完成"
    assert _title(n) == ["✅ 回合完成 · proj", f"Claude · {n.host} · abcdef12"]


def test_codex_stop_sends_single_turn_end_waiting(env, fake, tmp_path):
    payload = {"hook_event_name": "Stop", "session_id": "c0dex999zzz",
               "cwd": str(tmp_path / "svc"), "last_assistant_message": "done",
               "turn_id": "t1"}
    process("codex", payload, env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["回合结束，等待输入"]
    assert _title(fake.sent[0])[0] == "✅ 回合结束 · svc"
    assert fake.sent[0].session_id == "c0dex999"


def test_claude_idle_prompt_sends_waiting_input(env, fake, tmp_path):
    payload = {"hook_event_name": "Notification", "notification_type": "idle_prompt",
               "session_id": "s1234567xx", "cwd": str(tmp_path / "p"),
               "message": "Claude is waiting for your input"}
    process("claude", payload, env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["等待输入"]


def test_claude_mcp_elicitation_sends_waiting_input(env, fake, tmp_path):
    # SCN-008-A：MCP 服务器回合中途请求输入，两种对话框各发一条「等待输入」，摘要为提示文字
    for kind, message in [("elicitation_dialog", "请选择要部署的环境"),
                          ("elicitation_url_dialog", "请在浏览器中完成登录")]:
        payload = {"hook_event_name": "Notification", "notification_type": kind,
                   "session_id": "m1234567xx", "cwd": str(tmp_path / "p"), "message": message}
        process("claude", payload, env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["等待输入", "等待输入"]
    assert [n.body for n in fake.sent] == ["请选择要部署的环境", "请在浏览器中完成登录"]


def test_claude_unrelated_notification_types_are_ignored(env, fake, tmp_path):
    # SCN-008-B：与等待用户无关的 Notification 类型不发通知
    base = {"hook_event_name": "Notification", "session_id": "n1234567xx",
            "cwd": str(tmp_path / "p"), "message": "x"}
    for kind in ["auth_success", "elicitation_complete", "elicitation_response",
                 "agent_needs_input", "agent_completed", "quota_warning", "plugin_notification"]:
        process("claude", {**base, "notification_type": kind}, env, channels=[fake])
    assert fake.sent == []


def test_permission_requests_from_both_agents(env, fake, tmp_path):
    claude = {"hook_event_name": "Notification", "notification_type": "permission_prompt",
              "session_id": "aaaaaaaa1", "cwd": str(tmp_path / "p"),
              "message": "Claude needs your permission to use Bash"}
    codex = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb2",
             "cwd": str(tmp_path / "p"), "tool_name": "Bash",
             "tool_input": {"command": "rm -rf build"}}
    process("claude", claude, env, channels=[fake])
    process("codex", codex, env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["需要授权", "需要授权"]
    assert "Bash" in fake.sent[0].body
    assert "rm -rf build" in fake.sent[1].body


def test_claude_stop_failure_sends_error_with_kind(env, fake, tmp_path):
    payload = {"hook_event_name": "StopFailure", "error": "rate_limit", "error_details": "429 Too Many Requests",
               "session_id": "e" * 12, "cwd": str(tmp_path / "p")}
    process("claude", payload, env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["异常"]
    assert fake.sent[0].error_kind == "rate_limit"
    assert "429" in fake.sent[0].body


def test_unsupported_and_subagent_events_are_ignored(env, fake, tmp_path):
    base = {"session_id": "x" * 10, "cwd": str(tmp_path)}
    process("claude", {**base, "hook_event_name": "SubagentStop"}, env, channels=[fake])
    process("claude", {**base, "hook_event_name": "Notification",
                       "notification_type": "auth_success"}, env, channels=[fake])
    process("codex", {**base, "hook_event_name": "SubagentStop"}, env, channels=[fake])
    process("codex", {**base, "hook_event_name": "PreToolUse"}, env, channels=[fake])
    process("claude", {**base, "hook_event_name": "Stop", "agent_id": "sub1"}, env, channels=[fake])
    assert fake.sent == []


def _git_repo(path, branch):
    import subprocess
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    return path


def test_project_is_git_root_and_branch_shown(env, fake, tmp_path):
    repo = _git_repo(tmp_path / "myrepo", "feat/x")
    sub = repo / "src" / "pkg"
    sub.mkdir(parents=True)
    payload = {"hook_event_name": "Stop", "session_id": "1234567890ab",
               "cwd": str(sub), "session_title": "重构登录"}
    process("claude", payload, env, channels=[fake])
    n = fake.sent[0]
    assert (n.project, n.session_id) == ("myrepo", "12345678")
    assert n.branch == "feat/x"
    assert n.session_title == "重构登录"


def test_non_git_dir_uses_cwd_name_without_branch(env, fake, tmp_path):
    d = tmp_path / "plain"
    d.mkdir()
    process("codex", {"hook_event_name": "Stop", "session_id": "s" * 9, "cwd": str(d)},
            env, channels=[fake])
    assert fake.sent[0].project == "plain"
    assert fake.sent[0].branch == ""


def _stop(tmp_path, msg):
    return {"hook_event_name": "Stop", "session_id": "abcdefgh99",
            "cwd": str(tmp_path), "last_assistant_message": msg}


def test_summary_truncated_to_1000_chars_without_breaking_multibyte(env, fake, tmp_path):
    process("claude", _stop(tmp_path, "汉" * 1500), env, channels=[fake])
    assert fake.sent[0].body == "汉" * 1000 + "…"


def test_short_and_missing_summary(env, fake, tmp_path):
    process("claude", _stop(tmp_path, "ok <b>*_`"), env, channels=[fake])
    process("claude", _stop(tmp_path, None), env, channels=[fake])
    assert fake.sent[0].body == "ok <b>*_`"
    assert fake.sent[1].body == ""


def test_render_text_contains_all_parts(env, fake, tmp_path):
    process("claude", _stop(tmp_path, "已完成重构"), env, channels=[fake])
    text = render_plain(fake.sent[0])
    assert text.splitlines()[0] == "✅ 回合完成 · " + tmp_path.name
    assert text.splitlines()[1].endswith(" · abcdefgh")
    assert "回合完成" in text
    assert "已完成重构" in text


def test_privacy_mode_sends_only_title_and_event(env, fake, tmp_path):
    env["AGENT_NOTIFY_PRIVACY"] = "1"
    process("claude", _stop(tmp_path, "secret stuff"), env, channels=[fake])
    text = render_plain(fake.sent[0])
    assert "secret" not in text
    assert "回合完成" in text


def test_event_toggle_disables_type(env, fake, tmp_path):
    import json
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"events": {"turn_complete": False}}))
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    process("claude", _stop(tmp_path, "x"), env, channels=[fake])
    process("codex", {"hook_event_name": "Stop", "session_id": "c" * 9, "cwd": str(tmp_path)},
            env, channels=[fake])
    assert [n.event_type for n in fake.sent] == ["回合结束，等待输入"]


def test_env_overrides_config_file(tmp_path):
    import json
    from agent_notify.config import load_config
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"telegram": {"token": "file-token", "chat_id": "1"}}))
    c = load_config({"AGENT_NOTIFY_CONFIG": str(cfg), "AGENT_NOTIFY_TELEGRAM_CHAT_ID": "99"})
    assert (c.telegram_token, c.telegram_chat_id) == ("file-token", "99")


def test_channel_failure_is_logged_without_token_and_never_raises(env, tmp_path):
    from conftest import FakeChannel, TOKEN
    broken = FakeChannel(error=RuntimeError(f"HTTP 401 for bot{TOKEN}"))
    ok = FakeChannel()
    process("claude", _stop(tmp_path, "x"), env, channels=[broken, ok])
    assert len(ok.sent) == 1
    log = (tmp_path / "notify.log").read_text()
    assert "HTTP 401" in log and "abcdefgh" in log and "回合完成" in log
    assert TOKEN not in log


def test_missing_credentials_logs_and_sends_nothing(tmp_path):
    from agent_notify.hook import run
    env = {"AGENT_NOTIFY_CONFIG": str(tmp_path / "none.json"),
           "AGENT_NOTIFY_LOG": str(tmp_path / "n.log"), "HOME": str(tmp_path)}
    assert run("claude", '{"hook_event_name": "Stop", "session_id": "q"}', env, spawn=False) == 0
    # 缺少凭据属于跳过原因，只在 debug 级别记录（REQ-010）；debug 情况见 test_logging.py
    assert not (tmp_path / "n.log").exists()


def test_invalid_payload_never_raises(env):
    from agent_notify.hook import run
    assert run("claude", "not json{", env, spawn=False) == 0
    assert run("unknown-agent", "{}", env, spawn=False) == 0


def test_notify_test_command_reports_failure(env, tmp_path):
    import io
    from agent_notify import testcmd
    env.pop("AGENT_NOTIFY_TELEGRAM_TOKEN")
    out = io.StringIO()
    assert testcmd.main(env, out=out) == 1
    assert "缺少 Telegram token" in out.getvalue()


def test_hook_script_exits_zero_fast_without_stdout(env, tmp_path):
    import subprocess, sys, time, json
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "bin" / "hook.py"
    home = tmp_path / "home"
    config_dir = home / ".config" / "agent-notify"
    state_dir = home / ".local" / "state" / "agent-notify"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(json.dumps({"telegram": {"token": "x", "chat_id": "42"}}))
    workdir = tmp_path / "proj"
    workdir.mkdir()
    payload = json.dumps(_stop(workdir, "x"))
    # 使用默认配置和日志路径；指向不可达地址，确保子进程不会真的发出消息
    env = {k: v for k, v in env.items() if k not in ("AGENT_NOTIFY_CONFIG", "AGENT_NOTIFY_LOG")}
    env = {**env, "HOME": str(home), "AGENT_NOTIFY_TELEGRAM_TOKEN": "x",
           "https_proxy": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9"}
    start = time.monotonic()
    r = subprocess.run([sys.executable, str(script), "claude"], input=payload,
                       capture_output=True, text=True, env=env, timeout=10)
    assert r.returncode == 0 and r.stdout == ""
    assert time.monotonic() - start < 2

    # 等后台发送子进程失败并写完日志（NEG-002）
    log = state_dir / "notify.log"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and "result=fail" not in (log.read_text() if log.exists() else ""):
        time.sleep(0.05)
    assert "result=fail" in log.read_text()
    assert sorted(p.name for p in config_dir.rglob("*")) == ["config.json"]
    assert sorted(p.name for p in state_dir.rglob("*")) == ["notify.log"]


def test_codex_merged_event_off_only_when_both_toggles_off(env, fake, tmp_path):
    import json
    cfg = tmp_path / "cfg.json"
    codex = {"hook_event_name": "Stop", "session_id": "c" * 9, "cwd": str(tmp_path)}
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    cfg.write_text(json.dumps({"events": {"turn_complete": False, "waiting_input": False}}))
    process("codex", codex, env, channels=[fake])
    assert fake.sent == []
