"""测试通知命令：同步发送，在终端报告成功或失败原因。"""
from __future__ import annotations

import sys

from .channels import build_channels
from .config import TEST_NOTIFICATION, load_config, resolve_host
from .hook import Notification
from .redaction import redact


def make_test_notification(host=""):
    """测试命令与配置向导共用的测试通知；项目位置显示 agent-notify。"""
    return Notification("test", TEST_NOTIFICATION, host=host, project="agent-notify",
                        body="如果你看到这条消息，说明配置正确。")


def main(env, out=sys.stdout):
    config = load_config(env)
    channels = build_channels(config)
    if not channels:
        print("❌ 没有可用渠道，请检查配置中的 channels", file=out)
        return 1
    notification = make_test_notification(resolve_host(config))
    failed = False
    for channel in channels:
        try:
            channel.send(notification)
            print(f"✅ {channel.name}：发送成功", file=out)
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(f"❌ {channel.name}：{redact(str(exc), config.telegram_token)}", file=out)
    return 1 if failed else 0
