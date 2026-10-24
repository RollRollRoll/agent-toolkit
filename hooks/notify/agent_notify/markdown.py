"""把回合摘要里的 Markdown 转成 Telegram HTML（parse_mode=HTML 支持的子集）。

输入是已遮蔽、已截断的原文，输出可直接放进引用块。Telegram 没有标题和列表格式，
标题转成整行粗体；不认识的写法按原样转义。
"""
from __future__ import annotations

import html
import re

_HEADING = re.compile(r"#{1,6}\s+(.*)")
_BULLET = re.compile(r"(\s*)[-*+]\s+(.*)")
# 分隔线不含 ***：遮蔽后的值整行就是 ***，不能当成分隔线删掉
_RULE = re.compile(r"\s*(?:-{3,}|_{3,})\s*")
_FENCE = re.compile(r"\s*```[\w+-]*\s*")
# 行内代码优先：代码里的 ** 不再当作粗体。粗体两端不能是 *，避免把遮蔽后的 *** 当成标记。
# 只转 http(s) 链接，其他协议（file:// 等）按原文显示
_INLINE = re.compile(r"`([^`\n]+)`|\*\*(?=[^\s*])(.+?)(?<=[^\s*])\*\*"
                     # 链接文字不含 [：长串 [ 里每次尝试只扫到下一个 [，耗时保持线性
                     r"|\[([^\[\]\n]+)\]\((https?://[^\s)]+)\)")


def to_html(text):
    """返回转义后的 HTML。"""
    lines, code = [], None  # code 非 None 时正处在代码块里，收集原文
    for line in text.split("\n"):
        if _FENCE.fullmatch(line):
            if code is None:
                code = []
            else:
                lines.append(f"<pre>{_esc(chr(10).join(code))}</pre>")
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if _RULE.fullmatch(line):
            continue
        heading = _HEADING.fullmatch(line)
        bullet = _BULLET.fullmatch(line)
        if heading:
            title = _heading_text(heading.group(1))
            line = f"<b>{_inline(title, bold=False)}</b>" if title else ""
        elif bullet:
            line = f"{bullet.group(1)}• {_inline(bullet.group(2))}"
        else:
            line = _inline(line)
        # 去掉分隔线后，前后的空行合并为一行
        if not line.strip() and lines and not lines[-1].strip():
            continue
        lines.append(line)
    if code is not None:
        # 截断切掉了结尾的 ```：剩下的内容仍按代码块显示，并补上闭合标签
        lines.append(f"<pre>{_esc(chr(10).join(code))}</pre>")
    return "\n".join(lines)


def _heading_text(text):
    """去掉标题结尾的闭合 #：只有前面是空白时才算闭合标记（C# 里的 # 保留）。

    用字符串操作而不是正则，长串 # 时耗时保持线性。
    """
    text = text.rstrip()
    stripped = text.rstrip("#")
    if stripped != text and (not stripped or stripped[-1].isspace()):
        text = stripped.rstrip()
    return text


def _inline(text, bold=True):
    """转换一行内的代码、粗体与链接；bold=False 时去掉粗体标记（外层已是粗体，不再嵌套）。"""
    out, pos = [], 0
    for m in _INLINE.finditer(text):
        out.append(_esc(text[pos:m.start()]))
        code, inner, label, url = m.groups()
        if code is not None:
            out.append(f"<code>{_esc(code)}</code>")
        elif inner is not None:
            out.append(f"<b>{_esc(inner)}</b>" if bold else _esc(inner))
        else:
            out.append(f'<a href="{html.escape(url, quote=True)}">{_esc(label)}</a>')
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


_TAG = re.compile(r"<[^>]+>")


def to_plain(text):
    """去掉 Markdown 标记的纯文本：与 to_html 走同一套转换，再去掉标签、还原转义。"""
    return html.unescape(_TAG.sub("", to_html(text)))


def _esc(text):
    return html.escape(text, quote=False)
