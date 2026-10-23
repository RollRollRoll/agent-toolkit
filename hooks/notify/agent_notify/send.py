"""后台发送子进程：从环境变量读取已渲染前的通知并投递。"""
from __future__ import annotations

import json
import os

from .channels import build_channels
from .config import load_config
from .hook import Notification, deliver, render


def main():
    env = dict(os.environ)
    config = load_config(env)
    notification = Notification(**json.loads(env.pop("AGENT_NOTIFY_PAYLOAD")))
    deliver(notification, config, build_channels(config, render))


if __name__ == "__main__":
    main()
