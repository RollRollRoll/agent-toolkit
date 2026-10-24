"""敏感内容遮蔽（REQ-005、NEG-001）：规则表单元测试 + 主 seam 端到端测试。"""
from __future__ import annotations

import json
import time

import pytest

from agent_notify.redaction import redact
from conftest import process, telegram_channel, visible

CONFIGURED = "123:CONFIGURED-RAW"  # 当前配置的 bot token 原文（不是 Telegram 形态）
TG = "1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsawZ"  # 形如 Telegram bot token（35 位）

# 规则表：(用例名, 输入, 期望输出)；按 REQ-005 的规则顺序，每条规则至少一个命中、一个不命中
CASES = [
    # bot token 原文
    ("raw-token-hit", f"bot{CONFIGURED} fail", "bot*** fail"),
    ("raw-token-miss", "bot123:OTHER fail", "bot123:OTHER fail"),
    # Authorization 类头部
    ("auth-bearer", 'curl -H "Authorization: Bearer abc123" https://x',
     'curl -H "Authorization: Bearer ***" https://x'),
    ("auth-basic-proxy", "proxy-authorization: basic dXNlcjpwYXNz",
     "proxy-authorization: basic ***"),
    ("auth-token", "AUTHORIZATION: Token tok_99", "AUTHORIZATION: Token ***"),
    ("auth-bearer-double-quoted", 'Authorization: Bearer "abc 123"', 'Authorization: Bearer "***"'),
    ("auth-bearer-single-quoted", "authorization=bearer 'xyz'", "authorization=bearer '***'"),
    ("auth-miss", "Authorization required; bearer of news",
     "Authorization required; bearer of news"),
    # Telegram token 形态（数字:35 位）
    ("tg-shape-hit", f"GET /bot{TG}/getMe", "GET /bot***/getMe"),
    ("tg-shape-miss", "at 12:30 build 42:abc", "at 12:30 build 42:abc"),
    # 常见密钥前缀
    ("sk-hit", "key sk-proj-AbCdEf0123456789xyz end", "key sk-*** end"),
    ("sk-miss", "pip install sk-learn", "pip install sk-learn"),
    ("gh-hit", "ghp_AbCdEfGhIjKlMnOpQrSt1234 github_pat_11ABCDEFG0123456789abc",
     "ghp_*** github_pat_***"),
    ("gh-miss", "ghp_short gho_x", "ghp_short gho_x"),
    ("slack-hit", "xoxb-1234567890-abcdefghij", "xoxb-***"),
    ("slack-miss", "xoxc-abcdef123 xoxb-", "xoxc-abcdef123 xoxb-"),
    ("aws-hit", "AKIAIOSFODNN7EXAMPLE and asiaABCDEFGHIJKLMNOP", "AKIA*** and asia***"),
    ("aws-miss", "ASIAN AKIA123", "ASIAN AKIA123"),
    ("jwt-hit", "t=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.SflKxwRJSMeKKF2QT4fwpM ok", "t=*** ok"),
    ("jwt-miss", "eyJhbGciOiJIUzI1NiJ9 only header", "eyJhbGciOiJIUzI1NiJ9 only header"),
    # 敏感键名的键值（含引号包裹、JSON、查询串）
    ("kv-env", "DB_PASSWORD=hunter2 next", "DB_PASSWORD=*** next"),
    ("kv-json", '{"api_key": "abc def", "n": 1}', '{"api_key": "***", "n": 1}'),
    ("kv-single-quoted", "client_secret: 'xyz'", "client_secret: '***'"),
    ("kv-query", "GET /cb?access_token=abc&x=1", "GET /cb?access_token=***&x=1"),
    ("kv-variants", "PWD=a passwd:b Api-Key=c private_key=d ACCESS_KEY=e apikey=f",
     "PWD=*** passwd:*** Api-Key=*** private_key=*** ACCESS_KEY=*** apikey=***"),
    ("kv-miss", "password reset link; token count 5; docker -v $(pwd):/app",
     "password reset link; token count 5; docker -v $(pwd):/app"),
    # --password 参数
    ("flag-space", "psql --password s3cret -U app", "psql --password *** -U app"),
    ("flag-eq", "tool --PASSWORD=s3cret", "tool --PASSWORD=***"),
    ("flag-miss", "docker login --password-stdin", "docker login --password-stdin"),
    # 仅 mysql 系列命令中的 -p<值>
    ("mysql-hit", "mysql -u root -ps3cret db", "mysql -u root -p*** db"),
    ("mysqldump-hit", "cd x && mysqldump -pAbc db > d.sql", "cd x && mysqldump -p*** db > d.sql"),
    ("mysqladmin-hit", "MYSQLADMIN -pX status", "MYSQLADMIN -p*** status"),
    ("mysql-miss", "mysql -P3306 -p db && mkdir -p build && psql -p 5432",
     "mysql -P3306 -p db && mkdir -p build && psql -p 5432"),
    ("mysql-other-segment", "mysql -h db; tar -pxf a.tar", "mysql -h db; tar -pxf a.tar"),
    # 同一段命令里的参数含 mysql 子串时，仍要遮蔽其后的 -p
    ("mysql-host-named-mysql", "mysql -h mysqlhost -psecret db", "mysql -h mysqlhost -p*** db"),
    ("mysql-env-var", 'mysql -u $MYSQL_USER -p"$PW" db', "mysql -u $MYSQL_USER -p*** db"),
    ("mysql-socket-path", "mysql --socket=/var/run/mysqld/m.sock -psecret db",
     "mysql --socket=/var/run/mysqld/m.sock -p*** db"),
    ("mysql-twice", "mysql -h a mysql -pS3c db", "mysql -h a mysql -p*** db"),
    # URL 中的密码
    ("url-hit", "postgres://app:s3cr3t@db/x", "postgres://app:***@db/x"),
    ("url-after-digit", "1https://u:pw@h/x", "1https://u:***@h/x"),
    # 用户名含敏感键名时仍按 URL 规则处理，保留主机和路径
    ("url-token-user", "https://x-access-token:ghs_abc@github.com/a",
     "https://x-access-token:***@github.com/a"),
    ("kv-max-tokens", "max_tokens=100", "max_tokens=***"),
    ("url-miss", "https://host:8080/p and redis://app@db", "https://host:8080/p and redis://app@db"),
    # 不误伤常见命令（SCN-005-C）
    ("scn-005-c", "mkdir -p build && psql -p 5432", "mkdir -p build && psql -p 5432"),
]


@pytest.mark.parametrize("text,expected", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_redaction_rules(text, expected):
    assert redact(text, token=CONFIGURED) == expected


@pytest.mark.parametrize("text", [
    "x" * 18000,                      # 一整段没有空白的单词字符（长哈希、base64、压缩输出）
    "abc_" * 4500,
    "中" * 18000,
    "a.b-" * 4500,
    "x" * 18000 + "://",              # 只有末尾像 URL
    "token" * 3600,                   # 长串里反复出现敏感键名
    "mysql " * 3000,                  # 一段命令里反复出现 mysql 但没有 -p
], ids=["word-run", "underscore-run", "cjk-run", "dot-dash-run", "url-tail", "keyword-run", "mysql-run"])
def test_redaction_is_fast_on_long_input(text):
    # QOS-001：遮蔽在 hook 主进程同步执行，且在截断之前（DEC-001），输入是未截断的原文。
    # 取约 5 倍于摘要上限 3500 的长度：线性耗时只有几毫秒，二次方回溯会到秒级，
    # 阈值放宽到 200ms，慢机器上也不会误报
    start = time.perf_counter()
    redact(text, token=CONFIGURED)
    assert time.perf_counter() - start < 0.2


def test_redaction_failure_masks_whole_field():
    assert redact(None) == "***"


class _BrokenRule:
    """只在遇到特定输入时出错的规则：真实的正则异常也取决于输入，日志行本身仍能正常遮蔽。"""

    def sub(self, repl, text):
        if "SECRET-XYZ" in text:
            raise RuntimeError("regex blew up")
        return text


def test_redaction_error_is_logged_and_field_sent_as_mask(env, tmp_path, monkeypatch):
    # spec #2 §3.6：遮蔽正则异常时该字段整段替换为 ***，通知照常发送，并记录错误
    monkeypatch.setattr("agent_notify.redaction._RULES", [(_BrokenRule(), "")])
    ch = telegram_channel()
    process("claude", _stop(tmp_path, "原始正文 SECRET-XYZ"), env, channels=[ch])
    [text] = ch.opener.texts()
    assert visible(text).endswith("\n***") and "SECRET-XYZ" not in text
    lines = (tmp_path / "notify.log").read_text(encoding="utf-8").splitlines()
    errors = [l for l in lines if " error=redaction" in l]
    assert len(errors) == 1
    assert " level=error " in errors[0] and " result=fail " in errors[0]
    assert "SECRET-XYZ" not in "\n".join(lines)


def _permission(tmp_path, command):
    return {"hook_event_name": "PermissionRequest", "session_id": "perm12345",
            "cwd": str(tmp_path), "tool_name": "Bash", "tool_input": {"command": command}}


def _bodies(channel):
    return [json.dumps(r.body, ensure_ascii=False) for r in channel.opener.requests]


def test_bearer_token_in_command_is_masked(env, tmp_path):
    ch = telegram_channel()
    process("codex", _permission(tmp_path, 'curl -H "Authorization: Bearer abc123" https://x'),
            env, channels=[ch])
    assert 'Authorization: Bearer ***' in ch.opener.texts()[0]
    assert all("abc123" not in body for body in _bodies(ch))


def _stop(tmp_path, msg, **extra):
    return {"hook_event_name": "Stop", "session_id": "stop12345", "cwd": str(tmp_path),
            "last_assistant_message": msg, **extra}


def test_key_value_and_url_password_masked_in_summary_and_title(env, tmp_path):
    ch = telegram_channel()
    payload = _stop(tmp_path, "设置 DB_PASSWORD=hunter2，连接 postgres://app:s3cr3t@db/x",
                    session_title="调试 api_key=topsecret")
    process("claude", payload, env, channels=[ch])
    text = ch.opener.texts()[0]
    assert "DB_PASSWORD=***" in text and "postgres://app:***@db/x" in text
    assert "api_key=***" in text
    assert all(s not in body for body in _bodies(ch) for s in ("hunter2", "s3cr3t", "topsecret"))


def test_common_commands_shown_verbatim(env, tmp_path):
    ch = telegram_channel()
    process("codex", _permission(tmp_path, "mkdir -p build && psql -p 5432"), env, channels=[ch])
    assert visible(ch.opener.texts()[0]).endswith("Bash: mkdir -p build && psql -p 5432")


def test_credential_across_truncation_point_leaves_no_fragment(env, tmp_path):
    # 截断位置设为 300 字：密钥从第 290 字开始，先截断会留下规则匹配不到的半截
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"summary_max_chars": 300}), encoding="utf-8")
    env["AGENT_NOTIFY_CONFIG"] = str(cfg)
    key = "sk-proj-" + "Q7w" * 10
    ch = telegram_channel()
    process("claude", _stop(tmp_path, "x" * 289 + " " + key + " 结尾"), env, channels=[ch])
    text = ch.opener.texts()[0]
    assert "sk-***" in text
    assert all("Q7w" not in body for body in _bodies(ch))


def test_secrets_absent_from_request_body_and_log(env, tmp_path):
    from conftest import TOKEN
    marker = "MARKER-7f3a9c"
    secrets = (TOKEN, "abc123bearer", marker)
    leaky = f"token={TOKEN} Authorization: Bearer abc123bearer password={marker}"
    # 渠道错误信息回显了原文，检验日志写入前同样经过遮蔽
    from conftest import FakeChannel
    broken = FakeChannel(error=RuntimeError(f"Bad Request: {leaky}"))
    ch = telegram_channel()
    process("claude", _stop(tmp_path, leaky), env, channels=[broken, ch])
    log = (tmp_path / "notify.log").read_text()
    assert "Bad Request" in log and "Bearer ***" in log and "password=***" in log
    for secret in secrets:
        assert secret not in log
        assert all(secret not in body for body in _bodies(ch))
