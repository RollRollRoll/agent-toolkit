"""回合摘要里的 Markdown 转成 Telegram HTML。

经 process 走完整链路：引用块内的 HTML 直接比较，布局行用解析后的可见文本比较，
与 test_layout 的写法一致。只有回合完成 / 回合结束的正文（Agent 的回复）按 Markdown 排版。
"""
from __future__ import annotations

import time

import pytest

from agent_notify.markdown import to_html
from conftest import http_error, quote_html, send_once, visible, with_config

pytestmark = pytest.mark.usefixtures("hostname")


def _stop(tmp_path, message):
    return {"hook_event_name": "Stop", "session_id": "1a2b3c4d5e", "cwd": str(tmp_path / "p"),
            "last_assistant_message": message}


def _summary_quote(env, tmp_path, message):
    """发送一条回合完成通知，返回引用块内的 HTML。"""
    [body] = send_once("claude", _stop(tmp_path, message), env)
    return quote_html(body["text"])


def test_bold_and_inline_code(env, tmp_path):
    assert _summary_quote(env, tmp_path, "**粗体** 和 `main` 分支") == "<b>粗体</b> 和 <code>main</code> 分支"


def test_headings_become_bold_lines(env, tmp_path):
    # Telegram 没有标题格式：# 到 ###### 都转成整行粗体，去掉井号；
    # 结尾的 # 前面有空白时才算闭合标记，C# 里的 # 保留
    quote = _summary_quote(env, tmp_path, "## 🧹 删掉了什么\n正文\n### 小节 ###\n# C#")
    assert quote == "<b>🧹 删掉了什么</b>\n正文\n<b>小节</b>\n<b>C#</b>"

def test_lists_become_bullets_and_rules_are_dropped(env, tmp_path):
    # 无序列表转成 •，保留缩进；有序列表保持原样；分隔线整行去掉，前后空行合并为一行
    message = "- **本地分支**：a\n  - 子项\n* 星号项\n1. 第一步\n\n---\n\n结尾"
    quote = _summary_quote(env, tmp_path, message)
    assert quote == "• <b>本地分支</b>：a\n  • 子项\n• 星号项\n1. 第一步\n\n结尾"


def test_fenced_code_block_becomes_pre(env, tmp_path):
    # 代码块里的内容原样等宽显示，不再转换 ** 或列表
    message = "前文\n```bash\ngit branch -d **x**\n- 不是列表 <tag>\n```\n后文"
    quote = _summary_quote(env, tmp_path, message)
    assert quote == "前文\n<pre>git branch -d **x**\n- 不是列表 &lt;tag&gt;</pre>\n后文"


def test_unclosed_code_block_after_truncation_still_closes_pre(env, tmp_path):
    # 截断可能切掉结尾的 ```；剩下的内容仍按代码块显示，标签必须闭合
    assert _summary_quote(env, tmp_path, "说明\n```\nline 1\nline 2") == "说明\n<pre>line 1\nline 2</pre>"


def test_links_keep_text_and_url(env, tmp_path):
    # 只转 http(s) 链接；链接文字里的特殊字符照常转义，URL 里的引号转义后放进属性
    quote = _summary_quote(env, tmp_path,
                           '见 [PR #16](https://github.com/x/y/pull/16?a=1&b="2") 和 [本地](file:///etc)')
    assert quote == ('见 <a href="https://github.com/x/y/pull/16?a=1&amp;b=&quot;2&quot;">PR #16</a>'
                     " 和 [本地](file:///etc)")


def test_bold_and_link_nest_but_code_inside_them_is_plain(env, tmp_path):
    # Telegram 允许粗体与链接互相嵌套；粗体、链接里不能再放 code，反引号去掉按普通文字显示
    quote = _summary_quote(env, tmp_path, "**[x](https://e.com)** [**y**](https://e.com) **a `b` c** [d`e`](https://e.com)")
    assert quote == ('<b><a href="https://e.com">x</a></b> <a href="https://e.com"><b>y</b></a>'
                     ' <b>a b c</b> <a href="https://e.com">de</a>')


def test_plain_fallback_strips_markers_and_keeps_urls(env, tmp_path):
    # 纯文本回退（HTML 被拒）时去掉 Markdown 标记；链接写成「文字 (URL)」，地址不能丢
    message = "## 标题\n- **粗体** `code` [文档](https://x.io/p)\n```\nx\n```"
    _, plain = send_once("claude", _stop(tmp_path, message), env,
                         outcomes=[http_error(400, "Bad Request: can't parse entities")])
    assert "parse_mode" not in plain
    assert plain["text"].split("\n\n", 2)[2].split("\n") == ["标题", "• 粗体 code 文档 (https://x.io/p)", "x"]


def test_redaction_mask_line_is_not_a_rule(env, tmp_path):
    # 遮蔽后整行可能就是 ***，不能当成分隔线删掉
    assert _summary_quote(env, tmp_path, "密钥：\n***\n结尾") == "密钥：\n***\n结尾"


def test_body_of_only_rules_has_no_empty_quote(env, tmp_path):
    # 正文转换后为空时不发空引用块
    [body] = send_once("claude", _stop(tmp_path, "---\n\n---"), env)
    assert quote_html(body["text"]) is None
    assert visible(body["text"]).split("\n") == [
        "✅ 回合完成 · p @ box", "", "Agent：Claude", "会话：1a2b3c4d"]


@pytest.mark.parametrize("command", [
    "cd app\n# 清理构建\nrm -rf build",
    "- x **y** `z` [a](https://e.com)",
], ids=["comment", "markers"])
def test_command_preview_is_shown_verbatim(env, tmp_path, command):
    # 授权的命令预览不是 Markdown：# 注释、- 开头、** 和反引号都原样显示
    payload = {"hook_event_name": "PermissionRequest", "session_id": "bbbbbbbb1", "cwd": str(tmp_path / "p"),
               "tool_name": "Bash", "tool_input": {"command": command}}
    [body] = send_once("codex", payload, env)
    assert visible(quote_html(body["text"])) == f"Bash: {command}"


def test_error_details_are_shown_verbatim(env, tmp_path):
    # 错误详情是机器生成的字符串，不按 Markdown 排版
    payload = {"hook_event_name": "StopFailure", "session_id": "eeeeeeee1", "cwd": str(tmp_path / "p"),
               "error": "unknown", "error_details": "## 500 **upstream** - retry"}
    [body] = send_once("claude", payload, env)
    assert visible(quote_html(body["text"])) == "## 500 **upstream** - retry"


@pytest.mark.parametrize("text", [
    "[" * 18000,                      # 只有左方括号，链接规则不能每个位置都扫到行尾
    "**" * 9000,
    "`" * 18000,
    "[a](" * 4500,
    "```\n" * 4500,
    "# a" + "#" * 18000 + "x",        # 标题后面跟一长串 #，结尾的 # 不能反复试探切分点
    "**[" * 6000,                     # 粗体里再找链接，不能变成嵌套回溯
    "**a " * 4500,                    # 每个 ** 后面都找不到合法的闭合，不能每次都扫到行尾
], ids=["bracket-run", "star-run", "backtick-run", "link-prefix-run", "fence-run", "heading-hash-run",
        "bold-bracket-run", "unclosed-bold-run"])
def test_conversion_is_fast_on_long_input(text):
    # 与遮蔽的性能测试相同：约 5 倍于摘要上限 3500，线性耗时只有几毫秒，二次方回溯会到秒级
    start = time.perf_counter()
    to_html(text)
    assert time.perf_counter() - start < 0.2


def test_converted_body_still_fits_4096(env, tmp_path):
    # 标签会占用长度：正文全是粗体和代码时，请求 text 仍不超过 4096 个 UTF-16 码元
    with_config(env, tmp_path, summary_max_chars=3500)
    [body] = send_once("claude", _stop(tmp_path, "**a** `b` " * 400), env)
    assert len(body["text"].encode("utf-16-le")) // 2 <= 4096
    assert visible(body["text"]).split("\n")[0] == "✅ 回合完成 · p @ box"
