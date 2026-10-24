"""回合摘要里的 Markdown 转成 Telegram HTML。

经 process 走完整链路，断言 Telegram 收到的请求体：标签只在需要时检查，
其余用解析后的可见文本比较，与 test_layout 的写法一致。
"""
from __future__ import annotations

import pytest

from conftest import process, telegram_channel, visible

pytestmark = pytest.mark.usefixtures("hostname")


def _body(env, tmp_path, message, agent="claude"):
    """发送一条回合完成通知，返回 (请求体 text, 引用块内 HTML)。"""
    channel = telegram_channel()
    payload = {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e", "cwd": str(tmp_path / "p"),
               "last_assistant_message": message}
    process(agent, payload, env, channels=[channel])
    [request] = channel.opener.requests
    text = request.body["text"]
    start = text.index("<blockquote expandable>") + len("<blockquote expandable>")
    return text, text[start:text.rindex("</blockquote>")]


def test_bold_and_inline_code(env, tmp_path):
    _, quote = _body(env, tmp_path, "**粗体** 和 `main` 分支")
    assert quote == "<b>粗体</b> 和 <code>main</code> 分支"


def test_headings_become_bold_lines(env, tmp_path):
    # Telegram 没有标题格式：# 到 ###### 都转成整行粗体，去掉井号
    _, quote = _body(env, tmp_path, "## 🧹 删掉了什么\n正文\n### 小节 ###\n# C#")
    # 结尾的 # 前面有空白时才算闭合标记，C# 里的 # 保留
    assert quote == "<b>🧹 删掉了什么</b>\n正文\n<b>小节</b>\n<b>C#</b>"


def test_lists_become_bullets_and_rules_are_dropped(env, tmp_path):
    # 无序列表转成 •，保留缩进；有序列表保持原样；分隔线整行去掉，前后空行合并为一行
    message = "- **本地分支**：a\n  - 子项\n* 星号项\n1. 第一步\n\n---\n\n结尾"
    _, quote = _body(env, tmp_path, message)
    assert quote == ("• <b>本地分支</b>：a\n  • 子项\n• 星号项\n1. 第一步\n\n结尾")


def test_fenced_code_block_becomes_pre(env, tmp_path):
    # 代码块里的内容原样等宽显示，不再转换 ** 或列表
    message = "前文\n```bash\ngit branch -d **x**\n- 不是列表 <tag>\n```\n后文"
    _, quote = _body(env, tmp_path, message)
    assert quote == "前文\n<pre>git branch -d **x**\n- 不是列表 &lt;tag&gt;</pre>\n后文"


def test_unclosed_code_block_after_truncation_still_closes_pre(env, tmp_path):
    # 截断可能切掉结尾的 ```；剩下的内容仍按代码块显示，标签必须闭合
    _, quote = _body(env, tmp_path, "说明\n```\nline 1\nline 2")
    assert quote == "说明\n<pre>line 1\nline 2</pre>"


def test_links_keep_text_and_url(env, tmp_path):
    # 只转 http(s) 链接；链接文字里的特殊字符照常转义，URL 里的引号转义后放进属性
    _, quote = _body(env, tmp_path, '见 [PR #16](https://github.com/x/y/pull/16?a=1&b="2") 和 [本地](file:///etc)')
    assert quote == ('见 <a href="https://github.com/x/y/pull/16?a=1&amp;b=&quot;2&quot;">PR #16</a>'
                     " 和 [本地](file:///etc)")


def test_plain_fallback_strips_markdown_markers(env, tmp_path):
    # 纯文本回退（HTML 被拒）时显示的是去掉标签的内容，不能再出现 Markdown 标记
    from conftest import http_error
    channel = telegram_channel([http_error(400, "Bad Request: can't parse entities")])
    payload = {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e", "cwd": str(tmp_path / "p"),
               "last_assistant_message": "## 标题\n- **粗体** `code`\n```\nx\n```"}
    process("claude", payload, env, channels=[channel])
    plain = channel.opener.requests[1].body["text"]
    assert "parse_mode" not in channel.opener.requests[1].body
    assert plain.split("\n")[2:] == ["标题", "• 粗体 code", "x"]


def test_redaction_mask_line_is_not_a_rule(env, tmp_path):
    # 遮蔽后整行可能就是 ***，不能当成分隔线删掉
    _, quote = _body(env, tmp_path, "密钥：\n***\n结尾")
    assert quote == "密钥：\n***\n结尾"


def test_body_of_only_rules_has_no_empty_quote(env, tmp_path):
    # 正文转换后为空时不发空引用块
    channel = telegram_channel()
    payload = {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e", "cwd": str(tmp_path / "p"),
               "last_assistant_message": "---\n\n---"}
    process("claude", payload, env, channels=[channel])
    [text] = channel.opener.texts()
    assert "blockquote" not in text and visible(text).split("\n") == ["✅ p @ box", "回合完成 · Claude · 1a2b3c4d"]


@pytest.mark.parametrize("text", [
    "[" * 18000,                      # 只有左方括号，链接规则不能每个位置都扫到行尾
    "**" * 9000,
    "`" * 18000,
    "[a](" * 4500,
    "```\n" * 4500,
    "# a" + "#" * 18000 + "x",        # 标题后面跟一长串 #，结尾的 # 不能反复试探切分点
], ids=["bracket-run", "star-run", "backtick-run", "link-prefix-run", "fence-run", "heading-hash-run"])
def test_conversion_is_fast_on_long_input(text):
    # 与遮蔽的性能测试相同：约 5 倍于摘要上限 3500，线性耗时只有几毫秒，二次方回溯会到秒级
    import time
    from agent_notify.markdown import to_html
    start = time.perf_counter()
    to_html(text)
    assert time.perf_counter() - start < 0.2


def test_converted_body_still_fits_4096(env, tmp_path):
    # 标签会占用长度：正文全是粗体和代码时，请求 text 仍不超过 4096 个 UTF-16 码元
    from conftest import with_config
    with_config(env, tmp_path, summary_max_chars=3500)
    text, _ = _body(env, tmp_path, "**a** `b` " * 400)
    assert len(text.encode("utf-16-le")) // 2 <= 4096
    assert visible(text).split("\n")[0] == "✅ p @ box"
