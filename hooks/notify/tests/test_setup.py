from __future__ import annotations

import io
import json
import stat
import urllib.error

from conftest import TOKEN

from agent_notify import setup


HOST_PROMPT = "主机标签"


class FakeTelegram:
    """假 Bot API：按方法名依次返回预设结果（最后一个重复使用），并记录调用。"""

    def __init__(self, **responses):
        self.responses = {k: list(v) for k, v in responses.items()}
        self.calls = []

    def __call__(self, request, timeout):
        method = request.full_url.rsplit("/", 1)[1]
        self.calls.append((method, json.loads(request.data or b"{}")))
        queue = self.responses[method]
        outcome = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(outcome, Exception):
            raise outcome
        return io.BytesIO(json.dumps({"ok": True, "result": outcome}).encode())

    def sent_to(self):
        return [body["chat_id"] for method, body in self.calls if method == "sendMessage"]


class ScriptedTerminal:
    """按脚本回答提示，记录全部输出。"""

    def __init__(self, answers=(), secrets=(), host=""):
        self.answers = list(answers)
        self.secrets = list(secrets)
        self.host = host  # 主机标签提示的回答，默认直接回车
        self.transcript = ""

    def ask(self, prompt):
        self.transcript += prompt + "\n"
        if HOST_PROMPT in prompt:
            return self.host
        return self.answers.pop(0)

    def ask_secret(self, prompt):
        self.transcript += prompt + "\n"
        return self.secrets.pop(0)

    def say(self, text=""):
        self.transcript += text + "\n"


def _private(chat_id, name="Fan", update_id=1):
    return {"update_id": update_id,
            "message": {"chat": {"id": chat_id, "type": "private", "first_name": name}}}


def _env(tmp_path):
    return {"AGENT_NOTIFY_CONFIG": str(tmp_path / "agent-notify" / "config.json"),
            "HOME": str(tmp_path)}


def test_happy_path_writes_config_and_sends_test_message(tmp_path):
    env = _env(tmp_path)
    api = FakeTelegram(getMe=[{"username": "my_bot"}], getUpdates=[[_private(42)]],
                       sendMessage=[{"message_id": 1}])
    term = ScriptedTerminal(answers=[""], secrets=[TOKEN])

    assert setup.run_setup(env, term, opener=api) == 0

    cfg = tmp_path / "agent-notify" / "config.json"
    assert json.loads(cfg.read_text())["telegram"] == {"token": TOKEN, "chat_id": "42"}
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600
    assert api.sent_to() == ["42"]
    assert "@my_bot" in term.transcript
    assert TOKEN not in term.transcript


def _unauthorized():
    body = json.dumps({"ok": False, "error_code": 401, "description": "Unauthorized"}).encode()
    return urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(body))


def test_invalid_token_is_reasked_then_accepted(tmp_path):
    api = FakeTelegram(getMe=[_unauthorized(), {"username": "my_bot"}],
                       getUpdates=[[_private(42)]], sendMessage=[{"message_id": 1}])
    term = ScriptedTerminal(answers=[""], secrets=["bad-token", TOKEN])
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 0
    assert "Unauthorized" in term.transcript


def test_three_invalid_tokens_abort_without_writing(tmp_path):
    api = FakeTelegram(getMe=[_unauthorized()])
    term = ScriptedTerminal(secrets=["a", "b", "c"])
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 1
    assert not (tmp_path / "agent-notify" / "config.json").exists()
    assert "Unauthorized" in term.transcript


def test_rejected_token_is_never_echoed(tmp_path):
    # 错误信息里带出 token（例如代理把 URL 写进报错）也必须脱敏
    leaky = urllib.error.URLError(f"cannot reach https://api.telegram.org/bot{TOKEN}/getMe")
    api = FakeTelegram(getMe=[leaky])
    term = ScriptedTerminal(secrets=[TOKEN, TOKEN, TOKEN])
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 1
    assert TOKEN not in term.transcript


def test_empty_token_is_reasked_without_calling_api(tmp_path):
    api = FakeTelegram(getMe=[{"username": "my_bot"}], getUpdates=[[_private(7)]],
                       sendMessage=[{"message_id": 1}])
    term = ScriptedTerminal(answers=[""], secrets=["", TOKEN])
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 0
    assert [m for m, _ in api.calls].count("getMe") == 1


def _run_chat_step(tmp_path, updates, answers):
    api = FakeTelegram(getMe=[{"username": "my_bot"}], getUpdates=updates,
                       sendMessage=[{"message_id": 1}])
    term = ScriptedTerminal(answers=answers, secrets=[TOKEN])
    code = setup.run_setup(_env(tmp_path), term, opener=api)
    return code, api, term


def test_no_message_yet_retries_until_one_arrives(tmp_path):
    code, api, term = _run_chat_step(tmp_path, [[], [_private(42)]], ["", ""])
    assert code == 0 and api.sent_to() == ["42"]
    assert "还没收到消息" in term.transcript


def test_chat_id_can_be_typed_manually(tmp_path):
    code, api, _ = _run_chat_step(tmp_path, [[]], ["-1001234567890"])
    assert code == 0 and api.sent_to() == ["-1001234567890"]


def test_invalid_manual_chat_id_is_rejected(tmp_path):
    code, api, term = _run_chat_step(tmp_path, [[]], ["abc", "42"])
    assert code == 0 and api.sent_to() == ["42"]
    assert "chat_id 格式不对" in term.transcript


def test_quit_at_chat_step_leaves_config_untouched(tmp_path):
    code, _, _ = _run_chat_step(tmp_path, [[]], ["q"])
    assert code == 1
    assert not (tmp_path / "agent-notify" / "config.json").exists()


def test_multiple_chats_are_listed_and_chosen(tmp_path):
    group = {"update_id": 3, "message": {"chat": {"id": -500, "type": "group", "title": "Dev"}}}
    updates = [[_private(42, update_id=1), _private(42, update_id=2), group]]
    code, api, term = _run_chat_step(tmp_path, updates, ["", "2"])
    # 最近的对话排在前面：1 = Dev 群，2 = 私聊
    assert "1. Dev" in term.transcript and "2. Fan" in term.transcript
    assert code == 0 and api.sent_to() == ["42"]


def test_webhook_conflict_falls_back_to_manual_entry(tmp_path):
    body = json.dumps({"ok": False, "description": "Conflict: can't use getUpdates "
                       "method while webhook is active"}).encode()
    conflict = urllib.error.HTTPError("u", 409, "Conflict", {}, io.BytesIO(body))
    code, api, term = _run_chat_step(tmp_path, [conflict], ["", "42"])
    assert code == 0 and api.sent_to() == ["42"]
    assert "webhook" in term.transcript


def _existing(tmp_path, data):
    cfg = tmp_path / "agent-notify" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps(data) if not isinstance(data, str) else data)
    cfg.chmod(0o644)
    return cfg


def _ok_api(chat_id=42):
    return FakeTelegram(getMe=[{"username": "my_bot"}], getUpdates=[[_private(chat_id)]],
                        sendMessage=[{"message_id": 1}])


def test_rewrite_keeps_other_settings_and_tightens_permissions(tmp_path):
    cfg = _existing(tmp_path, {"telegram": {"token": "999:OLD-SECRET", "chat_id": "1"}, "privacy": True,
                               "events": {"turn_complete": False}})
    term = ScriptedTerminal(answers=["y", ""], secrets=[TOKEN])
    assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 0
    data = json.loads(cfg.read_text())
    assert data["telegram"] == {"token": TOKEN, "chat_id": "42"}
    assert data["privacy"] is True and data["events"] == {"turn_complete": False}
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600
    assert "OLD-SECRET" not in term.transcript  # 已有 token 也不能回显


def test_declining_overwrite_leaves_config_untouched(tmp_path):
    original = {"telegram": {"token": "old", "chat_id": "1"}}
    cfg = _existing(tmp_path, original)
    api = _ok_api()
    term = ScriptedTerminal(answers=["n"])
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 1
    assert json.loads(cfg.read_text()) == original
    assert api.calls == []


def test_corrupt_config_is_backed_up_before_rewrite(tmp_path):
    cfg = _existing(tmp_path, "{not json")
    term = ScriptedTerminal(answers=["y", ""], secrets=[TOKEN])
    assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 0
    assert json.loads(cfg.read_text())["telegram"]["chat_id"] == "42"
    backup = cfg.parent / "config.json.bak"
    assert backup.read_text() == "{not json"
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600


def test_warns_when_env_vars_would_override_file(tmp_path):
    env = {**_env(tmp_path), "AGENT_NOTIFY_TELEGRAM_TOKEN": "env-token"}
    term = ScriptedTerminal(answers=[""], secrets=[TOKEN])
    assert setup.run_setup(env, term, opener=_ok_api()) == 0
    assert "AGENT_NOTIFY_TELEGRAM_TOKEN" in term.transcript
    assert "env-token" not in term.transcript


class InterruptingTerminal(ScriptedTerminal):
    def __init__(self, exc):
        super().__init__()
        self.exc = exc

    def ask_secret(self, prompt):
        raise self.exc


def test_ctrl_c_or_eof_cancels_without_writing(tmp_path):
    for exc in (KeyboardInterrupt(), EOFError()):
        term = InterruptingTerminal(exc)
        assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 130
        assert "已取消" in term.transcript
        assert not (tmp_path / "agent-notify" / "config.json").exists()


def test_main_refuses_without_interactive_terminal(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    assert setup.main(_env(tmp_path), out=out) == 2
    assert "终端" in out.getvalue()


# ---- 主机标签（REQ-012） ----


def _box(monkeypatch):
    monkeypatch.setattr("socket.gethostname", lambda: "box.local")


def _host_prompt(term):
    lines = [line for line in term.transcript.splitlines() if HOST_PROMPT in line]
    assert len(lines) == 1, term.transcript
    return lines[0]


def test_enter_at_host_prompt_adds_no_host_label(tmp_path, monkeypatch):
    # SCN-012-A：回车跳过，不新增 host_label，其他设置保留，权限 600
    _box(monkeypatch)
    cfg = _existing(tmp_path, {"telegram": {"token": "old", "chat_id": "1"}, "privacy": True})
    term = ScriptedTerminal(answers=["y", ""], secrets=[TOKEN], host="")
    assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 0
    assert "box" in _host_prompt(term)
    data = json.loads(cfg.read_text())
    assert "host_label" not in data
    assert data["privacy"] is True and data["telegram"] == {"token": TOKEN, "chat_id": "42"}
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600


def test_typed_host_label_is_written(tmp_path, monkeypatch):
    _box(monkeypatch)
    term = ScriptedTerminal(answers=[""], secrets=[TOKEN], host=" mbp ")
    assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 0
    cfg = tmp_path / "agent-notify" / "config.json"
    assert json.loads(cfg.read_text())["host_label"] == "mbp"
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600


def test_existing_host_label_is_default_and_kept_on_enter(tmp_path, monkeypatch):
    _box(monkeypatch)
    cfg = _existing(tmp_path, {"telegram": {"token": "old", "chat_id": "1"}, "host_label": "office"})
    term = ScriptedTerminal(answers=["y", ""], secrets=[TOKEN], host="")
    assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 0
    prompt = _host_prompt(term)
    assert "office" in prompt and "box" not in prompt
    assert json.loads(cfg.read_text())["host_label"] == "office"


def test_ctrl_c_or_eof_at_host_prompt_cancels_without_writing(tmp_path):
    for exc in (KeyboardInterrupt(), EOFError()):
        term = HostInterruptingTerminal(exc, answers=[""], secrets=[TOKEN])
        assert setup.run_setup(_env(tmp_path), term, opener=_ok_api()) == 130
        assert "已取消" in term.transcript
        assert not (tmp_path / "agent-notify" / "config.json").exists()


class HostInterruptingTerminal(ScriptedTerminal):
    def __init__(self, exc, **kwargs):
        super().__init__(**kwargs)
        self.exc = exc

    def ask(self, prompt):
        if HOST_PROMPT in prompt:
            raise self.exc
        return super().ask(prompt)


def _sent_text(api):
    from conftest import visible
    return [visible(body["text"]) for method, body in api.calls if method == "sendMessage"]


def test_test_notification_shows_effective_host(tmp_path, monkeypatch):
    # 测试通知第二行显示最终生效的主机：新输入的标签
    _box(monkeypatch)
    api = _ok_api()
    term = ScriptedTerminal(answers=[""], secrets=[TOKEN], host="mbp")
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 0
    assert _sent_text(api)[0].splitlines()[1] == "mbp"


def test_test_notification_falls_back_to_machine_name(tmp_path, monkeypatch):
    _box(monkeypatch)
    api = _ok_api()
    term = ScriptedTerminal(answers=[""], secrets=[TOKEN], host="")
    assert setup.run_setup(_env(tmp_path), term, opener=api) == 0
    assert _sent_text(api)[0].splitlines()[1] == "box"
