"""把回合摘要里的 Markdown 转成 Telegram HTML（parse_mode=HTML 支持的子集）。

输入是已遮蔽、已截断的原文，输出可直接放进引用块。Telegram 没有标题和列表格式，
标题转成整行粗体、无序列表转成 •；不认识的写法按原样转义。

嵌套遵守 Telegram 文档：粗体与链接可以互相包含，code / pre 不能放进其他格式，
所以粗体、链接里的行内代码去掉反引号按普通文字显示。
"""
from __future__ import annotations

import html
import re

_HEADING = re.compile(r"#{1,6}\s+(.*)")
_BULLET = re.compile(r"(\s*)[-*+]\s+(.*)")
# 分隔线不含 ***：遮蔽后的值整行就是 ***，不能当成分隔线删掉
_RULE = re.compile(r"\s*(?:-{3,}|_{3,})\s*")
_FENCE = re.compile(r"\s*```[\w+-]*\s*")
# 行内代码优先：代码里的 ** 不再当作粗体。
# 粗体：两端不能是 *（遮蔽后的 *** 不当作标记）；内容不含 **，每次尝试只扫到下一个 **，耗时保持线性。
# 链接：只转 http(s)，其他协议（file:// 等）按原文显示；文字不含 [，理由同上（QOS-001）
_INLINE = re.compile(r"`([^`\n]+)`"
                     r"|\*\*(?=[^\s*])((?:[^*\n]|\*(?!\*))+?)(?<=[^\s*])\*\*"
                     r"|\[([^\[\]\n]+)\]\((https?://[^\s)]+)\)")
_TAG = re.compile(r"<[^>]+>")
_LINK_TAG = re.compile(r'<a href="([^"]*)">(.*?)</a>')


def to_html(text):
    """返回转义后的 HTML。"""
    lines, code_lines = [], None  # code_lines 非 None 时正处在代码块里，收集原文
    for line in text.split("\n"):
        if _FENCE.fullmatch(line):
            if code_lines is None:
                code_lines = []
            else:
                lines.append(_pre(code_lines))
                code_lines = None
            continue
        if code_lines is not None:
            code_lines.append(line)
            continue
        if _RULE.fullmatch(line):
            continue
        heading = _HEADING.fullmatch(line)
        bullet = _BULLET.fullmatch(line)
        if heading:
            title = _heading_text(heading.group(1))
            line = f"<b>{_inline(title, inside={'b'})}</b>" if title else ""
        elif bullet:
            line = f"{bullet.group(1)}• {_inline(bullet.group(2))}"
        else:
            line = _inline(line)
        # 去掉分隔线后，前后的空行合并为一行
        if not line.strip() and lines and not lines[-1].strip():
            continue
        lines.append(line)
    if code_lines is not None:
        # 截断切掉了结尾的 ```：剩下的内容仍按代码块显示，并补上闭合标签
        lines.append(_pre(code_lines))
    return "\n".join(lines)


def to_plain(text):
    """去掉 Markdown 标记的纯文本：与 to_html 走同一套转换，链接写成「文字 (URL)」，再去掉标签。"""
    converted = _LINK_TAG.sub(lambda m: f"{m.group(2)} ({m.group(1)})", to_html(text))
    return html.unescape(_TAG.sub("", converted))


def _pre(code_lines):
    return "<pre>" + _esc("\n".join(code_lines)) + "</pre>"


def _heading_text(text):
    """去掉标题结尾的闭合 #：只有前面是空白时才算闭合标记（C# 里的 # 保留）。

    用字符串操作而不是正则，长串 # 时耗时保持线性。
    """
    text = text.rstrip()
    stripped = text.rstrip("#")
    if stripped != text and (not stripped or stripped[-1].isspace()):
        text = stripped.rstrip()
    return text


def _inline(text, inside=frozenset()):
    """转换一行内的代码、粗体与链接。

    inside 是外层已有的格式（"b" 粗体、"a" 链接）：已在粗体里就只保留内容，
    已在链接里就不再套链接；在任何格式里，行内代码都去掉反引号。
    """
    out, pos = [], 0
    for m in _INLINE.finditer(text):
        out.append(_esc(text[pos:m.start()]))
        code, bold, label, url = m.groups()
        if code is not None:
            out.append(_esc(code) if inside else f"<code>{_esc(code)}</code>")
        elif bold is not None:
            content = _inline(bold, inside | {"b"})
            out.append(content if "b" in inside else f"<b>{content}</b>")
        elif "a" in inside:
            out.append(_inline(label, inside))
        else:
            out.append(f'<a href="{html.escape(url, quote=True)}">{_inline(label, inside | {"a"})}</a>')
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


def _esc(text):
    return html.escape(text, quote=False)
