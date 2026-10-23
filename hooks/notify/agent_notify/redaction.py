"""敏感内容遮蔽（REQ-005）：按固定规则把文本中的凭据替换为 ***，内容准备与日志共用。"""
from __future__ import annotations

import re

MASK = "***"

# 按 REQ-005 的顺序排列；每条规则用捕获组 1 保留键名或前缀，只替换其后的值
_KEY_WORDS = r"(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)"

# 每条规则是 (正则, 替换模板)；模板里的 \1 是保留的键名或前缀
_RULES = [(re.compile(pattern, re.IGNORECASE), repl) for pattern, repl in [
    # Telegram bot token 形态：数字:35 位字母数字_-，整串替换
    (r"(?<!\d)()\d+:[\w-]{35}(?![\w-])", r"\1***"),
    # Authorization / Proxy-Authorization 头里 Bearer、Basic、Token 之后的值
    (r"((?:proxy-)?authorization[\"']?\s*[:=]\s*[\"']?(?:bearer|basic|token)\s+)[^\s\"',;]+",
     r"\1***"),
    # 常见密钥前缀：保留前缀，替换其后的值
    (r"\b(sk-)[\w-]{16,}", r"\1***"),
    (r"\b(gh[pousr]_)[a-z0-9]{20,}", r"\1***"),
    (r"\b(github_pat_)\w{20,}", r"\1***"),
    (r"\b(xox[abpors]-)[a-z0-9][a-z0-9-]*", r"\1***"),
    (r"\b(akia|asia)[a-z0-9]{16}\b", r"\1***"),
    # 三段式 JWT，整串替换
    (r"()\beyJ[\w-]*\.[\w-]+\.[\w-]+", r"\1***"),
    # 敏感键名的键值：= 或 : 之后的值；引号包裹的值保留引号（\2 是开引号，
    # 后顾断言保证只有开了引号才读到对应的闭引号为止）
    (r"([\w.-]*" + _KEY_WORDS + r"[\w.-]*[\"']?\s*[:=]\s*)([\"']?)"
     r"(?:(?<=\")[^\"]+|(?<=')[^']+|[^\s&,;\"'}\]]+)\2", r"\1\2***\2"),
    # 命令行参数 --password <值> / --password=<值>
    (r"(--password(?:\s*=\s*|\s+))(?:\"[^\"]*\"|'[^']*'|[^\s\"']+)", r"\1***"),
    # 仅 mysql 系列命令（同一段命令内，不跨 ; & |）的 -p<值>；-p 区分大小写，-P 是端口
    (r"(\bmysql(?:dump|admin)?\b[^;&|\n]*?\s(?-i:-p))[^\s;&|]+", r"\1***"),
    # URL 用户信息中的密码 scheme://user:<值>@host
    (r"([a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s@/]+(?=@)", r"\1***"),
]]


def redact(text, token=""):
    """返回遮蔽后的文本；token 为当前配置的 bot token 原文。出错时整段替换为 ***。"""
    try:
        if token:
            # bot token 原文用字符串替换，放在正则之前
            text = text.replace(token, MASK)
        for rule, repl in _RULES:
            text = rule.sub(repl, text)
        return text
    except Exception:  # noqa: BLE001 - 宁可多遮，也不能让通知失败
        return MASK
