from __future__ import annotations

import sys
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
