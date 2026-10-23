from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass
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


@dataclass
class TelegramRequest:
    """假 opener 记录的一次 Bot API 请求。"""

    method: str
    body: dict
    timeout: float


class RecordingOpener:
    """假 urlopen：按顺序返回预设结果（异常则抛出，耗尽后视为成功），记录每次请求。"""

    def __init__(self, outcomes=()):
        self.outcomes = list(outcomes)
        self.requests = []

    def __call__(self, request, timeout):
        method = request.full_url.rsplit("/", 1)[1]
        self.requests.append(TelegramRequest(method, json.loads(request.data or b"{}"), timeout))
        outcome = self.outcomes.pop(0) if self.outcomes else None
        if isinstance(outcome, Exception):
            raise outcome
        return io.BytesIO(b'{"ok":true}')

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
