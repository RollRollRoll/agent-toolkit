"""hook 入口：把 Agent 原始 payload 转成通知并交给渠道发送。"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import (AGENT_LABELS, ERROR, PERMISSION, TURN_COMPLETE, TURN_END_WAITING,
                     WAITING_INPUT, load_config)
from .log import log_event

# Claude Code Notification 事件的 notification_type → 通知事件类型
# elicitation_* 是 MCP 服务器在回合中途向用户请求输入；未列出的类型一律不通知
CLAUDE_NOTIFICATION_TYPES = {
    "idle_prompt": WAITING_INPUT,
    "elicitation_dialog": WAITING_INPUT,
    "elicitation_url_dialog": WAITING_INPUT,
    "permission_prompt": PERMISSION,
}

FIELD_MAX_CHARS = 64  # 项目、分支、会话标题的长度上限（REQ-003）
HOST_LIMIT = 32


@dataclass
class Notification:
    """结构化通知对象：只承载已处理的字段，排版由各渠道负责（DEC-001）。"""

    agent: str
    event_type: str
    host: str = ""
    project: str = ""
    branch: str = ""
    session_id: str = ""
    session_title: str = ""
    error_kind: str = ""
    body: str = ""  # 摘要或命令预览


def build(agent, payload, config):
    """把原始 payload 转成通知；不需要通知时返回 None。"""
    if agent not in AGENT_LABELS or not isinstance(payload, dict):
        return None
    event_type = _event_type(agent, payload)
    if event_type is None or not config.event_enabled(event_type):
        # debug 级别记录跳过原因；只记事件元数据，不记正文
        reason = ("subagent" if payload.get("agent_id") else "unsupported") \
            if event_type is None else "event_disabled"
        log_event(config, "debug", agent=agent, session=_short_session(payload),
                  hook=payload.get("hook_event_name"), event=event_type,
                  result="skip", reason=reason)
        return None
    cwd = payload.get("cwd") or os.getcwd()
    project, branch = _project_and_branch(cwd)
    # 内容准备顺序（DEC-001）：选取原文 → 遮蔽 → 开关 → 截断
    body = _summary(event_type, payload)
    session_title = str(payload.get("session_title") or "")
    # 开关（REQ-004）：授权的正文是命令预览，其余事件的正文和会话标题属于摘要
    if not (config.include_tool_detail if event_type == PERMISSION else config.include_summary):
        body = ""
    if not config.include_summary:
        session_title = ""
    return Notification(
        agent, event_type, host=resolve_host(config), project=_truncate(project, FIELD_MAX_CHARS),
        branch=_truncate(branch, FIELD_MAX_CHARS),
        session_id=_short_session(payload),
        session_title=_truncate(session_title, FIELD_MAX_CHARS),
        error_kind=str(payload.get("error") or "") if event_type == ERROR else "",
        body=_truncate(body, config.summary_max_chars),
    )


def _short_session(payload):
    return str(payload.get("session_id") or "")[:8]


def deliver(notification, config, channels):
    """逐个渠道发送并计时，按级别记录结果；单个渠道失败只记日志，互不影响。"""
    for channel in channels:
        fields = {"agent": notification.agent, "session": notification.session_id,
                  "event": notification.event_type, "channel": getattr(channel, "name", "?")}
        start = time.monotonic()
        try:
            channel.send(notification)
        except Exception as exc:  # noqa: BLE001 - 任何失败都不能影响 Agent
            # 失败行固定带 result=fail 与 error=<类型>，供诊断命令查找最近一次失败
            log_event(config, "error", **fields, result="fail", duration_ms=_elapsed_ms(start),
                      error=getattr(exc, "kind", "internal"), status=getattr(exc, "code", None),
                      detail=str(exc))
            continue
        log_event(config, "info", **fields, result="ok", duration_ms=_elapsed_ms(start))


def _elapsed_ms(start):
    return int((time.monotonic() - start) * 1000)




def _event_type(agent, payload):
    """按 Agent 支持矩阵把 hook 事件映射为通知事件类型；不支持的返回 None。"""
    event = payload.get("hook_event_name")
    if payload.get("agent_id"):
        # 子 agent 上下文触发的事件不通知
        return None
    if agent == "claude":
        if event == "Stop":
            return TURN_COMPLETE
        if event == "Notification":
            return CLAUDE_NOTIFICATION_TYPES.get(payload.get("notification_type"))
        if event == "StopFailure":
            return ERROR
    if agent == "codex":
        if event == "Stop":
            return TURN_END_WAITING
        if event == "PermissionRequest":
            return PERMISSION
    return None


def _summary(event_type, payload):
    """按事件类型挑选摘要原文（未截断）。"""
    if event_type == ERROR:
        parts = [payload.get("error"), payload.get("error_details")]
        return " · ".join(str(p) for p in parts if p)
    if event_type == PERMISSION:
        if payload.get("tool_input") is not None:
            tool_input = payload["tool_input"]
            command = tool_input.get("command") if isinstance(tool_input, dict) else None
            detail = command or json.dumps(tool_input, ensure_ascii=False)
            return f"{payload.get('tool_name', '')}: {detail}".strip(": ")
        return str(payload.get("message") or "")
    return str(payload.get("last_assistant_message") or payload.get("message") or "")


def resolve_host(config):
    """主机：配置的 host_label 优先，否则取机器名第一个 . 之前的部分；超长截断（REQ-002）。"""
    host = config.host_label
    if not host:
        try:
            host = socket.gethostname().split(".", 1)[0].strip()
        except OSError:
            host = ""
    return host if len(host) <= HOST_LIMIT else host[:HOST_LIMIT] + "…"


def _git(cwd, *args):
    try:
        result = subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, timeout=1
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _project_and_branch(cwd):
    """项目名取 git 仓库根目录名，不在仓库内则取 cwd 末级目录名。"""
    root = _git(cwd, "rev-parse", "--show-toplevel")
    if not root:
        return Path(cwd).name, ""
    # symbolic-ref 在尚无提交的仓库里也能拿到分支名
    branch = _git(cwd, "symbolic-ref", "--short", "-q", "HEAD")
    return Path(root).name, branch


def _truncate(text, limit):
    # Python 字符串按码点截断，不会切坏多字节字符
    return text if len(text) <= limit else text[:limit] + "…"


def run(agent, raw, env, spawn=True):
    """hook 入口：任何情况都返回 0，不向 stdout 输出决策。"""
    try:
        config = load_config(env)
        try:
            payload = json.loads(raw or "{}")
        except ValueError:
            log_event(config, "error", agent=agent, result="fail", error="invalid_payload")
            return 0
        notification = build(agent, payload, config)
        if notification is None:
            return 0
        if "telegram" in config.channels and not (config.telegram_token and config.telegram_chat_id):
            log_event(config, "debug", agent=agent, session=notification.session_id,
                      event=notification.event_type, channel="telegram",
                      result="skip", reason="missing_credentials")
            return 0
        if spawn:
            _spawn_sender(notification, env)
        else:
            from .channels import build_channels
            deliver(notification, config, build_channels(config))
    except Exception as exc:  # noqa: BLE001
        try:
            log_event(load_config(env), "error", agent=agent, result="fail",
                      error="internal", detail=repr(exc))
        except Exception:  # noqa: BLE001
            pass
    return 0


def _spawn_sender(notification, env):
    """派生脱离父进程的发送子进程，入口立即返回（DEC-002）。"""
    import sys
    from dataclasses import asdict
    subprocess.Popen(
        [sys.executable, "-m", "agent_notify.send"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, **env, "AGENT_NOTIFY_PAYLOAD": json.dumps(asdict(notification))},
        cwd=str(Path(__file__).resolve().parents[1]),
        start_new_session=True,
    )
