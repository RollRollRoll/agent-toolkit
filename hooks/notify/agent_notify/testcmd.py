"""测试通知命令：同步发送，在终端报告成功或失败原因。"""
from __future__ import annotations

import sys

from .channels import build_channels
from .config import load_config
from .hook import Notification, render
from .log import redact


def make_test_notification():
    """测试命令与配置向导共用的测试通知。"""
    return Notification("test", "测试通知", "[agent-notify] 测试通知",
                        summary="如果你看到这条消息，说明配置正确。")


def main(env, out=sys.stdout):
    config = load_config(env)
    channels = build_channels(config, render)
    if not channels:
        print("❌ 没有可用渠道，请检查配置中的 channels", file=out)
        return 1
    notification = make_test_notification()
    failed = False
    for channel in channels:
        try:
            channel.send(notification)
            print(f"✅ {channel.name}：发送成功", file=out)
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(f"❌ {channel.name}：{redact(config, str(exc))}", file=out)
    return 1 if failed else 0
