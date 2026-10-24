"""摘要长度与摘要 / 命令预览开关（spec REQ-003、REQ-004、REQ-013）。"""
from __future__ import annotations

import subprocess

import pytest
from conftest import TOKEN, process, telegram_channel, visible, with_config

pytestmark = pytest.mark.usefixtures("hostname")


def _visible(channel):
    return [visible(t) for t in channel.opener.texts()]

CODEX_PERMISSION = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb2",
                    "tool_name": "Bash", "tool_input": {"command": "rm -rf build"}}


def _stop(cwd, msg, **extra):
    return {"hook_event_name": "Stop", "session_id": "abcdefgh99", "cwd": str(cwd),
            "last_assistant_message": msg, **extra}


def test_default_summary_limit_is_1000_chars(env, fake, tmp_path):
    # SCN-003-A
    msg = "".join(chr(ord("a") + i % 26) for i in range(1500))
    process("claude", _stop(tmp_path, msg), env, channels=[fake])
    assert fake.sent[0].body == msg[:1000] + "…"


def test_long_chinese_summary_keeps_whole_characters(env, telegram, tmp_path):
    # SCN-003-A：含中文的长摘要按字符截断，请求里的 text 不含被切坏的字符
    msg = "中文摘要🙂" * 300
    process("claude", _stop(tmp_path, msg), env, channels=[telegram])
    [text] = telegram.opener.texts()
    assert visible(text).endswith("\n" + msg[:1000] + "…")
    text.encode("utf-8")  # 切坏代理对或多字节字符时这里会抛错


@pytest.mark.parametrize("value, expected", [(200, 200), ("abc", 1000), (0, 1000), (9999, 3500)])
def test_summary_max_chars_custom_and_invalid_values(env, fake, tmp_path, value, expected):
    # SCN-003-B：非法值按 1000、超过上限按 3500，通知照常发送
    with_config(env, tmp_path, **{"summary_max_chars": value})
    process("claude", _stop(tmp_path, "x" * 5000), env, channels=[fake])
    assert fake.sent[0].body == "x" * expected + "…"


def test_project_branch_and_session_title_truncated_to_64_chars(env, fake, tmp_path):
    repo = tmp_path / ("p" * 70)
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "b" * 70, str(repo)], check=True)
    process("claude", _stop(repo, "ok", session_title="标" * 70), env, channels=[fake])
    n = fake.sent[0]
    assert (n.project, n.branch, n.session_title) == ("p" * 64 + "…", "b" * 64 + "…", "标" * 64 + "…")


def test_summary_off_keeps_command_preview(env, telegram, tmp_path):
    # SCN-004-A：只关摘要
    with_config(env, tmp_path, **{"include_summary": False})
    cwd = str(tmp_path / "p")
    process("claude", _stop(cwd, "回合摘要", session_title="标题"), env, channels=[telegram])
    process("codex", {**CODEX_PERMISSION, "cwd": cwd, "session_title": "标题"}, env, channels=[telegram])
    assert _visible(telegram) == ["✅ 回合完成 · p @ box\n\nAgent：Claude\n会话：abcdefgh",
                                  "🔐 需要授权 · p @ box\n\nAgent：Codex\n会话：bbbbbbbb\n\nBash: rm -rf build"]


def test_summary_off_drops_waiting_prompt_and_error_details_but_keeps_error_kind(env, fake, tmp_path):
    with_config(env, tmp_path, **{"include_summary": False})
    process("claude", {"hook_event_name": "Notification", "notification_type": "idle_prompt",
                       "session_id": "s" * 9, "cwd": str(tmp_path), "message": "等你输入"},
            env, channels=[fake])
    process("claude", {"hook_event_name": "StopFailure", "error": "rate_limit",
                       "error_details": "429", "session_id": "e" * 9, "cwd": str(tmp_path)},
            env, channels=[fake])
    assert [n.body for n in fake.sent] == ["", ""]
    assert fake.sent[1].error_kind == "rate_limit"


def test_tool_detail_off_keeps_turn_summary(env, telegram, tmp_path):
    # SCN-004-A：只关命令预览
    with_config(env, tmp_path, **{"include_tool_detail": False})
    cwd = str(tmp_path / "p")
    process("claude", _stop(cwd, "回合摘要", session_title="标题"), env, channels=[telegram])
    process("codex", {**CODEX_PERMISSION, "cwd": cwd}, env, channels=[telegram])
    assert _visible(telegram) == ["✅ 回合完成 · p @ box\n\nAgent：Claude\n会话：abcdefgh\n标题：标题\n\n回合摘要",
                                  "🔐 需要授权 · p @ box\n\nAgent：Codex\n会话：bbbbbbbb"]


def test_143_privacy_config_drops_body_and_session_title(env, telegram, tmp_path):
    # SCN-004-B：privacy 优先于两个开关本身的值
    with_config(env, tmp_path, **{"privacy": True, "include_summary": True, "include_tool_detail": True})
    cwd = str(tmp_path / "p")
    process("codex", {**CODEX_PERMISSION, "cwd": cwd, "session_title": "标题"}, env, channels=[telegram])
    process("claude", _stop(cwd, "回合摘要", session_title="标题"), env, channels=[telegram])
    assert _visible(telegram) == ["🔐 需要授权 · p @ box\n\nAgent：Codex\n会话：bbbbbbbb",
                                  "✅ 回合完成 · p @ box\n\nAgent：Claude\n会话：abcdefgh"]


@pytest.mark.parametrize("env_value, file_privacy, body", [
    ("1", False, ""), ("true", False, ""), ("0", True, "回合摘要"), ("false", True, "回合摘要")])
def test_privacy_env_overrides_config_file(env, fake, tmp_path, env_value, file_privacy, body):
    with_config(env, tmp_path, **{"privacy": file_privacy})
    env["AGENT_NOTIFY_PRIVACY"] = env_value
    process("claude", _stop(tmp_path, "回合摘要"), env, channels=[fake])
    assert fake.sent[0].body == body


@pytest.mark.parametrize("value, expected", [
    ("false", False), ("0", False), ("no", False), ("OFF", False), ("", False),
    ("true", True), ("yes", True), ("anything", True),
    (True, True), (False, False), (0, False), (1, True),
])
def test_boolean_config_values_parsed_consistently(env, tmp_path, value, expected):
    # spec #2 §3.4：privacy 与 include_* 共用同一套真假判定；字符串 "false" 不能被当成真
    from agent_notify.config import load_config
    with_config(env, tmp_path, **{"privacy": value})
    assert load_config(env).privacy is expected
    for key in ("include_summary", "include_tool_detail"):
        with_config(env, tmp_path, **{key: value})
        assert getattr(load_config(env), key) is expected


def test_null_boolean_values_fall_back_to_defaults(env, tmp_path):
    # JSON null 视同缺省：privacy 默认关，include_* 默认开
    from agent_notify.config import load_config
    with_config(env, tmp_path, **{"privacy": None, "include_summary": None,
                                 "include_tool_detail": None})
    config = load_config(env)
    assert (config.privacy, config.include_summary, config.include_tool_detail) == \
        (False, True, True)


def test_include_switches_default_to_true(env, tmp_path):
    from agent_notify.config import load_config
    with_config(env, tmp_path)
    config = load_config(env)
    assert config.include_summary is True and config.include_tool_detail is True


def test_143_config_file_upgrade(tmp_path):
    # SCN-013-A：只有 telegram、privacy、events 三项，通知照常送达，开关和隐私生效
    from agent_notify.channels import build_channels
    from agent_notify.config import load_config
    env = with_config({"AGENT_NOTIFY_LOG": str(tmp_path / "n.log")}, tmp_path, **{
        "telegram": {"token": TOKEN, "chat_id": "7"}, "privacy": True,
        "events": {"permission": False}})
    [built] = build_channels(load_config(env))
    channel = telegram_channel(token=built.token, chat_id=built.chat_id)
    cwd = str(tmp_path / "p")
    process("codex", {**CODEX_PERMISSION, "cwd": cwd}, env, channels=[channel])
    process("claude", _stop(cwd, "回合摘要", session_title="标题"), env, channels=[channel])
    [request] = channel.opener.requests
    assert request.body["chat_id"] == "7"
    assert visible(request.body["text"]) == "✅ 回合完成 · p @ box\n\nAgent：Claude\n会话：abcdefgh"
