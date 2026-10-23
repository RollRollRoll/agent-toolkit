"""诊断命令 notify-doctor（REQ-009、NEG-001、NEG-004）：经 main(env, out, opener) 观察输出与退出码。"""
from __future__ import annotations

import io
import json
import os

import pytest
from conftest import TOKEN, RecordingOpener

from agent_notify import doctor

GET_ME_OK = json.dumps({"ok": True, "result": {"id": 1, "is_bot": True, "username": "my_notify_bot"}}).encode()
GET_CHAT_OK = json.dumps({"ok": True, "result": {"id": 42, "type": "private", "first_name": "kg"}}).encode()


@pytest.fixture
def cfg(tmp_path):
    """凭据写在配置文件里、权限 600 的典型环境。"""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"telegram": {"token": TOKEN, "chat_id": "42"}, "host_label": "devbox"}))
    os.chmod(path, 0o600)
    return path


@pytest.fixture
def denv(tmp_path, cfg):
    return {"AGENT_NOTIFY_CONFIG": str(cfg), "AGENT_NOTIFY_LOG": str(tmp_path / "state" / "notify.log")}


def run(env, outcomes=(GET_ME_OK, GET_CHAT_OK), argv=()):
    out = io.StringIO()
    opener = RecordingOpener(outcomes)
    code = doctor.main(env, out=out, opener=opener, argv=argv)
    return code, out.getvalue(), opener


def line(text, keyword):
    """输出中第一条包含 keyword 的检查行。"""
    return next(l for l in text.splitlines() if keyword in l)


def test_all_good_is_all_check_marks_and_exit_zero(denv, cfg):
    code, text, opener = run(denv)
    assert code == 0
    assert "⚠️" not in text and "❌" not in text
    assert str(cfg) in line(text, "配置文件")
    assert line(text, "getMe").startswith("✅") and "@my_notify_bot" in text
    assert line(text, "getChat").startswith("✅")
    # NEG-001：token 只露出前 4 位和后 4 位
    assert TOKEN not in text
    assert "1234…OKEN" in line(text, "token")
    # NEG-004：只调用 getMe 和 getChat
    assert [r.method for r in opener.requests] == ["getMe", "getChat"]
    assert opener.requests[1].body == {"chat_id": "42"}


def hint(text, keyword):
    """keyword 所在检查行之后的修复建议行。"""
    lines = text.splitlines()
    i = next(i for i, l in enumerate(lines) if keyword in l)
    assert lines[i + 1].lstrip().startswith("→"), lines[i + 1]
    return lines[i + 1]


def _http(code, description):
    import urllib.error
    body = json.dumps({"ok": False, "error_code": code, "description": description}).encode()
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(body))


def test_rejected_token_fails_get_me_and_skips_get_chat(denv):
    code, text, opener = run(denv, outcomes=[_http(401, "Unauthorized")])
    assert code == 1
    assert line(text, "getMe").startswith("❌")
    assert "notify-setup" in hint(text, "getMe")
    assert line(text, "getChat").startswith("⏭️")
    assert [r.method for r in opener.requests] == ["getMe"]
    assert TOKEN not in text


def test_network_error_fails_get_me_with_network_hint(denv):
    import urllib.error
    code, text, opener = run(denv, outcomes=[urllib.error.URLError("connection refused")])
    assert code == 1
    assert line(text, "getMe").startswith("❌")
    assert "网络或代理" in hint(text, "getMe")
    # 单次调用、超时取 request_timeout，保证命令在 request_timeout + 5 秒内结束
    assert [(r.method, r.timeout) for r in opener.requests] == [("getMe", 10.0)]


def test_unreachable_chat_fails_get_chat_with_hint(denv):
    code, text, opener = run(denv, outcomes=[GET_ME_OK, _http(400, "Bad Request: chat not found")])
    assert code == 1
    assert line(text, "getMe").startswith("✅")
    assert line(text, "getChat").startswith("❌")
    assert "先给 Bot 发一条消息" in hint(text, "getChat")
    assert "chat_id 填写错误" in hint(text, "getChat")
    assert [r.method for r in opener.requests] == ["getMe", "getChat"]


def test_config_wider_than_600_is_warning_not_failure(denv, cfg):
    os.chmod(cfg, 0o644)
    code, text, _ = run(denv)
    assert code == 0
    assert line(text, "权限").startswith("⚠️") and "644" in line(text, "权限")
    assert "chmod 600" in hint(text, "权限")


def test_broken_config_fails_and_reports_env_credentials(denv, cfg):
    cfg.write_text("{not json")
    env = {**denv, "AGENT_NOTIFY_TELEGRAM_TOKEN": TOKEN, "AGENT_NOTIFY_TELEGRAM_CHAT_ID": "42"}
    code, text, _ = run(env)
    assert code == 1
    assert line(text, "配置文件").startswith("❌") and "JSON" in line(text, "配置文件")
    assert "notify-setup" in hint(text, "配置文件")
    assert "环境变量 AGENT_NOTIFY_TELEGRAM_TOKEN" in line(text, "token")
    assert "环境变量 AGENT_NOTIFY_TELEGRAM_CHAT_ID" in line(text, "chat_id")


def test_missing_credentials_fail_and_skip_online_checks(tmp_path):
    env = {"AGENT_NOTIFY_CONFIG": str(tmp_path / "missing.json"),
           "AGENT_NOTIFY_LOG": str(tmp_path / "notify.log")}
    code, text, opener = run(env)
    assert code == 1
    assert line(text, "token").startswith("❌") and "notify-setup" in hint(text, "token")
    assert line(text, "chat_id").startswith("❌")
    assert line(text, "getMe").startswith("⏭️") and line(text, "getChat").startswith("⏭️")
    assert opener.requests == []


def test_shows_effective_settings(denv, cfg):
    cfg.write_text(json.dumps({
        "telegram": {"token": TOKEN, "chat_id": "42"}, "host_label": " devbox ",
        "events": {"permission": False}, "include_tool_detail": False,
        "summary_max_chars": 99999, "request_timeout": 5, "log_level": "debug"}))
    _, text, _ = run(denv, argv=["--offline"])
    assert "turn_complete=开" in line(text, "事件开关") and "permission=关" in line(text, "事件开关")
    assert "devbox（来自配置 host_label）" in line(text, "主机")
    assert "include_summary=开" in text and "include_tool_detail=关" in text
    assert "隐私模式=关" in text
    assert "summary_max_chars=3500" in text
    assert "request_timeout=5" in text and "log_level=debug" in text


def test_host_falls_back_to_machine_name(denv, cfg, monkeypatch):
    import socket
    cfg.write_text(json.dumps({"telegram": {"token": TOKEN, "chat_id": "42"}}))
    monkeypatch.setattr(socket, "gethostname", lambda: "kg-mbp.local")
    _, text, _ = run(denv, argv=["--offline"])
    assert "kg-mbp（来自机器名）" in line(text, "主机")


def test_no_log_yet_shows_writable_and_no_failure(denv, tmp_path):
    _, text, _ = run(denv, argv=["--offline"])
    assert line(text, "Python").startswith("✅")
    assert line(text, "日志路径").startswith("✅") and str(tmp_path / "state" / "notify.log") in text
    assert line(text, "最近一次发送失败").endswith("无")
    # 只读：诊断不创建日志目录
    assert not (tmp_path / "state").exists()


def test_log_with_failures_shows_latest_failure_time_and_kind(denv, tmp_path):
    log = tmp_path / "state" / "notify.log"
    log.parent.mkdir()
    # 成功行早于最近一次失败：未恢复，显示 ⚠️
    log.write_text(
        "2026-10-19T08:00:00 level=info agent=claude channel=telegram result=ok duration_ms=3\n"
        "2026-10-20T09:00:00 level=error agent=claude channel=telegram result=fail "
        "duration_ms=5 error=network detail=down\n"
        "2026-10-21T10:30:00 level=error agent=codex channel=telegram result=fail "
        'duration_ms=8 error=api status=401 detail="Telegram HTTP 401: Unauthorized"\n')
    code, text, _ = run(denv, argv=["--offline"])
    assert code == 0
    last = line(text, "最近一次发送失败")
    assert last.startswith("⚠️") and "2026-10-21T10:30:00" in last and "api" in last and "401" in last
    hint(text, "最近一次发送失败")


@pytest.mark.parametrize("result", ["ok", "fallback"])
def test_failure_followed_by_success_is_shown_as_recovered(denv, tmp_path, result):
    log = tmp_path / "state" / "notify.log"
    log.parent.mkdir()
    log.write_text(
        "2026-10-21T10:30:00 level=error agent=codex channel=telegram result=fail "
        "duration_ms=8 error=network detail=down\n"
        f"2026-10-22T11:00:00 level=info agent=claude channel=telegram result={result} "
        "duration_ms=3\n")
    _, text, _ = run(denv, argv=["--offline"])
    last = line(text, "最近一次发送失败")
    assert last == "✅ 最近一次发送失败：2026-10-21T10:30:00 error=network（已恢复）"
    assert "→" not in text.splitlines()[text.splitlines().index(last) + 1]


def test_failure_without_later_success_line_is_warning(denv, tmp_path):
    # log_level: error 时没有成功行，无法判断是否恢复，按 ⚠️ 处理
    log = tmp_path / "state" / "notify.log"
    log.parent.mkdir()
    log.write_text("2026-10-21T10:30:00 level=error agent=codex channel=telegram result=fail "
                   "duration_ms=8 error=network\n")
    _, text, _ = run(denv, argv=["--offline"])
    assert line(text, "最近一次发送失败").startswith("⚠️")
    hint(text, "最近一次发送失败")


def test_unreadable_log_is_warning_not_none(denv, tmp_path):
    # spec #2 §3.4：日志读取失败时该项为 ⚠️
    log = tmp_path / "state" / "notify.log"
    log.parent.mkdir()
    log.write_text("2026-10-21T10:30:00 level=info result=ok duration_ms=3\n")
    os.chmod(log, 0o000)
    try:
        _, text, _ = run(denv, argv=["--offline"])
    finally:
        os.chmod(log, 0o600)
    last = line(text, "最近一次发送失败")
    assert last.startswith("⚠️") and not last.endswith("无")
    hint(text, "最近一次发送失败")


def test_unwritable_log_dir_is_failure(denv, tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    os.chmod(state, 0o500)
    try:
        code, text, _ = run(denv, argv=["--offline"])
    finally:
        os.chmod(state, 0o700)
    assert code == 1
    assert line(text, "日志路径").startswith("❌")
    hint(text, "日志路径")


def test_fixed_reminders_about_hook_registration(denv):
    _, text, _ = run(denv, argv=["--offline"])
    assert "/hooks" in text and "Codex" in text
    assert "hook 注册状态需在 Agent 内确认" in text


def test_skill_registered_and_both_manifests_are_valid_json():
    from pathlib import Path
    repo = Path(__file__).resolve().parents[3]
    claude = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    json.loads((repo / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert "./skills/support/notify-doctor" in claude["skills"]
    assert (repo / "skills" / "support" / "notify-doctor" / "SKILL.md").is_file()


def test_script_offline_runs_without_network(denv):
    import subprocess
    import sys
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "bin" / "notify-doctor.py"
    # 代理指向不可达地址：若有请求发出会失败，--offline 下应完全不受影响
    env = {**denv, "PATH": os.environ.get("PATH", ""), "HTTPS_PROXY": "http://127.0.0.1:9"}
    r = subprocess.run([sys.executable, str(script), "--offline"], capture_output=True,
                       text=True, env=env, timeout=10)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "getMe" not in r.stdout and TOKEN not in r.stdout


def test_offline_makes_no_requests_and_has_no_online_items(denv):
    code, text, opener = run(denv, argv=["--offline"])
    assert code == 0
    assert opener.requests == []
    assert "getMe" not in text and "getChat" not in text
    assert str(denv["AGENT_NOTIFY_CONFIG"]) in text
