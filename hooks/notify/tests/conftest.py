from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TOKEN = "123456:FIXTURE-SECRET-TOKEN"


class FakeChannel:
    """假渠道：记录收到的通知，可配置为抛错。"""

    name = "fake"

    def __init__(self, error=None):
        self.sent = []
        self.error = error

    def send(self, notification):
        if self.error:
            raise self.error
        self.sent.append(notification)


def process(agent, payload, env, channels):
    """主测试 seam：从原始 payload 经 hook 归一化到渠道投递；渠道可用 FakeChannel 或 telegram_channel()。"""
    from agent_notify.config import load_config
    from agent_notify.hook import build, deliver
    config = load_config(env)
    notification = build(agent, payload, config)
    if notification is not None:
        deliver(notification, config, channels)


@pytest.fixture
def env(tmp_path):
    return {
        "AGENT_NOTIFY_TELEGRAM_TOKEN": TOKEN,
        "AGENT_NOTIFY_TELEGRAM_CHAT_ID": "42",
        "AGENT_NOTIFY_CONFIG": str(tmp_path / "missing.json"),
        "AGENT_NOTIFY_LOG": str(tmp_path / "notify.log"),
    }


@pytest.fixture
def fake():
    return FakeChannel()


@pytest.fixture
def hostname(monkeypatch):
    """机器名固定为 box.local；测试可改 hostname["value"]。各文件用 usefixtures 默认启用。"""
    names = {"value": "box.local"}
    monkeypatch.setattr("socket.gethostname", lambda: names["value"])
    return names


def with_config(env, tmp_path, **data):
    """把 data 写成配置文件并让 env 指向它；直接修改 env 并返回它。"""
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(data), encoding="utf-8")
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    return env


def http_error(code, description):
    """Bot API 返回的 HTTP 错误，响应体与 Telegram 一致。"""
    import urllib.error
    body = {"ok": False, "error_code": code, "description": description}
    return urllib.error.HTTPError("u", code, "err", {}, io.BytesIO(json.dumps(body).encode()))


@dataclass
class TelegramRequest:
    """假 opener 记录的一次 Bot API 请求。"""

    method: str
    body: dict
    timeout: float


class RecordingOpener:
    """假 urlopen：按顺序返回预设结果（异常则抛出，bytes 作为响应体，耗尽后视为成功），记录每次请求。"""

    def __init__(self, outcomes=()):
        self.outcomes = list(outcomes)
        self.requests = []

    def __call__(self, request, timeout):
        method = request.full_url.rsplit("/", 1)[1]
        self.requests.append(TelegramRequest(method, json.loads(request.data or b"{}"), timeout))
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, Exception):
            raise outcome
        # bytes 结果作为响应体原样返回（如 getMe 的 Bot 信息）
        return io.BytesIO(outcome if isinstance(outcome, bytes) else b'{"ok":true}')

    def texts(self):
        """每次 sendMessage 请求体中的 text。"""
        return [r.body["text"] for r in self.requests if r.method == "sendMessage"]


def telegram_channel(outcomes=(), token=TOKEN, chat_id="42", env=None, opener=None):
    """真实 TelegramChannel，网络换成 RecordingOpener；用 channel.opener 取请求记录。

    传入 env 时按该环境的配置经 build_channels 构造（可观察 request_timeout 等配置）。
    """
    from agent_notify.channels import TelegramChannel, build_channels
    opener = opener or RecordingOpener(outcomes)
    if env is not None:
        from agent_notify.config import load_config
        [channel] = build_channels(load_config(env), opener=opener)
        return channel
    return TelegramChannel(token, chat_id, opener=opener)


@pytest.fixture
def telegram():
    return telegram_channel()


class _Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def visible(html_text):
    """Telegram HTML 解析后用户看到的文本（去掉标签、还原转义）。"""
    parser = _Visible()
    parser.feed(html_text)
    parser.close()
    return "".join(parser.parts)
