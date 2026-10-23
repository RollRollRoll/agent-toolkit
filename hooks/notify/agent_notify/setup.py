"""交互式配置向导：校验 token、自动获取 chat_id、写入用户级配置并发送测试通知。"""
from __future__ import annotations

import getpass
import json
import os
import sys
import urllib.request

from .channels import ChannelError, TelegramAPIError, TelegramChannel, telegram_call
from .config import config_path, read_config_file, telegram_section
from .testcmd import make_test_notification

MAX_TOKEN_ATTEMPTS = 3


class ConsoleTerminal:
    """真实终端：token 输入不回显。"""

    def ask(self, prompt):
        return input(prompt)

    def ask_secret(self, prompt):
        return getpass.getpass(prompt)

    def say(self, text=""):
        print(text)


def main(env, out=sys.stdout):
    """命令入口：只在交互终端里运行，避免 token 落进 Agent 对话或日志。"""
    if not sys.stdin.isatty():
        print("❌ 配置向导需要在交互终端里运行：请在你自己的终端执行 "
              "python3 <插件目录>/hooks/notify/bin/notify-setup.py", file=out)
        return 2
    return run_setup(env, ConsoleTerminal())


def run_setup(env, term, opener=urllib.request.urlopen):
    try:
        return _run(env, term, opener)
    except (KeyboardInterrupt, EOFError):
        term.say("\n已取消，配置未改动。")
        return 130


def _run(env, term, opener):
    path = config_path(env)
    term.say("🔧 agent-notify 配置向导")
    term.say(f"配置文件：{path}")

    existing, corrupt = read_config_file(path)
    if path.exists():
        if corrupt:
            term.say("⚠️ 现有配置文件不是合法 JSON，继续后会备份为 config.json.bak。")
        else:
            term.say("已有配置文件，只会替换 telegram 的 token 与 chat_id，其他设置保留。")
        if term.ask("继续并覆盖？[y/N]：").strip().lower() not in ("y", "yes"):
            term.say("已取消，配置未改动。")
            return 1

    token, username = _ask_token(term, opener)
    if token is None:
        term.say(f"❌ 连续 {MAX_TOKEN_ATTEMPTS} 次未通过校验（原因见上方），配置未改动。"
                 "Unauthorized 表示 token 不对，网络错误请检查网络或代理后重试。")
        return 1
    chat_id = _find_chat_id(term, token, username, opener)
    if chat_id is None:
        term.say("已退出，配置未改动。")
        return 1
    if corrupt:
        backup = path.with_name(path.name + ".bak")
        path.replace(backup)
        # 损坏的旧文件可能含 token，备份同样收紧到 600
        os.chmod(backup, 0o600)
    _write_config(path, existing, token, chat_id)
    term.say(f"✅ 已写入 {path}（权限 600），chat_id={chat_id}")
    _warn_env_override(term, env)
    return _send_test(term, token, chat_id, opener)


def _warn_env_override(term, env):
    # 只提示变量名，不回显变量值
    names = [n for n in ("AGENT_NOTIFY_TELEGRAM_TOKEN", "AGENT_NOTIFY_TELEGRAM_CHAT_ID") if env.get(n)]
    if names:
        term.say(f"⚠️ 当前环境设置了 {'、'.join(names)}，hook 会优先使用环境变量而不是刚写入的配置。")


def _ask_token(term, opener):
    term.say("1/3 在 Telegram 找 @BotFather 发送 /newbot 创建 Bot（已有可跳过），复制它给的 token。")
    for _ in range(MAX_TOKEN_ATTEMPTS):
        token = term.ask_secret("Bot token（输入不显示）：").strip()
        if not token:
            term.say("token 不能为空。")
            continue
        try:
            me = telegram_call(token, "getMe", opener=opener) or {}
        except ChannelError as exc:
            term.say(f"❌ token 校验失败：{_redact(exc, token)}")
            continue
        username = me.get("username", "")
        term.say(f"✅ 已连接 Bot @{username}")
        return token, username
    return None, ""


def _find_chat_id(term, token, username, opener):
    """返回 chat_id 字符串；用户输入 q 时返回 None。"""
    term.say(f"2/3 在 Telegram 打开 https://t.me/{username} ，给 Bot 发一条任意消息。")
    while True:
        answer = term.ask("发完后按回车自动获取；也可直接输入 chat_id；输入 q 退出：").strip()
        if answer.lower() == "q":
            return None
        if answer:
            if _looks_like_chat_id(answer):
                return answer
            term.say("chat_id 格式不对，应为整数（群组通常以 -100 开头）。")
            continue
        try:
            chats = _recent_chats(telegram_call(token, "getUpdates", opener=opener) or [])
        except ChannelError as exc:
            if isinstance(exc, TelegramAPIError) and exc.code == 409:
                term.say("这个 Bot 设置了 webhook，无法自动获取 chat_id，请直接输入。")
            else:
                term.say(f"❌ 获取消息失败：{_redact(exc, token)}")
            continue
        if not chats:
            term.say("还没收到消息。确认已给 Bot 发过消息后再按回车。")
            continue
        if len(chats) == 1:
            return chats[0][0]
        return _choose_chat(term, chats)


def _recent_chats(updates):
    """从 getUpdates 结果提取去重后的对话列表，最近的在前：[(chat_id, 描述)]。"""
    seen = {}
    for update in reversed(updates):
        for key in ("message", "edited_message", "channel_post", "my_chat_member"):
            chat = (update.get(key) or {}).get("chat")
            if chat and "id" in chat:
                chat_id = str(chat["id"])
                if chat_id not in seen:
                    name = chat.get("title") or chat.get("first_name") or chat.get("username") or chat_id
                    seen[chat_id] = f"{name}（{chat.get('type', '?')}，{chat_id}）"
                break
    return list(seen.items())


def _choose_chat(term, chats):
    term.say("收到多个对话的消息：")
    for i, (_, label) in enumerate(chats, 1):
        term.say(f"  {i}. {label}")
    while True:
        answer = term.ask(f"选择编号 1-{len(chats)}：").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(chats):
            return chats[int(answer) - 1][0]
        term.say("编号无效。")


def _looks_like_chat_id(text):
    return text.lstrip("-").isdigit()


def _write_config(path, data, token, chat_id):
    """合并写入 telegram 段，保留其他配置；先写临时文件再替换，权限始终为 600。"""
    telegram = telegram_section(data)
    data = {**data, "telegram": {**telegram, "token": token, "chat_id": chat_id}}
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _send_test(term, token, chat_id, opener):
    try:
        TelegramChannel(token, chat_id, opener=opener).send(make_test_notification())
    except ChannelError as exc:
        term.say(f"❌ 测试通知发送失败：{exc}。配置已保存，可稍后运行 notify-test 重试。")
        return 1
    term.say("3/3 ✅ 测试通知已发送，请在 Telegram 查看。")
    return 0


def _redact(exc, token):
    return str(exc).replace(token, "***") if token else str(exc)
