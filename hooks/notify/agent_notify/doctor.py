"""诊断命令 notify-doctor（REQ-009）：逐项检查配置、凭据、日志与 Bot 可达性，只读。

只调用 getMe、getChat（NEG-004），token 只显示前 4 位和后 4 位（NEG-001）。
"""
from __future__ import annotations

import os
import re
import stat
import sys
import time
import urllib.request

from .channels import ChannelError, telegram_call
from .config import EVENT_KEYS, config_path, load_config, read_config_file, resolve_host
from .redaction import redact

OK, WARN, FAIL, SKIP = "✅", "⚠️", "❌", "⏭️"
USAGE = "用法：notify-doctor [--offline]"
NETWORK_HINT = "无法连接 Telegram：检查网络或代理（HTTPS_PROXY）设置"


class Report:
    """收集检查结果并按行输出；⚠️ / ❌ 之后附一行修复建议。"""

    def __init__(self, out):
        self.out = out
        self.failed = False

    def item(self, status, text, hint=""):
        print(f"{status} {text}", file=self.out)
        if hint and status in (WARN, FAIL):
            print(f"   → {hint}", file=self.out)
        if status == FAIL:
            self.failed = True


def mask_token(token):
    """token 只露出前 4 位和后 4 位；太短时一位也不露。"""
    return f"{token[:4]}…{token[-4:]}" if len(token) >= 12 else "***"


def main(env, out=sys.stdout, opener=urllib.request.urlopen, argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(a != "--offline" for a in argv):
        print(USAGE, file=out)
        return 2
    offline = "--offline" in argv
    report = Report(out)
    config = load_config(env)
    print("agent-notify 诊断" + ("（离线模式）" if offline else ""), file=out)

    _check_config_file(report, config_path(env))
    have_credentials = _check_credentials(report, env, config)
    _show_settings(report, config)
    _check_runtime(report, config)

    # 在线检查：--offline 时整段不执行，不发起任何网络请求
    if not offline:
        if have_credentials:
            _online(report, config, opener)
        else:
            report.item(SKIP, "getMe：跳过（缺少 token 或 chat_id）")
            report.item(SKIP, "getChat：跳过（缺少 token 或 chat_id）")
    return 1 if report.failed else 0


def _check_config_file(report, path):
    """路径、是否存在、是否为合法 JSON、权限是否为 600。"""
    if not path.exists():
        report.item(WARN, f"配置文件：{path}（不存在）",
                    "运行 notify-setup 创建配置；只用环境变量提供凭据时可忽略")
        return
    _, broken = read_config_file(path)
    if broken:
        report.item(FAIL, f"配置文件：{path}（不是合法的 JSON 对象，当前按空配置运行）",
                    "修正文件中的 JSON 语法，或运行 notify-setup 重新生成")
        return
    report.item(OK, f"配置文件：{path}")
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        report.item(WARN, f"配置文件权限：无法读取（{exc}）", f"运行 chmod 600 {path}")
        return
    if mode & 0o177:
        report.item(WARN, f"配置文件权限：{mode:o}（宽于 600，其他用户可能读到 token）",
                    f"运行 chmod 600 {path}")
    else:
        report.item(OK, f"配置文件权限：{mode:o}")


def _check_credentials(report, env, config):
    """token、chat_id 是否存在及来源；token 只显示首尾各 4 位。返回两者是否齐全。"""
    if config.telegram_token:
        source = _source(env, "AGENT_NOTIFY_TELEGRAM_TOKEN")
        report.item(OK, f"token：{mask_token(config.telegram_token)}（来自{source}）")
    else:
        report.item(FAIL, "token：未设置",
                    "运行 notify-setup，或设置环境变量 AGENT_NOTIFY_TELEGRAM_TOKEN")
    if config.telegram_chat_id:
        source = _source(env, "AGENT_NOTIFY_TELEGRAM_CHAT_ID")
        report.item(OK, f"chat_id：{config.telegram_chat_id}（来自{source}）")
    else:
        report.item(FAIL, "chat_id：未设置",
                    "运行 notify-setup，或设置环境变量 AGENT_NOTIFY_TELEGRAM_CHAT_ID")
    return bool(config.telegram_token and config.telegram_chat_id)


def _on(flag):
    return "开" if flag else "关"


def _show_settings(report, config):
    """生效值：已经过 load_config 归一化（非法值按默认、超限按上限），与 hook 实际行为一致。"""
    events = " ".join(f"{key}={_on(config.event_enabled(types[0]))}"
                      for key, types in EVENT_KEYS.items())
    report.item(OK, f"事件开关：{events}")
    host = resolve_host(config)
    origin = "配置 host_label" if config.host_label else "机器名"
    report.item(OK, f"主机：{host or '（空）'}（来自{origin}）")
    report.item(OK, f"内容：include_summary={_on(config.include_summary)} "
                    f"include_tool_detail={_on(config.include_tool_detail)} "
                    f"隐私模式={_on(config.privacy)}")
    report.item(OK, f"参数：summary_max_chars={config.summary_max_chars} "
                    f"request_timeout={config.request_timeout:g} log_level={config.log_level}")


def _check_runtime(report, config):
    """Python 版本、日志可写性、最近一次发送失败，以及两条固定提示。"""
    version = ".".join(str(v) for v in sys.version_info[:3])
    if sys.version_info >= (3, 9):
        report.item(OK, f"Python：{version}")
    else:
        report.item(FAIL, f"Python：{version}（需要 3.9 或更高）", "升级 python3 到 3.9 或更高版本")

    path = config.log_path
    if _writable(path):
        report.item(OK, f"日志路径：{path}（可写）")
    else:
        report.item(FAIL, f"日志路径：{path}（不可写）",
                    "检查目录权限，或用环境变量 AGENT_NOTIFY_LOG 指向可写位置")

    _check_last_failure(report, path)

    print("💡 Codex 需在 /hooks 中信任本插件的 hooks，否则不会触发通知", file=report.out)
    print("💡 hook 注册状态需在 Agent 内确认（Claude Code 用 /hooks 查看）", file=report.out)


def _check_last_failure(report, path):
    """最近一次发送失败：之后有成功行为 ✅（已恢复），否则 ⚠️；读日志失败也是 ⚠️（spec #2 §3.4）。"""
    try:
        failure, recovered = _last_failure(path)
    except OSError as exc:
        report.item(WARN, f"最近一次发送失败：无法读取日志（{exc.strerror or exc}）",
                    "检查日志文件权限，或用环境变量 AGENT_NOTIFY_LOG 指向可读写位置")
        return
    if not failure:
        report.item(OK, "最近一次发送失败：无")
    elif recovered:
        report.item(OK, f"最近一次发送失败：{failure}（已恢复）")
    else:
        report.item(WARN, f"最近一次发送失败：{failure}",
                    "运行 notify-test 复现；仍失败时按上面的 getMe / getChat 结果处理")


def _writable(path):
    """日志文件存在时看文件本身，否则看最近一级已存在的父目录；不创建任何文件或目录。"""
    if path.exists():
        return os.access(path, os.W_OK)
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return os.access(parent, os.W_OK | os.X_OK)


def _last_failure(path):
    """从新到旧扫描日志（及轮转文件），返回 (失败摘要, 是否已恢复)。

    失败摘要是最近一条 result=fail 的「时间 error=类型 [status=码]」，没有失败时为空串；
    它之后出现过 result=ok / fallback 视为已恢复。文件不存在跳过，其他读取错误抛 OSError。
    """
    recovered = False
    for candidate in (path, path.with_name(path.name + ".1")):
        try:
            lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
        except FileNotFoundError:
            continue
        for text in reversed(lines):
            # detail 是最后一个字段且可能含任意文本，先截掉，避免误取其中的 error= / result=
            head = text.split(" detail=", 1)[0]
            match = _RESULT.search(head)
            if not match:
                continue
            if match.group(1) != "fail":
                recovered = True
                continue
            return " ".join([head.split(" ", 1)[0]] + _FIELD.findall(head)), recovered
    return "", recovered


# 日志行的结果字段与失败行里的错误类型、HTTP 状态码（#8 的日志格式）
_RESULT = re.compile(r"(?<= )result=(ok|fallback|fail)(?= |$)")
_FIELD = re.compile(r"(?<= )(?:error|status)=\S+")


def _get_me_hint(exc):
    if getattr(exc, "code", None) in (401, 404):
        return "token 无效或已被撤销：运行 notify-setup 重新配置"
    return NETWORK_HINT


def _source(env, key):
    # 与 load_config 一致：非空环境变量优先，否则来自配置文件
    return f"环境变量 {key}" if env.get(key) else "配置文件"


def _online(report, config, opener):
    deadline = time.monotonic() + config.request_timeout
    try:
        me = telegram_call(config.telegram_token, "getMe", opener=opener, timeout=config.request_timeout)
    except ChannelError as exc:
        report.item(FAIL, f"getMe：{redact(str(exc), config.telegram_token)}", _get_me_hint(exc))
        report.item(SKIP, "getChat：跳过（getMe 未通过）")
        return
    report.item(OK, f"getMe：token 有效，Bot @{(me or {}).get('username', '?')}")
    # 两次调用共用 request_timeout 的总时限，保证命令在 request_timeout + 5 秒内结束
    remaining = max(deadline - time.monotonic(), 1.0)
    try:
        telegram_call(config.telegram_token, "getChat", {"chat_id": config.telegram_chat_id},
                      opener=opener, timeout=remaining)
    except ChannelError as exc:
        hint = ("先给 Bot 发一条消息，或检查 chat_id 填写错误：可运行 notify-setup 重新获取"
                if getattr(exc, "code", None) is not None else NETWORK_HINT)
        report.item(FAIL, f"getChat：chat_id {config.telegram_chat_id} 不可达："
                          f"{redact(str(exc), config.telegram_token)}", hint)
        return
    report.item(OK, f"getChat：chat_id {config.telegram_chat_id} 可达")
