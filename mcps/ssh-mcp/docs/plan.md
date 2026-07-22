# SSH MCP Foundation 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 0→1 实现 SSH MCP 服务器，覆盖 Notion 17 模块全部能力，通过 stdio + Streamable HTTP 双 transport 暴露 Tools/Resources/Prompts，所有动作经 PolicyEngine 闸门 + 审计 + 高危审批闭环。

**Architecture:** 洋葱分层 Transport → Dispatcher → PolicyEngine → OperationHandler → Backends；MCP SDK 提供协议层，asyncssh 提供受控连接池，所有工具走统一 ToolContract（9 字段）+ ToolResult envelope（9 字段）；JSONL 审计 + SQLite approval/task store；4 风险等级 + 5 features 默认全关。

**Tech Stack:** Python 3.11+ / `mcp` SDK / `asyncssh` / `aiosqlite` / `pydantic` / `pyyaml` / `httpx` / `anyio` / `pytest` / `pytest-asyncio` / `ruff` / `mypy --strict` / `uv`。

**依赖顺序:** 工程化 → 配置 → 工具契约 → SSH pool → PolicyEngine → 审计 → 审批 → MCP 入口 → 17 业务模块 → CLI → 发布。

**前置约定:**
- 所有源码位于 `src/ssh_mcp/`，所有测试位于 `tests/{unit,integration,e2e}/`。
- 测试先行：每 Task 先写失败用例，再写最小实现，最后跑通并提交。
- `asyncio_mode=auto`，所有协程函数无需手动 `@pytest.mark.asyncio`。
- 提交粒度：每完成一个 Task 提交一次，message 用 `<scope>: <action>`，如 `policy: add deny-stage rule stack`。
- 引用：本计划反复提到的 `design.md` 与 `specs/<capability>/spec.md` 在 `openspec/changes/ssh-mcp-foundation/` 下。

---

## Task 1: 工程化基础

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `src/ssh_mcp/__init__.py` 与 13 个子包 `__init__.py`（transport/server/policy/operations/ssh/credentials/audit/approval/store/resources/prompts/config/utils）
- Create: `tests/conftest.py`、`tests/{unit,integration,e2e,fixtures,support}/__init__.py`
- Create: `pyproject.toml`（ruff + mypy strict 段）
- Create: `.github/workflows/ci.yml`
- Create: `runbooks/{network-debug,nginx-debug,postgres-debug,disk-full,firewall-debug}.md`

- [ ] **Step 1: 写 `pyproject.toml`**

```toml
[project]
name = "ssh-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "mcp>=1.0",
  "asyncssh>=2.16",
  "aiosqlite>=0.20",
  "pydantic>=2.7",
  "pyyaml>=6.0",
  "httpx>=0.27",
  "anyio>=4.4",
  "python-ulid>=2.7",
  "starlette>=0.37",
  "uvicorn>=0.30",
  "bashlex>=0.18",
]

[project.optional-dependencies]
test = [
  "pytest>=8", "pytest-asyncio>=0.23", "pytest-cov>=5",
  "ruff>=0.5", "mypy>=1.10", "types-PyYAML>=6.0",
  "pre-commit>=3.7",
]

[project.scripts]
ssh-mcp = "ssh_mcp.cli:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
[tool.ruff.lint]
select = ["E","F","I","B","UP","SIM"]

[tool.mypy]
strict = true
python_version = "3.11"
```

- [ ] **Step 2: 锁定依赖**

Run: `uv sync --extra test`
Expected: 生成 `uv.lock`，无错误。

- [ ] **Step 3: 建包骨架与测试根**

```bash
mkdir -p src/ssh_mcp/{transport,server,policy,operations,ssh,credentials,audit,approval,store,resources,prompts,config,utils}
for d in transport server policy operations ssh credentials audit approval store resources prompts config utils; do
  printf '' > src/ssh_mcp/$d/__init__.py
done
printf '' > src/ssh_mcp/__init__.py
mkdir -p tests/{unit,integration,e2e,fixtures,support}
for d in unit integration e2e fixtures support; do printf '' > tests/$d/__init__.py; done
```

写最小 `tests/conftest.py`：

```python
from __future__ import annotations
import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"
```

- [ ] **Step 4: 写一个冒烟测试验证测试链路**

`tests/unit/test_smoke.py`：

```python
from ssh_mcp import __name__ as pkg

def test_package_importable():
    assert pkg == "ssh_mcp"
```

Run: `uv run pytest tests/unit/test_smoke.py -v`
Expected: PASS。

- [ ] **Step 5: 配 ruff + mypy + pre-commit + CI**

- 增 `.pre-commit-config.yaml` 跑 ruff/ruff-format/mypy。
- 写 `.github/workflows/ci.yml` 三 job：`pr-checks`（ruff/mypy/unit/integration）、`nightly-e2e`（main 夜跑 docker `linuxserver/openssh-server`）。
- 写 5 份 runbook 占位（标题 + 摘要 + 步骤骨架），见 spec `mcp-resources-and-prompts` 第 16.4 节。

- [ ] **Step 6: 提交**

```bash
git add pyproject.toml uv.lock src/ tests/ .pre-commit-config.yaml .github/ runbooks/
git commit -m "chore: bootstrap python package skeleton, tooling, ci, runbooks"
```

---

## Task 2: 配置体系

**Files:**
- Create: `src/ssh_mcp/config/models.py`
- Create: `src/ssh_mcp/config/loader.py`
- Create: `src/ssh_mcp/config/snapshot.py`
- Create: `examples/config/{hosts,commands,policy,audit,server}.yaml`
- Test: `tests/unit/config/test_loader.py`

- [ ] **Step 1: 写失败测试覆盖加载顺序与 allowed_args 合并**

```python
# tests/unit/config/test_loader.py
from ssh_mcp.config.loader import load_config

def test_priority_cli_overrides_env(tmp_path, monkeypatch):
    yaml_path = tmp_path / "server.yaml"
    yaml_path.write_text("listen: ':9000'\n")
    monkeypatch.setenv("SSH_MCP_LISTEN", ":7000")
    cfg = load_config(global_dir=tmp_path, cli={"listen": ":8080"})
    assert cfg.server.listen == ":8080"

def test_strict_credentials_rejects_root(tmp_path):
    (tmp_path / "hosts.yaml").write_text("hosts:\n  vps:\n    user: root\n    host: 1.2.3.4\n")
    (tmp_path / "server.yaml").write_text("strict_credentials: true\n")
    import pytest
    with pytest.raises(ValueError, match="root"):
        load_config(global_dir=tmp_path, cli={})

def test_allowed_args_merged_into_enum(tmp_path):
    (tmp_path / "commands.yaml").write_text(
        "commands:\n  systemctl_status:\n    argv: ['systemctl','status','{name}']\n"
        "    arg_schema: {type: object, properties: {name: {type: string}}}\n"
        "    allowed_args: {name: [nginx, postgres]}\n"
    )
    cfg = load_config(global_dir=tmp_path, cli={})
    schema = cfg.commands.entries["systemctl_status"].arg_schema
    assert schema["properties"]["name"]["enum"] == ["nginx", "postgres"]
```

Run: `uv run pytest tests/unit/config/ -v`
Expected: FAIL — module missing。

- [ ] **Step 2: 写 `models.py` 五个 pydantic 模型**

照 design.md D14 字段：`HostsConfig.hosts: dict[str, HostEntry]`，`HostEntry` 含 `host/port/user/auth/key_path/password/bastion/tags/env`；`CommandsConfig.entries: dict[str, CommandSpec]`；`PolicyConfig` 含 `host_allowlist/cmd_allowlist/path_policy/risk_levels/maintenance_windows/rate_limits/features/break_glass/network_policy/task`；`AuditConfig` 含 `dir/sinks/redact_patterns`；`ServerConfig` 含 `listen/bearer_token/strict_credentials/backup_retention_days/state_dir`。

环境变量 → 字段映射（`_apply_env` 按此表做精确映射，不做通配 prefix strip）：

| 环境变量 | 目标字段 | 说明 |
|---|---|---|
| `SSH_MCP_CONFIG_DIR` | CLI `--config-dir` | loader 的 `global_dir` 参数，不入模型 |
| `SSH_MCP_AUDIT_DIR` | `AuditConfig.dir` | 审计 JSONL 输出目录 |
| `SSH_MCP_STATE_DIR` | `ServerConfig.state_dir` | state.db + pidfile 所在目录 |
| `SSH_MCP_LISTEN` | `ServerConfig.listen` | HTTP 监听地址 |
| `SSH_MCP_BEARER_TOKEN` | `ServerConfig.bearer_token` | HTTP 鉴权 token |

`ServerConfig.state_dir` 默认 `~/.ssh-mcp/`；`AuditConfig.dir` 默认 `~/.ssh-mcp/audit/`。

所有模型 `model_config = ConfigDict(extra="forbid", frozen=True)`。

- [ ] **Step 3: 写 `loader.py`**

```python
# src/ssh_mcp/config/loader.py
from pathlib import Path
import os, copy, yaml
from .models import HostsConfig, CommandsConfig, PolicyConfig, AuditConfig, ServerConfig, RootConfig

_ENV_MAP: dict[str, tuple[str, str]] = {
    # env_var → (config_section, field)
    "SSH_MCP_AUDIT_DIR":    ("audit", "dir"),
    "SSH_MCP_STATE_DIR":    ("server", "state_dir"),
    "SSH_MCP_LISTEN":       ("server", "listen"),
    "SSH_MCP_BEARER_TOKEN": ("server", "bearer_token"),
}

def _read_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text()) or {} if p.exists() else {}

def _apply_env(sections: dict[str, dict]) -> None:
    """精确映射环境变量到对应 section.field，不做通配 prefix strip。"""
    for env_key, (section, field) in _ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            sections.setdefault(section, {})[field] = val

def _merge_allowed_args(commands: dict) -> dict:
    for name, spec in commands.get("commands", {}).items():
        for arg, vals in spec.get("allowed_args", {}).items():
            spec.setdefault("arg_schema", {}).setdefault("properties", {}).setdefault(arg, {})["enum"] = list(vals)
    return commands

def load_config(*, global_dir: Path, cli: dict) -> RootConfig:
    hosts = _read_yaml(global_dir / "hosts.yaml")
    cmds  = _merge_allowed_args(_read_yaml(global_dir / "commands.yaml"))
    pol   = _read_yaml(global_dir / "policy.yaml")
    aud   = _read_yaml(global_dir / "audit.yaml")
    srv   = _read_yaml(global_dir / "server.yaml")
    # 精确 env 映射（覆盖 yaml 值）
    sections = {"audit": aud, "server": srv}
    _apply_env(sections)
    # CLI 参数最高优先级——白名单过滤，只允许 ServerConfig 字段进入 srv
    _SERVER_FIELDS = {"listen", "bearer_token", "strict_credentials", "backup_retention_days", "state_dir"}
    for k, v in cli.items():
        if k in _SERVER_FIELDS and v is not None:
            srv[k] = v
    cfg = RootConfig(
        hosts=HostsConfig(**hosts),
        commands=CommandsConfig(**cmds),
        policy=PolicyConfig(**pol),
        audit=AuditConfig(**aud),
        server=ServerConfig(**srv),
    )
    cfg.validate_invariants()  # strict_credentials + root user check
    return cfg
```

`RootConfig.validate_invariants` 在 `strict_credentials=true` 下任一 host `user=="root"` raise `ValueError`。

- [ ] **Step 4: 写 `snapshot.py`（不可变快照原子替换）**

```python
# src/ssh_mcp/config/snapshot.py
from __future__ import annotations
import threading
from .models import RootConfig

class ConfigSnapshot:
    def __init__(self, cfg: RootConfig):
        self._cfg = cfg
        self._lock = threading.RLock()
    @property
    def current(self) -> RootConfig:
        with self._lock:
            return self._cfg
    def replace(self, new: RootConfig) -> None:
        with self._lock:
            self._cfg = new
```

热重载只允许替换 `policy/hosts/commands` 三段；其它项 raise `RuntimeError("not hot-reloadable")`。

- [ ] **Step 5: 落 5 份示例 yaml 与 runbooks 引用**

写到 `examples/config/`：每份带说明注释，`commands.yaml` 至少包含 `systemctl_status` 与 `journal_tail`，`policy.yaml` 至少含 `risk_levels` 4 级声明 + 1 条 `maintenance_windows`。

- [ ] **Step 6: 跑测试 + 提交**

Run: `uv run pytest tests/unit/config/ -v`
Expected: 3 PASS。

```bash
git add src/ssh_mcp/config/ tests/unit/config/ examples/config/
git commit -m "config: add pydantic models, layered loader, immutable snapshot"
```

---

## Task 3: 工具契约与输出流水线（capability: tool-contract）

**Files:**
- Create: `src/ssh_mcp/server/contract.py`
- Create: `src/ssh_mcp/server/envelope.py`
- Create: `src/ssh_mcp/server/registry.py`
- Create: `src/ssh_mcp/server/output_pipeline.py`
- Test: `tests/unit/server/{test_contract.py,test_envelope.py,test_pipeline.py}`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/server/test_contract.py
import pytest
from ssh_mcp.server.contract import ToolContract, ToolRegistry

def _ok_contract(name: str) -> ToolContract:
    return ToolContract(
        name=name, description=f"{name} tool", input_schema={}, result_schema={},
        readonly=True, risk_default="low", timeout_default=10,
        output_limits={"max_lines": 1000, "max_bytes": 1_048_576},
        approval_required_when=None,
    )

def test_missing_field_rejects():
    with pytest.raises(ValueError, match="CONFIG_TOOL_CONTRACT_MISSING_FIELD"):
        ToolContract(name="x", description="x tool")  # 缺 7 个字段

def test_per_action_risk_dict_ok():
    c = ToolContract(
        name="manage_service", description="systemd unit management",
        input_schema={"type": "object"}, result_schema={"type": "object"},
        readonly=False,
        risk_default={"start":"medium","stop":"high","daemon_reload":"high"},
        timeout_default=30,
        output_limits={"max_lines":2000, "max_bytes": 2_097_152},
        approval_required_when="risk in {high,forbidden}",
    )
    assert c.risk_default["daemon_reload"] == "high"

def test_registry_rejects_duplicate():
    reg = ToolRegistry()
    reg.register(_ok_contract("a"))
    with pytest.raises(ValueError, match="duplicate"):
        reg.register(_ok_contract("a"))
```

```python
# tests/unit/server/test_envelope.py
from ssh_mcp.server.envelope import ToolResult

def test_envelope_top_level_fields():
    r = ToolResult(ok=True, host="h", exit_code=0, duration_ms=1, truncated=False,
                   cursor=None, summary="ok",
                   correlation_id="01HZX9T6Y5F0Q2J7M3K8B4N1AA", data={})
    d = r.model_dump()
    assert set(d) >= {"ok","host","exit_code","duration_ms","truncated","cursor","summary","correlation_id","data"}
```

```python
# tests/unit/server/test_pipeline.py
from ssh_mcp.server.output_pipeline import run_pipeline

def test_secret_redacted_in_stdout():
    out = run_pipeline(
        stdout=b"AWS_SECRET=AKIAIOSFODNN7EXAMPLE token=ghp_abcdefghijklmnopqrst",
        stderr=b"", max_lines=10, max_bytes=1_048_576, extra_patterns=[], raw=False,
    )
    assert "AKIA" not in out.stdout_text
    assert "<REDACTED>" in out.stdout_text

def test_stderr_kept_separate():
    out = run_pipeline(stdout=b"hello\n", stderr=b"warn:x\n",
                       max_lines=10, max_bytes=1_048_576, extra_patterns=[], raw=False)
    assert out.stdout_text.strip() == "hello"
    assert out.stderr_text.strip() == "warn:x"

def test_paging_cursor_by_line():
    out = run_pipeline(stdout=b"a\n" * 5000, stderr=b"",
                       max_lines=2000, max_bytes=10_000_000, extra_patterns=[], raw=False)
    assert out.truncated is True
    assert out.cursor == "line:2000"

def test_byte_truncation():
    out = run_pipeline(stdout=b"x" * 5_000_000, stderr=b"",
                       max_lines=1_000_000, max_bytes=1_048_576, extra_patterns=[], raw=False)
    assert out.truncated is True
    assert out.cursor and out.cursor.startswith("bytes:")
    assert len(out.stdout_text.encode()) <= 1_048_576

def test_binary_payload_rejected():
    # NUL byte 触发二进制识别
    out = run_pipeline(stdout=b"hello\x00\x01\x02\x03world", stderr=b"",
                       max_lines=10, max_bytes=1_048_576, extra_patterns=[], raw=False)
    assert out.binary_rejected is True
    assert out.stdout_text == ""

def test_binary_elf_header_rejected():
    # 真实 ELF magic bytes
    out = run_pipeline(stdout=b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100, stderr=b"",
                       max_lines=10, max_bytes=1_048_576, extra_patterns=[], raw=False)
    assert out.binary_rejected is True

def test_raw_skips_redaction_but_marks_audit_flag():
    out = run_pipeline(stdout=b"AKIAIOSFODNN7EXAMPLE", stderr=b"",
                       max_lines=10, max_bytes=1_048_576, extra_patterns=[], raw=True)
    assert "AKIA" in out.stdout_text  # 不脱敏
    assert out.audit_flags == {"raw": True}
```

Run: `uv run pytest tests/unit/server/ -v`
Expected: 全 FAIL。

- [ ] **Step 2: 实现 `contract.py`**

`ToolContract` 用 pydantic dataclass，9 字段全部 required；`risk_default: str | dict[str, str]`；构造时校验缺字段抛 `ValueError("CONFIG_TOOL_CONTRACT_MISSING_FIELD: <field>")`。`ToolRegistry.register(c)` 拒绝重名。

- [ ] **Step 3: 实现 `envelope.py`**

`ToolResult` pydantic 模型，9 顶层字段 + `error: ErrorInfo | None` 平级（`error` 与 `ok=False` 互斥配套）+ `raw: bool = False`（第 10 字段，仅 `raw=true` 请求时置 True）。`ErrorInfo`: `code/message/retryable/data`。

- [ ] **Step 4: 实现 `output_pipeline.py`**

按设计 D11.5 / tasks 3.5 必须做：二进制识别（C0 控制字符 → 拒绝）→ 字节截断（max_bytes）→ 编码探测（UTF-8 优先，回退 latin-1）→ 脱敏（pattern + custom regex）→ stdout/stderr 分离 → 分页（按行 cursor，超过 max_bytes 退化为 bytes cursor）；`raw=true` 不脱敏并在 `audit_flags["raw"]=True`，由 dispatcher 决定是否允许（policy 拒则不进入本函数）。

```python
# src/ssh_mcp/server/output_pipeline.py
from __future__ import annotations
from dataclasses import dataclass, field
import re

DEFAULT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----[\s\S]+?-----END [^-]+ PRIVATE KEY-----"),
]
# 二进制识别：除 \t \n \r 外的 C0 控制字符出现即判定为二进制
_BIN_CTRL = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")

@dataclass
class PipelineResult:
    stdout_text: str
    stderr_text: str
    truncated: bool
    cursor: str | None          # "line:N" 或 "bytes:N"
    binary_rejected: bool
    encoding: str               # "utf-8" / "latin-1" / "binary"
    audit_flags: dict[str, bool] = field(default_factory=dict)

def _detect_encoding(buf: bytes) -> str:
    try:
        buf.decode("utf-8"); return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"

def _redact(text: str, extra: list[re.Pattern[str]]) -> str:
    for pat in (*DEFAULT_PATTERNS, *extra):
        text = pat.sub("<REDACTED>", text)
    return text

def run_pipeline(
    *, stdout: bytes, stderr: bytes,
    max_lines: int, max_bytes: int,
    extra_patterns: list[re.Pattern[str]],
    raw: bool,
) -> PipelineResult:
    # 1. 二进制识别（任一通道含禁用控制字符 → 拒绝）
    if _BIN_CTRL.search(stdout) or _BIN_CTRL.search(stderr):
        return PipelineResult(
            stdout_text="", stderr_text="",
            truncated=True, cursor=None,
            binary_rejected=True, encoding="binary",
            audit_flags={"binary_rejected": True, "raw": raw},
        )
    # 2. 字节截断（按通道分别裁；超限退化为 bytes cursor）
    truncated_bytes = False
    if len(stdout) > max_bytes:
        stdout = stdout[:max_bytes]; truncated_bytes = True
    if len(stderr) > max_bytes:
        stderr = stderr[:max_bytes]; truncated_bytes = True
    # 3. 编码探测
    enc = _detect_encoding(stdout + stderr)
    so = stdout.decode(enc, errors="replace")
    se = stderr.decode(enc, errors="replace")
    # 4. 脱敏（raw=true 跳过）
    if not raw:
        so = _redact(so, extra_patterns)
        se = _redact(se, extra_patterns)
    # 5. 分页（按行）
    lines_o = so.splitlines(); lines_e = se.splitlines()
    truncated_lines = len(lines_o) > max_lines or len(lines_e) > max_lines
    if truncated_lines:
        lines_o = lines_o[:max_lines]; lines_e = lines_e[:max_lines]
    cursor = None
    if truncated_lines:
        cursor = f"line:{max_lines}"
    elif truncated_bytes:
        cursor = f"bytes:{max_bytes}"
    return PipelineResult(
        stdout_text="\n".join(lines_o),
        stderr_text="\n".join(lines_e),
        truncated=truncated_lines or truncated_bytes,
        cursor=cursor,
        binary_rejected=False,
        encoding=enc,
        audit_flags={"raw": raw} if raw else {},
    )
```

dispatcher 在装 envelope 时：

1. **`binary_rejected=True`** → 装配错误 envelope：`ok=False, error=ErrorInfo(code="EXEC_BINARY_OUTPUT", message="command produced binary output", retryable=False)`，不返回 stdout/stderr 内容。
2. **`raw=True`** → envelope 顶层增加 `raw: true` 字段（与 `ok/host/exit_code/...` 同级），同时 audit 行标记 `raw=true`。
3. 其它情况 → 正常装配 `ok=True` envelope，`data.stdout/stderr` 取 pipeline 输出。

`raw=true` 必须由 policy 单独放行（默认 deny）。

- [ ] **Step 5: 跑测试 + 提交**

Run: `uv run pytest tests/unit/server/ -v`
Expected: 11 PASS（contract 3 + envelope 1 + pipeline 7）。

```bash
git add src/ssh_mcp/server/ tests/unit/server/
git commit -m "server: add ToolContract, ToolResult envelope, output pipeline (stdout/stderr/binary/raw)"
```

---

## Task 4: SSH 连接池（capability: ssh-connection-pool）

**Files:**
- Create: `src/ssh_mcp/credentials/{base.py,yaml_provider.py}`
- Create: `src/ssh_mcp/ssh/{pool.py,known_hosts.py,errors.py}`
- Create: `src/ssh_mcp/cli/trust.py`
- Test: `tests/unit/ssh/{test_pool.py,test_known_hosts.py}`、`tests/integration/test_proxyjump.py`

- [ ] **Step 1: 写失败测试覆盖握手 / 复用 / 串行 / 超时**

```python
# tests/unit/ssh/test_pool.py
import asyncio, asyncssh, pytest
from ssh_mcp.ssh.pool import ConnectionPool
from ssh_mcp.credentials.yaml_provider import YamlCredentialProvider

async def test_acquire_serializes_per_host(memory_ssh_server, tmp_hosts_yaml):
    pool = ConnectionPool(YamlCredentialProvider(tmp_hosts_yaml), known_hosts=memory_ssh_server.known_hosts)
    async with pool.acquire("vps") as c1, pool.acquire("vps") as c2:
        assert c1 is c2  # 复用

async def test_unknown_host_key_rejects(memory_ssh_server_unknown_key, tmp_hosts_yaml):
    pool = ConnectionPool(
        YamlCredentialProvider(tmp_hosts_yaml),
        known_hosts=memory_ssh_server_unknown_key.empty_known_hosts,  # 空文件，强制 unknown
    )
    with pytest.raises(Exception, match="SSH_CONNECT_HOST_KEY_UNKNOWN"):
        async with pool.acquire("vps"): pass

async def test_command_timeout(memory_ssh_server_slow, tmp_hosts_yaml):
    pool = ConnectionPool(
        YamlCredentialProvider(tmp_hosts_yaml),
        known_hosts=memory_ssh_server_slow.known_hosts,
        command_timeout=0.5,
    )
    with pytest.raises(Exception, match="EXEC_TIMEOUT"):
        async with pool.acquire("vps") as c: await c.run("sleep 5")
```

`tests/support/ssh_server.py` 提供 `memory_ssh_server` fixture（复用 asyncssh 内置 `SSHServer` + 临时 host key）。

Run: `uv run pytest tests/unit/ssh/ -v`
Expected: FAIL — 模块缺失。

- [ ] **Step 2: 写 `errors.py` 错误码 + `known_hosts.py` 强校验**

```python
# src/ssh_mcp/ssh/errors.py
class SSHError(Exception):
    code: str = "SSH_UNKNOWN"

class HostKeyUnknown(SSHError): code = "SSH_CONNECT_HOST_KEY_UNKNOWN"
class HostKeyMismatch(SSHError): code = "SSH_CONNECT_HOST_KEY_MISMATCH"
class KeyUnreadable(SSHError): code = "SSH_CONNECT_KEY_UNREADABLE"
class ExecTimeout(SSHError): code = "EXEC_TIMEOUT"
```

`known_hosts.py` 包装 `asyncssh.read_known_hosts`；找不到 → `HostKeyUnknown`；指纹不匹配 → `HostKeyMismatch`，永不自动覆盖。

- [ ] **Step 3: 写 `CredentialProvider` 与 yaml 实现**

```python
# src/ssh_mcp/credentials/base.py
from typing import Protocol
class HostCred:  # dataclass
    host: str; port: int; user: str; key_path: str | None; password: str | None; bastion: str | None

class CredentialProvider(Protocol):
    async def resolve(self, host: str) -> HostCred: ...
    async def list_hosts(self) -> list[str]: ...
```

`YamlCredentialProvider` 直接读 `HostsConfig`，对 caller 永不返回 `key_path/password` 字段（只在 pool 内部消费，调用方拿不到）。

- [ ] **Step 4: 写 `pool.py`**

```python
# src/ssh_mcp/ssh/pool.py
import asyncio, asyncssh
from contextlib import asynccontextmanager
from .errors import HostKeyUnknown, HostKeyMismatch, ExecTimeout, KeyUnreadable

class ConnectionPool:
    def __init__(self, provider, *, known_hosts, connect_timeout=10, command_timeout=30, keepalive=30, global_concurrency=16):
        self._provider = provider
        self._known_hosts = known_hosts
        self._locks: dict[str, asyncio.Lock] = {}
        self._conns: dict[str, asyncssh.SSHClientConnection] = {}
        self._sem = asyncio.Semaphore(global_concurrency)
        self._cfg = (connect_timeout, command_timeout, keepalive)

    @asynccontextmanager
    async def acquire(self, host: str):
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with self._sem, lock:
            if host not in self._conns or self._conns[host].is_closed():
                self._conns[host] = await self._dial(host)
            yield self._conns[host]

    async def _dial(self, host: str):
        cred = await self._provider.resolve(host)
        try:
            return await asyncio.wait_for(
                asyncssh.connect(
                    host=cred.host, port=cred.port, username=cred.user,
                    client_keys=[cred.key_path] if cred.key_path else None,
                    password=cred.password, known_hosts=self._known_hosts,
                    keepalive_interval=self._cfg[2],
                    tunnel=await self._tunnel(cred.bastion) if cred.bastion else None,
                ), timeout=self._cfg[0])
        except asyncssh.HostKeyNotVerifiable as e: raise HostKeyUnknown(str(e)) from e
        except asyncssh.PermissionDenied as e: raise KeyUnreadable(str(e)) from e

    async def connect_once(self, host: str) -> "ProbeResult":
        """探测式连接：建立 + 立即关闭，**不入池**。test_connection 工具用。

        返回 latency_ms / auth_method / banner_redacted / fingerprint_sha256。
        """
        import time
        t0 = time.monotonic()
        conn = await self._dial(host)
        latency_ms = int((time.monotonic() - t0) * 1000)
        try:
            fp = conn.get_server_host_key().get_fingerprint()  # "SHA256:..."
            auth = conn.get_extra_info("auth_method") or "publickey"
            banner = (conn.get_extra_info("banner") or "")[:200]  # 截断防泄露
            return ProbeResult(
                latency_ms=latency_ms,
                auth_method=auth,
                banner_redacted=banner,
                fingerprint_sha256=fp,
            )
        finally:
            conn.close(); await conn.wait_closed()
```

`ProbeResult` 用 dataclass 定义在 `ssh/pool.py` 内。约定：`test_connection` 工具 **只能** 调 `pool.connect_once(host)`，禁止访问 `_dial`（lint 测试附加一条断言：`_dial` 在 pool.py 之外不可被 import）。

加一道 `lint` 测试：`tests/unit/ssh/test_no_direct_connect.py` 用 `ast` 扫 `src/ssh_mcp/` 禁止 `asyncssh.connect` 出现在 pool.py 之外。

- [ ] **Step 5: 写 `ssh-mcp trust <host>` CLI 子命令**

`src/ssh_mcp/cli/trust.py`：交互拉取首次指纹（用 asyncssh 一次性 dial 不校验仅取 fingerprint），SHA256 hex 显示，二次确认后写入 `~/.ssh-mcp/known_hosts`（mode 0600）。

- [ ] **Step 6: 跑测试 + 集成 docker + 提交**

Run: `uv run pytest tests/unit/ssh/ -v`
Expected: PASS。

`tests/integration/test_proxyjump.py` 在 CI 夜跑 docker `linuxserver/openssh-server` 起 bastion + target 两容器，验证 ProxyJump 与 known_hosts 拒覆盖。

```bash
git add src/ssh_mcp/credentials/ src/ssh_mcp/ssh/ src/ssh_mcp/cli/trust.py tests/unit/ssh/ tests/integration/test_proxyjump.py
git commit -m "ssh: add credential provider, connection pool with strict known_hosts"
```

---

## Task 5: PolicyEngine（capability: policy-engine）

**Files:**
- Create: `src/ssh_mcp/policy/{decision.py,engine.py,rules/{host,allowlist,arg_schema,deny,risk,approval,window,rate_limit}.py}`
- Test: `tests/unit/policy/test_<rule>.py` 8 份 + `test_engine_pipeline.py`

- [ ] **Step 1: 写失败测试**

每子规则一文件一测试。例：

```python
# tests/unit/policy/test_deny.py
from ssh_mcp.policy.engine import PolicyEngine
from ssh_mcp.policy.decision import PolicyDecision

def test_deny_blacklisted_command(engine_with_policy):
    d = engine_with_policy.evaluate(tool="run_shell_command", args={"cmd":"rm -rf /"}, caller=ops_caller())
    assert d.allow is False and "BLACKLIST" in d.reasons[0]
```

```python
# tests/unit/policy/test_window.py
def test_readonly_bypasses_window(engine, frozen_time_outside_window):
    d = engine.evaluate(tool="get_system_info", args={"host":"vps"}, caller=ops_caller())
    assert d.allow is True
def test_mutation_blocked_outside_window(engine, frozen_time_outside_window):
    d = engine.evaluate(tool="manage_service", args={"action":"restart","host":"prod","name":"nginx"}, caller=ops_caller())
    assert d.allow is False and any("WINDOW" in r for r in d.reasons)
```

Run: `uv run pytest tests/unit/policy/ -v`
Expected: FAIL。

- [ ] **Step 2: 写 `PolicyDecision`**

```python
# src/ssh_mcp/policy/decision.py
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PolicyDecision:
    allow: bool
    risk: str  # low|medium|high|forbidden
    reasons: tuple[str, ...] = ()
    needs_approval: bool = False
    approval_token: str | None = None
    redact_rules: tuple[str, ...] = ()
```

- [ ] **Step 3: 写 8 个 rule 模块 + 引擎管线**

每个 rule 实现 `evaluate(ctx) -> PolicyDecision | None`（None=放行进下一阶段，非 None=立停）。`engine.py` 按固定顺序串联：

```python
PIPELINE = [host_allowlist, allowlist, arg_schema, deny, risk_classify, approval_gate, window, rate_limit]
def evaluate(self, *, tool, args, caller) -> PolicyDecision:
    ctx = Ctx(tool=tool, args=args, caller=caller, snapshot=self._snap.current)
    for rule in PIPELINE:
        out = rule(ctx)
        if out is not None:
            return out
    return PolicyDecision(allow=True, risk=ctx.risk or "low")
```

`risk_classify` 读 ToolContract `risk_default`（支持 dict per-action）+ caller env 升档（prod 比 test 升一档）；break-glass 启用且满足三重条件时再升一档。

- [ ] **Step 4: 实现 break-glass 三重 + forbidden 不可解锁 + 审计标记升级**

`approval_gate` 收到 break-glass 上下文：require `break_glass_reason` 非空，否则返回 `POLICY_DENIED_BREAKGLASS_REASON_MISSING`；`risk_classify` 输出的 `risk` 在 audit 阶段被消费时升一档。`forbidden` 永远 deny，break-glass 不解锁。

- [ ] **Step 5: 实现 token bucket rate_limit**

```python
# src/ssh_mcp/policy/rules/rate_limit.py
import time
class TokenBucket:
    def __init__(self, capacity, refill_per_sec):
        self.cap = capacity; self.rate = refill_per_sec
        self.tokens = capacity; self.ts = time.monotonic()
    def take(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.cap, self.tokens + (now - self.ts) * self.rate)
        self.ts = now
        if self.tokens >= 1: self.tokens -= 1; return True
        return False
```

引擎维护 3 维 bucket：`(tool, user, host)` 各一组。

- [ ] **Step 6: 跑测试 + 覆盖率门槛 + 提交**

Run: `uv run pytest tests/unit/policy/ --cov=src/ssh_mcp/policy --cov-fail-under=95 -v`
Expected: PASS，覆盖率 ≥ 95%。

```bash
git add src/ssh_mcp/policy/ tests/unit/policy/
git commit -m "policy: add 8-stage rule stack with risk levels, break-glass, rate_limit"
```

---

## Task 6: 审计链路（capability: audit-pipeline）

**Files:**
- Create: `src/ssh_mcp/audit/{event.py,sink.py,jsonl_sink.py,redact.py,index.py,query.py}`
- Create: `src/ssh_mcp/cli/audit.py`
- Test: `tests/unit/audit/test_{sink,redact,query,export}.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/audit/test_sink.py
async def test_jsonl_rotation_per_utc_day(tmp_path, frozen_time):
    sink = JsonlAuditSink(dir=tmp_path)
    await sink.write(make_event(ts="2026-05-26T23:59:59Z"))
    await sink.write(make_event(ts="2026-05-27T00:00:00Z"))
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["audit-2026-05-26.jsonl", "audit-2026-05-27.jsonl"]
    assert (tmp_path / files[0]).stat().st_mode & 0o777 == 0o600

async def test_fan_out_failure_does_not_block(tmp_path, caplog):
    from ssh_mcp.audit.sink import FanOutSink
    from ssh_mcp.audit.jsonl_sink import JsonlAuditSink

    class BrokenSink:
        async def write(self, ev): raise RuntimeError("disk gone")
        async def flush(self): pass
        async def close(self): pass

    primary = JsonlAuditSink(dir=tmp_path)
    secondary = BrokenSink()
    fan = FanOutSink(primary=primary, secondaries=[secondary])
    await fan.write(make_event(ts="2026-05-27T10:00:00Z"))   # 业务不抛
    # 主 sink 落盘成功
    assert any(p.name.startswith("audit-2026-05-27") for p in tmp_path.iterdir())
    # secondary 失败仅 warning
    assert any("audit secondary sink failed" in r.message for r in caplog.records)
```

```python
# tests/unit/audit/test_redact.py
def test_x_redact_strips_password():
    schema = {"type":"object","properties":{"password":{"type":"string","x-redact":True}}}
    out = redact_args({"password":"secret","name":"nginx"}, schema)
    assert out == {"password":"<REDACTED>","name":"nginx"}
```

Run: `uv run pytest tests/unit/audit/ -v`
Expected: FAIL。

- [ ] **Step 2: 写 `event.py` + `sink.py` 接口**

```python
# src/ssh_mcp/audit/sink.py
from typing import Protocol
class AuditSink(Protocol):
    async def write(self, event: AuditEvent) -> None: ...
    async def flush(self) -> None: ...
    async def close(self) -> None: ...
```

`AuditEvent` 字段：`ts/correlation_id/tool/host/user/env/risk/decision/reasons/args_redacted/output_summary/duration_ms/break_glass/break_glass_reason/raw`。

- [ ] **Step 3: 写 `JsonlAuditSink`**

```python
# src/ssh_mcp/audit/jsonl_sink.py
import asyncio, json, os
from datetime import datetime, timezone
from pathlib import Path

class JsonlAuditSink:
    def __init__(self, *, dir: Path):
        self.dir = dir; self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._fp = None; self._date = None
    async def _rotate(self, ts: str):
        d = ts[:10]
        if d != self._date:
            if self._fp: self._fp.close()
            path = self.dir / f"audit-{d}.jsonl"
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            self._fp = os.fdopen(fd, "a", encoding="utf-8"); self._date = d
    async def write(self, event):
        async with self._lock:
            await self._rotate(event.ts); self._fp.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n"); self._fp.flush()
```

启动期可写探测：模块导入后立即调用 `os.access(dir, os.W_OK)`，false → raise + main 拒启。

- [ ] **Step 4: 写 fan-out + redact 流水线**

`FanOutSink` 含主+多 secondary，主写失败 raise；secondary 失败 fail-safe 仅 `logging.warning`。

`redact_args` 递归遍历 schema，遇 `x-redact: true` 替换值为 `<REDACTED>`。

- [ ] **Step 5: 写读侧索引 + CLI query/export**

`index.py`：扫描日 jsonl 建内存倒排（day/tool/host/user/risk → 行偏移）。

`cli/audit.py` argparse：

```
ssh-mcp audit query --since 2026-05-20 --tool manage_service --host prod --limit 50
ssh-mcp audit export --format csv --out /tmp/audit.csv
```

CSV 表头与字段顺序写死，加一道断言。

- [ ] **Step 6: 跑测试 + 提交**

Run: `uv run pytest tests/unit/audit/ -v`
Expected: PASS。

```bash
git add src/ssh_mcp/audit/ src/ssh_mcp/cli/audit.py tests/unit/audit/
git commit -m "audit: add jsonl sink with daily rotation, redact, index, query/export cli"
```

---

## Task 7: 审批工作流（capability: approval-workflow）

**Files:**
- Create: `src/ssh_mcp/approval/{models.py,backend.py,local_sqlite.py}`
- Create: `src/ssh_mcp/operations/approval/{plan_action.py,manage_approval.py,apply_approved_action.py}`
- Create: `src/ssh_mcp/cli/approve.py`
- Test: `tests/integration/test_approval_loop.py`

- [ ] **Step 1: 写失败集成测试覆盖闭环 + 4 个反例**

```python
# tests/integration/test_approval_loop.py
async def test_full_loop(harness):
    plan = await harness.call("plan_action", tool="manage_service", host="prod", action="restart", name="nginx")
    req = await harness.call("manage_approval", action="request", plan_id=plan["plan_id"])
    await harness.cli("approve", req["request_id"])
    out = await harness.call("apply_approved_action",
        approval_token=req["approval_token"], nonce=req["nonce"],
        confirmation_text=plan["confirmation_text"])
    assert out["ok"]

async def test_token_replay_rejected(harness, approved):
    await harness.call("apply_approved_action", **approved.payload)
    r = await harness.call("apply_approved_action", **approved.payload)
    assert r["error"]["code"] == "APPROVAL_TOKEN_CONSUMED"

async def test_token_cross_tool_rejected(harness, approved_for_nginx):
    payload = approved_for_nginx.payload | {"tool":"manage_file"}  # 试图换工具
    r = await harness.call("apply_approved_action", **payload)
    assert r["error"]["code"] == "APPROVAL_TOKEN_MISMATCH"

async def test_expired_token_rejected(harness, expired):
    r = await harness.call("apply_approved_action", **expired.payload)
    assert r["error"]["code"] == "APPROVAL_EXPIRED"

async def test_confirmation_text_mismatch(harness, approved):
    bad = approved.payload | {"confirmation_text": approved.payload["confirmation_text"] + " "}
    r = await harness.call("apply_approved_action", **bad)
    assert r["error"]["code"] == "APPROVAL_CONFIRMATION_MISMATCH"
```

Run: `uv run pytest tests/integration/test_approval_loop.py -v`
Expected: FAIL。

- [ ] **Step 2: 写 SQLite schema + `LocalApprovalBackend`**

DDL：

```sql
CREATE TABLE IF NOT EXISTS approval (
  request_id   TEXT PRIMARY KEY,
  plan_id      TEXT NOT NULL,
  tool         TEXT NOT NULL,
  args_json    TEXT NOT NULL,
  caller_user  TEXT NOT NULL,
  risk         TEXT NOT NULL,
  confirmation_text TEXT NOT NULL,
  approval_token    TEXT UNIQUE NOT NULL,
  nonce        TEXT NOT NULL,
  state        TEXT NOT NULL,  -- pending|approved|consumed|denied|expired|canceled
  created_at   TEXT NOT NULL,
  expires_at   TEXT NOT NULL,
  break_glass  INTEGER NOT NULL DEFAULT 0,
  break_glass_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_token_nonce ON approval(approval_token, nonce);
```

接口：

```python
# src/ssh_mcp/approval/backend.py
class ApprovalBackend(Protocol):
    async def request(self, req: ApprovalRequest) -> ApprovalRequest: ...
    async def list_pending(self, *, filter: dict) -> list[ApprovalRequest]: ...
    async def approve(self, request_id: str, *, by: str) -> None: ...
    async def deny(self, request_id: str, *, by: str, reason: str) -> None: ...
    async def consume(self, *, token: str, nonce: str) -> ApprovalRequest: ...
```

`consume` 用单事务 `UPDATE ... WHERE state='approved' AND token=? AND nonce=? RETURNING *`，影响行 0 → raise `APPROVAL_TOKEN_CONSUMED`/`MISMATCH`/`EXPIRED` 按状态分类。

- [ ] **Step 3: 写 3 个工具 handler**

`plan_action`：渲染 `confirmation_text=确认在 {env} 主机 {host} 上 {action} {target}`，返回 envelope `data={plan_id, risk, confirmation_text, expected_argv | expected_changes}`。**不连 SSH**。

`manage_approval(action=request|cancel|list)`：默认 `expires_at=now+30min`。

`apply_approved_action(approval_token, nonce, confirmation_text)`：
1. `backend.consume()` 拿到原 plan 上下文。
2. **重新**调用 PolicyEngine 用 `args+caller+now`，任何 deny 立返；token 标记 consumed 不退回。
3. 调用对应工具实际执行；envelope `data.consumed_via=token`。

- [ ] **Step 4: 写 CLI `ssh-mcp approve`**

`ssh-mcp approve --list` 列待审；`ssh-mcp approve <request_id>` 二次输入 confirmation_text 校验后 `backend.approve(by=$USER)`。

- [ ] **Step 5: 跑测试 + 提交**

Run: `uv run pytest tests/integration/test_approval_loop.py -v`
Expected: 5 PASS。

```bash
git add src/ssh_mcp/approval/ src/ssh_mcp/operations/approval/ src/ssh_mcp/cli/approve.py tests/integration/test_approval_loop.py
git commit -m "approval: add plan/request/apply 3-step loop with sqlite backend and re-policy-check"
```

---

## Task 8: MCP 协议入口（capability: mcp-protocol-surface）

**Files:**
- Create: `src/ssh_mcp/transport/{stdio.py,http.py,bearer.py}`
- Create: `src/ssh_mcp/server/dispatcher.py`
- Create: `src/ssh_mcp/server/mcp_app.py`
- Create: `src/ssh_mcp/utils/correlation.py`
- Test: `tests/integration/test_mcp_dual_transport.py`

- [ ] **Step 1: 写失败测试覆盖 9 方法 / 401 / 未 init / list 过滤 / templates**

```python
# tests/integration/test_mcp_dual_transport.py
async def test_stdio_and_http_share_state(stdio_client, http_client, harness):
    await stdio_client.call("tools/call", name="list_hosts", arguments={})
    await http_client.call("tools/call", name="list_hosts", arguments={})
    assert harness.audit_lines() >= 2  # 同一 sink 两行

async def test_http_missing_bearer_returns_401(http_client_no_token):
    r = await http_client_no_token.raw_post("/", {"method":"tools/list"})
    assert r.status_code == 401

async def test_call_before_initialize_rejected(http_client_no_init):
    r = await http_client_no_init.call("tools/call", name="list_hosts")
    assert r["error"]["code"] == -32002

async def test_method_not_found(http_client):
    r = await http_client.call("tools/cancel")
    assert r["error"]["code"] == -32601

async def test_templates_list_includes_audit_search(http_client):
    r = await http_client.call("resources/templates/list")
    uris = [t["uriTemplate"] for t in r["resourceTemplates"]]
    assert "ssh://audit/search{?since,until,tool,host,user,risk,limit}" in uris
```

Run: 全 FAIL。

- [ ] **Step 2: 写 `correlation.py` + `dispatcher.py`**

```python
# src/ssh_mcp/utils/correlation.py
from contextvars import ContextVar
from ulid import ULID  # python-ulid
_CID: ContextVar[str | None] = ContextVar("correlation_id", default=None)
def new_correlation_id() -> str: return str(ULID())
def set_correlation_id(cid: str) -> None: _CID.set(cid)
def current_correlation_id() -> str | None: return _CID.get()
```

`Dispatcher` 是单例，构造时注入 `(registry, policy, audit, approval, task_store)`；`dispatch(call_ctx)` 入口生成 `correlation_id`，挂到 `contextvars.ContextVar` 贯穿日志/审计/error。

- [ ] **Step 3: 写 `mcp_app.py` 注册 9 handler**

用官方 mcp SDK：

```python
# src/ssh_mcp/server/mcp_app.py
from mcp.server import Server
def build_app(deps) -> Server:
    app = Server("ssh-mcp")

    @app.list_tools()
    async def _list_tools():
        return await deps.dispatcher.list_tools(caller=deps.current_caller())

    @app.call_tool()
    async def _call_tool(name, arguments):
        return await deps.dispatcher.call_tool(name, arguments, caller=deps.current_caller())

    @app.list_resources()
    async def _list_resources():
        return await deps.dispatcher.list_resources(caller=deps.current_caller())

    @app.read_resource()
    async def _read_resource(uri: str):
        return await deps.dispatcher.read_resource(uri, caller=deps.current_caller())

    @app.list_resource_templates()
    async def _list_templates():
        return deps.dispatcher.resource_templates()  # 静态 5 模板

    @app.list_prompts()
    async def _list_prompts():
        return await deps.dispatcher.list_prompts(caller=deps.current_caller())

    @app.get_prompt()
    async def _get_prompt(name: str, arguments: dict):
        return await deps.dispatcher.get_prompt(name, arguments, caller=deps.current_caller())

    return app
```

`templates/list` 返回固定 5 个 template 含 `ssh://audit/search{?since,until,tool,host,user,risk,limit}`。

- [ ] **Step 4: 写 stdio + HTTP transport，共用同一 deps**

```python
# src/ssh_mcp/transport/stdio.py
async def serve_stdio(deps):
    app = build_app(deps)
    async with mcp.server.stdio.stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())
```

```python
# src/ssh_mcp/transport/http.py
from starlette.applications import Starlette
from .bearer import bearer_middleware
def build_http(deps, *, token):
    return Starlette(middleware=[bearer_middleware(token)], routes=[
        Route("/", endpoint=streamable_handler(build_app(deps)), methods=["POST","GET"]),
        Route("/admin/reload", endpoint=reload_handler(deps), methods=["POST"]),
        Route("/metrics", endpoint=metrics_handler(deps), methods=["GET"]),
    ])
```

`bearer_middleware`：缺/不一致返回 401，**不进 Dispatcher 不写业务审计**，仅 `logging.warning`。

- [ ] **Step 5: list 类按 caller policy 过滤可见性**

`Dispatcher.list_tools()` 遍历 registry，对每项 `policy.is_visible(tool, caller)`；不可见直接不入返回数组。`resources/list` `prompts/list` 同。

- [ ] **Step 6: 跑测试 + 提交**

Run: `uv run pytest tests/integration/test_mcp_dual_transport.py -v`
Expected: 5 PASS。

```bash
git add src/ssh_mcp/transport/ src/ssh_mcp/server/{dispatcher,mcp_app}.py src/ssh_mcp/utils/correlation.py tests/integration/test_mcp_dual_transport.py
git commit -m "mcp: add dual transport (stdio + streamable http) with shared dispatcher and bearer auth"
```

---

## Task 9: 主机资产管理（capability: host-inventory）

**Files:**
- Create: `src/ssh_mcp/operations/host_inventory/{list_hosts,get_host_info,test_connection,sync_inventory}.py`
- Create: `src/ssh_mcp/credentials/inventory_source.py`
- Test: `tests/integration/test_host_inventory.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_list_hosts_strips_credentials(harness):
    out = await harness.call("list_hosts", filter={"env":"prod"})
    for h in out["data"]["hosts"]:
        assert "key_path" not in h and "password" not in h

async def test_test_connection_returns_fingerprint(harness):
    out = await harness.call("test_connection", host="vps-test")
    assert out["data"]["fingerprint_sha256"].startswith("SHA256:")

async def test_unknown_host_denied(harness):
    r = await harness.call("test_connection", host="not-in-allowlist")
    assert r["error"]["code"] == "POLICY_DENIED_HOST"
```

- [ ] **Step 2: 写 4 个 handler 与 `InventorySource` 接口**

`list_hosts` 直接读 `HostsConfig`，序列化时白名单字段（host alias / port / user / tags / env / bastion 名）；`get_host_info(include=[basic,policy,inventory])` 组合三段信息。`test_connection` 调 `pool.connect_once(host)` 公共方法（**不**走 `_dial`），返回 `ProbeResult` 字段 latency_ms / auth_method / banner_redacted / fingerprint_sha256。

`InventorySource` Protocol：`list_hosts() / fetch(host)`。**首版仅实现 `YamlInventorySource`**；接口 docstring 注明未来可接 CMDB / Ansible inventory（参见 design.md D2 扩展点声明）。**不注册运行时占位 backend**——避免不可用后端被误调用；后续要加新 source 时单独走变更流程。

`sync_inventory(source)` 调 `source.list_hosts()` → 写入 SQLite `inventory_cache` 表（与 host pool 解耦）。

- [ ] **Step 3: 注册 4 个 ToolContract 9 字段**

每个工具构造期向 `ToolRegistry` 注册完整契约，`registry.validate_all()` 在启动期跑一次。

- [ ] **Step 4: 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_host_inventory.py -v
git add src/ssh_mcp/operations/host_inventory/ src/ssh_mcp/credentials/inventory_source.py tests/integration/test_host_inventory.py
git commit -m "operations: add 4 host inventory tools with credential filtering"
```

---

## Task 10: 系统巡检与日志（capabilities: system-inspection / log-query）

**Files:**
- Create: `src/ssh_mcp/operations/system_inspection/{get_system_info,get_system_metrics,query_services,query_processes}.py`
- Create: `src/ssh_mcp/operations/log_query/{query_journal,list_log_files}.py`
- Create: `src/ssh_mcp/operations/_helpers/safe_exec.py`（受控 argv 执行 + envelope 装配）
- Test: `tests/integration/test_system_inspection.py`、`tests/integration/test_log_query.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_get_system_info_default(harness):
    out = await harness.call("get_system_info", host="vps", include=["os","uptime","hostname"])
    assert out["data"]["os"]["kernel"]
async def test_query_journal_grep_mode(harness):
    out = await harness.call("query_journal", host="vps", source="journal", target="nginx",
                             mode="grep", pattern="error", lines=200)
    assert out["data"]["matches_count"] >= 0
async def test_list_log_files_outside_allowlist_returns_empty(harness):
    out = await harness.call("list_log_files", host="vps", path="/etc/shadow")
    assert out["data"]["files"] == []
    audit = harness.last_audit()
    assert "filtered_outside_allowlist" in audit["reasons"]
```

- [ ] **Step 2: 写 `safe_exec` 助手**

```python
# src/ssh_mcp/operations/_helpers/safe_exec.py
async def safe_exec(*, pool, host, argv: list[str], timeout: int) -> ExecResult:
    async with pool.acquire(host) as conn:
        proc = await asyncio.wait_for(conn.run(' '.join(map(shlex.quote, argv)), check=False), timeout=timeout)
        return ExecResult(stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)
```

约定：所有 operations 必须经 `safe_exec`，禁止直接拼 shell（lint 测试断言）。

- [ ] **Step 3: 实现 6 个工具 handler**

每个工具：解析 `include/kinds/mode/filter` → 拼出对应受控 argv（`uname -a`、`uptime`、`free -m`、`df -h`、`ss -tnlp`、`systemctl status <name>`、`journalctl -u <name> -n 200 --no-pager`、`find <path> -name <glob>`）→ 调 `safe_exec` → 走 output_pipeline → 装 envelope。

`list_log_files`：用 `policy.path_policy` 过滤；不在 readable 白名单的项被剔除，`audit.reasons += ("filtered_outside_allowlist",)`。

- [ ] **Step 4: 注册 6 个 ToolContract**

含 `risk_default="low"`、`readonly=true`、`output_limits.max_lines={1000-5000}`、`approval_required_when=null`。

- [ ] **Step 5: 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_system_inspection.py tests/integration/test_log_query.py -v
git add src/ssh_mcp/operations/system_inspection/ src/ssh_mcp/operations/log_query/ src/ssh_mcp/operations/_helpers/
git commit -m "operations: add system inspection (4) + log query (2) readonly tools"
```

---

## Task 11: 命令执行（capability: command-execution）

**Files:**
- Create: `src/ssh_mcp/operations/command_execution/{list_command_presets,run_command_preset,validate_shell_command,explain_shell_command,run_shell_command,run_shell_command_with_approval}.py`
- Create: `src/ssh_mcp/operations/command_execution/blacklist.py`
- Test: `tests/integration/test_command_execution.py`

- [ ] **Step 1: 写失败测试**

```python
def test_blacklist_blocks_rm_rf():
    from ssh_mcp.operations.command_execution.blacklist import is_blacklisted
    assert is_blacklisted("rm -rf /")
    assert is_blacklisted("nft flush ruleset")
    assert is_blacklisted("curl https://x | sh")
def test_background_token_blocked():
    assert is_blacklisted("nginx -t & echo done")
    assert is_blacklisted("nohup tail -f log")
async def test_arbitrary_shell_default_disabled(harness):
    r = await harness.call("run_shell_command", host="vps", cmd="echo hi")
    assert r["error"]["code"] == "POLICY_DENIED_FEATURE_DISABLED"
async def test_dry_run_returns_argv(harness):
    r = await harness.call("run_command_preset", name="systemctl_status", args={"name":"nginx"}, mode="dry-run")
    assert r["data"]["expected_argv"] == ["systemctl","status","nginx"]
    assert r["data"].get("stdout") is None
```

- [ ] **Step 2: 写黑名单**

```python
# src/ssh_mcp/operations/command_execution/blacklist.py
import re
PATTERNS = [
    r"\brm\s+-rf\b", r"\bmkfs\b", r"\bdd\b", r"\bshutdown\b", r"\breboot\b",
    r"iptables\s+-F", r"nft\s+flush\s+ruleset", r"docker\s+system\s+prune",
    r"\buserdel\b", r"\bpasswd\b", r"chmod\s+-R\s+777", r"chown\s+-R",
    r"\|\s*sh\b", r"\|\s*bash\b",
]
BG_TOKENS = re.compile(r"(?<!\w)(&|nohup|disown|setsid)(?!\w)")

def is_blacklisted(cmd: str) -> bool:
    for p in PATTERNS:
        if re.search(p, cmd): return True
    if BG_TOKENS.search(cmd): return True
    return False
```

- [ ] **Step 3: 实现 6 个工具**

`list_command_presets` 读 `CommandsConfig.entries`，附 `policy_explain`（每条规则放行/拦截原因）。

`run_command_preset(name, args, mode)`：
1. 取 spec 的 argv 模板，按 `arg_schema`（merge 后的 enum）+ `allowed_args` 双校验。
2. `mode="dry-run"` 仅返回 `expected_argv`，不连 SSH。
3. `mode="run"` 经 PolicyEngine → `safe_exec` → envelope。

`validate_shell_command` / `explain_shell_command`：纯本地 lint，**不连 SSH**。validate 先跑 blacklist，再用 `bashlex` 解析做"是否含管道/背景符/命令替换"语法检查。

`run_shell_command` 默认 `features.arbitrary_shell=false` deny；启用时跑 8 道防护（黑名单 / 背景 / TTY 拒分配 / 路径白名单 / 命令长度 / 编码 / 输出大小 / 非 root login shell）。

`run_shell_command_with_approval`：在 `run_shell_command` 上叠加 `approval_required_when="always"`。

- [ ] **Step 4: TTY 防护实现**

`safe_exec` 始终 `request_pty=False`；命令含 `tput`/`tty` 等交互指令直接 deny。

- [ ] **Step 5: 注册 6 个 ToolContract + 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_command_execution.py -v
git add src/ssh_mcp/operations/command_execution/
git commit -m "operations: add 6 command execution tools with blacklist + 8 guards"
```

---

## Task 12: 服务与进程变更（capability: service-and-process-mutation）

**Files:**
- Create: `src/ssh_mcp/operations/svc_proc/{manage_service.py,manage_process.py}`
- Test: `tests/integration/test_service_process.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_kill_pid_1_denied(harness):
    r = await harness.call("manage_process", host="vps", action="kill", pid=1)
    assert r["error"]["code"] == "POLICY_DENIED_PROCESS"
async def test_daemon_reload_requires_approval(harness):
    r = await harness.call("manage_service", host="prod", action="daemon_reload", name="nginx")
    assert r["error"]["code"] == "APPROVAL_REQUIRED"
async def test_restart_returns_pre_post_state(harness, approved_restart_nginx):
    out = await harness.call("apply_approved_action", **approved_restart_nginx.payload)
    assert out["data"]["pre_state"] in {"active","inactive","failed"}
    assert out["data"]["post_state"] in {"active","inactive","failed"}
async def test_failure_still_writes_pre_state(harness, approved_restart_broken):
    out = await harness.call("apply_approved_action", **approved_restart_broken.payload)
    assert out["ok"] is False
    assert "pre_state" in out["data"]
```

- [ ] **Step 2: 实现 `manage_service` 7 action**

> 下文为示意伪代码，实现时按 `safe_exec` 真实签名补全；`_systemctl_show` 走 `systemctl show <name> --property=ActiveState,UnitFileState --no-pager`。

```python
async def handle(args, *, pool, timeout: int = 30):
    pre = await _systemctl_show(pool=pool, host=args.host, name=args.name)
    ok = True
    try:
        await safe_exec(pool=pool, host=args.host,
                        argv=["systemctl", args.action, args.name], timeout=timeout)
    except Exception:
        ok = False
        raise
    finally:
        post = await _systemctl_show(pool=pool, host=args.host, name=args.name)
    return ToolResult(ok=ok, host=args.host, exit_code=0, duration_ms=0,
                      truncated=False, cursor=None, summary=f"{args.action} {args.name}",
                      correlation_id=current_correlation_id(),
                      data={"pre_state": pre.active, "post_state": post.active,
                            "is_active": post.active=="active", "is_enabled": post.enabled})
```

per-action risk dict：`start=medium, stop=high, restart=medium, reload=low, enable=medium, disable=medium, daemon_reload=high`。

- [ ] **Step 3: 实现 `manage_process`**

`action=kill|nice`；`pid==1` 或 `pid==os.getpid()`（自身）直接 deny；`nice` 记录 before-after `nice_value`。

- [ ] **Step 4: 高危确认文案模板渲染**

`plan_action` 收到 manage_service/process 时统一拼 `确认在 {env} 主机 {host} 上 {action} {target}`，`target` 取 `name` 或 `pid`。

- [ ] **Step 5: 注册 ToolContract（含 per-action risk dict）+ 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_service_process.py -v
git add src/ssh_mcp/operations/svc_proc/
git commit -m "operations: add manage_service (7 actions) + manage_process with per-action risk"
```

---

## Task 13: 文件操作（capability: file-operations）

**Files:**
- Create: `src/ssh_mcp/operations/file_ops/{read_file,find_files,stat_file,apply_patch,write_file,transfer_file,manage_file}.py`
- Create: `src/ssh_mcp/operations/file_ops/backup.py`
- Create: `src/ssh_mcp/utils/operation_id.py`
- Test: `tests/integration/test_file_ops.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_apply_patch_three_stages(harness, approved_patch):
    out = await harness.call("apply_approved_action", **approved_patch.payload)
    op_id = out["data"]["operation_id"]
    assert op_id.startswith("op-")
    backup = out["data"]["backup_path"]
    # 远端 mode 0700
    mode = await harness.ssh_stat_mode(host=approved_patch.host, path=backup)
    assert mode & 0o777 == 0o700
    # meta.json 含 sha256
    meta = await harness.ssh_read_json(host=approved_patch.host, path=f"{backup}/meta.json")
    assert "sha256" in meta and "correlation_id" in meta

async def test_rollback_re_policy_check(harness, op_id_done):
    r = await harness.call("apply_patch", action="rollback", operation_id=op_id_done)
    assert r["error"]["code"] == "APPROVAL_REQUIRED"  # 重新经 PolicyEngine

async def test_rollback_missing_backup_errors(harness, op_id_no_backup):
    # op_id_no_backup fixture 已先 plan_action + manage_approval(request) 拿到 token/nonce
    fx = op_id_no_backup
    r = await harness.call("apply_patch", action="rollback", operation_id=fx.op_id,
                           approval_token=fx.token, nonce=fx.nonce,
                           confirmation_text=fx.confirmation_text)
    assert r["error"]["code"] == "ROLLBACK_BACKUP_MISSING"

async def test_overwrite_risk_upgraded(harness):
    p = await harness.call("plan_action", tool="write_file", host="prod", action="overwrite",
                           path="/etc/nginx/nginx.conf", content="worker_processes 2;")
    assert p["data"]["risk"] == "high"  # mode=overwrite 升档
```

- [ ] **Step 2: 写 `operation_id.py` 与 `backup.py`**

```python
# src/ssh_mcp/utils/operation_id.py
import time
from ulid import ULID  # python-ulid
def new_operation_id() -> str:
    return f"op-{int(time.time())}-{str(ULID())[-8:].lower()}"
```

`backup.py`：

```python
async def make_backup(*, conn, paths: list[str], correlation_id: str) -> str:
    op_id = new_operation_id()
    base = f"/tmp/ssh-mcp/backups/{op_id}"
    await _exec(conn, f"install -d -m 0700 {base}")
    metas = []
    for p in paths:
        sha = (await _exec(conn, f"sha256sum {shlex.quote(p)}")).stdout.split()[0]
        await _exec(conn, f"cp -p {shlex.quote(p)} {base}/$(basename {shlex.quote(p)})")
        metas.append({"path": p, "sha256": sha})
    meta = {"correlation_id": correlation_id, "files": metas}
    await _exec(conn, f"cat > {base}/meta.json <<'EOF'\n{json.dumps(meta)}\nEOF")
    return base, op_id
```

- [ ] **Step 3: 实现 `apply_patch` 三阶段**

> 下文为示意伪代码，`_validate / _atomic_apply` 在同文件实现；`pool` 与 `correlation_id` 由 dispatcher 注入。

```python
async def apply_patch(args, *, pool, correlation_id: str):
    if args.action == "rollback":
        return await _rollback(args, pool=pool, correlation_id=correlation_id)
    # 1. validate dry-run（diff 解析、目标路径存在），失败时仍要写审计
    plan = await _validate(args.patch, pool=pool, host=args.host)
    # 2. backup
    async with pool.acquire(args.host) as conn:
        backup_path, op_id = await make_backup(
            conn=conn, paths=plan.touched_paths, correlation_id=correlation_id,
        )
        # 3. atomic apply：写 tmp 同分区，fdatasync，rename
        await _atomic_apply(conn=conn, plan=plan, backup_path=backup_path)
    return ToolResult(ok=True, host=args.host, exit_code=0, duration_ms=0,
                      truncated=False, cursor=None, summary=f"patch {len(plan.touched_paths)} files",
                      correlation_id=correlation_id,
                      data={"operation_id": op_id, "backup_path": backup_path,
                            "bytes_changed": plan.bytes_changed})
```

`_atomic_apply` 失败保证不留半文件：tmp 文件写完 fsync → `mv -T` 原子覆盖；任一步抛错则清理 tmp 不动原文件。

`rollback`：从 `state.db` `operation` 表查出 op_id，校验 backup 存在 → 重新 PolicyEngine（risk=high）→ 拒绝时仍写审计 → 通过则 `cp -p` 覆盖回原路径，envelope `data.rolled_back_from=op_id`。

- [ ] **Step 4: `write_file` / `transfer_file` / `manage_file`**

`write_file` 默认 `features.write_file=false`；启用时 `mode=overwrite` 在 `plan_action` 阶段把 `risk` 升一档（`medium → high`）。

`transfer_file(direction=up|down)` 用 asyncssh.SFTPClient 流式 chunk（默认 256KB），envelope `data.bytes_transferred`。

`manage_file(action=delete|move|chmod|chown)` per-action risk：`delete=high, chown=high, move=medium, chmod=medium`。

- [ ] **Step 5: 备份保留期清理**

注册到 task system：每日凌晨扫 `/tmp/ssh-mcp/backups/` 删 mtime > `server.yaml.backup_retention_days`（默认 7）的目录。

- [ ] **Step 6: 注册 ToolContract + 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_file_ops.py -v
git add src/ssh_mcp/operations/file_ops/ src/ssh_mcp/utils/operation_id.py
git commit -m "operations: add 7 file ops with backup/rollback and atomic apply"
```

---

## Task 14: 网络排障（capability: network-diagnostics）

**Files:**
- Create: `src/ssh_mcp/operations/network/{probe_network,get_network_info,capture_packets}.py`
- Test: `tests/integration/test_network.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_probe_tls(harness):
    out = await harness.call("probe_network", host="vps", mode="tls", target="example.com:443")
    assert out["data"]["protocol"] in {"TLSv1.2","TLSv1.3"}
    assert out["data"]["cert_chain"][0]["subject"]
async def test_target_not_in_allowlist(harness):
    r = await harness.call("probe_network", host="vps", mode="tcp", target="10.0.0.1:22")
    assert r["error"]["code"] == "POLICY_DENIED_TARGET"
async def test_packet_capture_truncated_by_policy(harness, packet_capture_enabled):
    out = await harness.call("capture_packets", host="vps", filter="port 80",
                             duration=300, max_packets=100000)
    assert out["data"]["truncated_by_policy"] is True
    assert out["data"]["effective_duration"] == 60
    assert out["data"]["effective_max_packets"] == 5000
async def test_firewall_counters_redacted(harness):
    out = await harness.call("get_network_info", host="vps", kinds=["firewall_nft"])
    assert "<REDACTED>" in out["data"]["firewall_nft"]
```

- [ ] **Step 2: 实现 `probe_network` 6 mode**

每 mode 一个子 handler，result_schema 显式声明：

| mode | argv | result fields |
|------|------|---------------|
| ping | `ping -c 5 -W 2 <t>` | rtt_ms_avg/min/max, loss_pct |
| traceroute | `traceroute -n -w 2 <t>` | hops[].{ip,rtt_ms} |
| dns | `dig +short <t>` | records[].{type,value} |
| tcp | `nc -z -w 3 host port` | reachable, latency_ms |
| http | httpx GET | status, headers_redacted, ttfb_ms |
| tls | python ssl 握手 | protocol, cipher, cert_chain[].subject |

PolicyEngine 第 2 段 allowlist 同时校验 `network_policy.allowed_targets`（domain glob 或 CIDR）。

- [ ] **Step 3: 实现 `get_network_info` 10 kinds**

`kinds=[interfaces, routes, sockets, conntrack, addresses, ports, firewall_nft, firewall_iptables, forwarding, firewall_policy]`，默认 `[interfaces, routes, addresses, ports]`。

`firewall_*` 输出过 `redact` 流水线把 `counter packets N bytes M` 段替换为 `<REDACTED>`。

- [ ] **Step 4: 实现 `capture_packets`**

默认 `features.packet_capture=false`。启用时 PolicyEngine 改写 `duration=min(duration,60)`、`max_packets=min(max_packets,5000)`，envelope 标 `truncated_by_policy=true` + `effective_*` 字段。

- [ ] **Step 5: 注册 ToolContract + 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_network.py -v
git add src/ssh_mcp/operations/network/
git commit -m "operations: add probe_network (6 modes) + get_network_info + capture_packets"
```

---

## Task 15: 批量与长任务

**Files:**
- Create: `src/ssh_mcp/operations/batch/{batch_run,compare_hosts}.py`
- Create: `src/ssh_mcp/store/{base.py,sqlite_task_store.py,schema.sql}`
- Create: `src/ssh_mcp/operations/task/{manage_task,get_task}.py`
- Test: `tests/integration/test_batch_and_tasks.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_canary_fail_fast_stops_batch(harness, three_hosts_one_broken):
    out = await harness.call("batch_run", preset="systemctl_status",
                             hosts=["a","b","c"], mode="run", concurrency=2,
                             canary={"n":1,"fail_fast":True})
    assert out["data"]["aborted"] is True
    assert len(out["data"]["completed_hosts"]) == 1

async def test_features_batch_mutation_off_blocks_mutation(harness):
    r = await harness.call("batch_run", preset="systemctl_restart_nginx",
                           hosts=["a","b"], mode="run")
    assert r["error"]["code"] == "POLICY_DENIED_FEATURE_DISABLED"

async def test_get_task_pagination(harness, long_task_id):
    out = await harness.call("get_task", task_id=long_task_id, include=["output"])
    assert out["data"]["cursor"]
    out2 = await harness.call("get_task", task_id=long_task_id, include=["output"], cursor=out["data"]["cursor"])
    assert out2["data"]["output"] != out["data"]["output"]

async def test_recovered_marked_on_restart(harness, prepared_running_task_in_db):
    await harness.restart_server()
    out = await harness.call("get_task", task_id=prepared_running_task_in_db)
    assert out["data"]["recovered"] is True

async def test_max_duration_times_out(harness, long_running_preset_2s, frozen_policy_max_duration_minutes_0):
    # 用 policy.yaml.task.max_duration_minutes=0（向上取最小执行单元）+ 2s preset，确保 3s 内触发超时
    out = await harness.call("manage_task", action="run",
                             preset=long_running_preset_2s, host="vps")
    task_id = out["data"]["task_id"]
    await asyncio.sleep(3)
    final = await harness.call("get_task", task_id=task_id)
    assert final["data"]["status"] == "timeout"
    assert final["data"]["cancel_reason"] == "MAX_DURATION_EXCEEDED"

async def test_manage_task_cancel_sets_canceled(harness, long_running_preset_60s):
    out = await harness.call("manage_task", action="run",
                             preset=long_running_preset_60s, host="vps")
    task_id = out["data"]["task_id"]
    await harness.call("manage_task", action="cancel", task_id=task_id)
    final = await harness.call("get_task", task_id=task_id)
    assert final["data"]["status"] == "canceled"
```

- [ ] **Step 2: 写 `TaskStore` schema 与 sqlite 实现**

```sql
-- src/ssh_mcp/store/schema.sql
CREATE TABLE IF NOT EXISTS task (
  task_id TEXT PRIMARY KEY,
  preset TEXT, hosts_json TEXT,
  mode TEXT,
  status TEXT,  -- running | completed | failed | canceled | timeout | recovered
  started_at TEXT, ended_at TEXT,
  cursor TEXT, recovered INTEGER DEFAULT 0,
  cancel_reason TEXT  -- MAX_DURATION_EXCEEDED | USER_CANCEL | SERVER_SHUTDOWN | null
);
CREATE TABLE IF NOT EXISTS task_output (
  task_id TEXT, seq INTEGER, line TEXT,
  PRIMARY KEY(task_id, seq)
);
```

`SqliteTaskStore` 接口：`create / update_status / append_output / get / list / mark_recovered`。

- [ ] **Step 3: 实现 `batch_run` 与 `canary fail_fast`**

```python
async def batch_run(args):
    canary_hosts = args.hosts[:args.canary["n"]]
    rest = args.hosts[args.canary["n"]:]
    completed = []
    for h in canary_hosts:
        r = await _run_one(args.preset, h)
        completed.append(r)
        if not r.ok and args.canary["fail_fast"]:
            return ToolResult(ok=False, data={"aborted": True, "completed_hosts": completed})
    sem = asyncio.Semaphore(args.concurrency)
    async def _run_with_sem(h):
        async with sem: return await _run_one(args.preset, h)
    results = await asyncio.gather(*[_run_with_sem(h) for h in rest])
    return ToolResult(ok=True, data={"aborted": False, "completed_hosts": completed + list(results)})
```

`features.batch_mutation=false` 时 PolicyEngine 校验 preset 是否 readonly，非 readonly 直接 deny。

- [ ] **Step 4: 实现 `compare_hosts`**

`dimensions ⊆ {system_info, services, file_hashes, network_info, package_versions}`；并行采集后做 diff，envelope `data.diffs[].{dimension, key, values_per_host}`。

- [ ] **Step 5: 实现 `manage_task` / `get_task` + 启动 recovered + max_duration**

`manage_task(action=run|cancel|cleanup)`：`run` 创建 task 异步调度；`cancel` 优雅 set event。

启动期：`store.list(status='running')` → 全部标 `recovered=1`。

`policy.yaml.task.max_duration_minutes` → 启动后台监视协程，超时把 task `status` 置为 `timeout`、`cancel_reason="MAX_DURATION_EXCEEDED"`，并取消执行协程。

- [ ] **Step 6: 注册 ToolContract + 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_batch_and_tasks.py -v
git add src/ssh_mcp/operations/batch/ src/ssh_mcp/operations/task/ src/ssh_mcp/store/
git commit -m "operations: add batch_run (with canary), compare_hosts, sqlite task store"
```

---

## Task 16: Resources 与 Prompts

**Files:**
- Create: `src/ssh_mcp/resources/{router.py,hosts.py,policy.py,commands.py,audit.py,runbooks.py}`
- Create: `src/ssh_mcp/prompts/{registry.py,builtins/*.md}`
- Test: `tests/integration/test_resources_and_prompts.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_resources_list_filters_invisible_audit(http_client_non_ops):
    r = await http_client_non_ops.call("resources/list")
    assert not any(x["uri"].startswith("ssh://audit/") for x in r["resources"])

async def test_audit_recent_redacted_and_caller_filtered(http_client_dev):
    r = await http_client_dev.call("resources/read", uri="ssh://audit/recent")
    rows = json.loads(r["contents"][0]["text"])
    assert all(row["user"] == "dev" for row in rows)

async def test_runbook_not_found(http_client):
    r = await http_client.call("resources/read", uri="ssh://runbooks/not-exist")
    assert r["error"]["code"] == "RESOURCE_NOT_FOUND"

async def test_prompts_list_returns_11(http_client_ops):
    r = await http_client_ops.call("prompts/list")
    names = {p["name"] for p in r["prompts"]}
    assert names == {"debug_service_failure","debug_port_unreachable","debug_high_cpu",
                     "debug_high_memory","debug_disk_full","debug_nginx_config",
                     "debug_postgres_connection","debug_firewall_forwarding",
                     "prepare_safe_change","post_change_validation","incident_report"}

async def test_prompt_renders_args(http_client_ops):
    r = await http_client_ops.call("prompts/get", name="debug_service_failure",
                                    arguments={"host":"test-vps","service":"nginx"})
    txt = r["messages"][0]["content"]["text"]
    assert "test-vps" in txt and "nginx" in txt
```

- [ ] **Step 2: 实现 10 个 Resource URI**

`router.py` 注册前缀 → handler 表；`resources/list` 返回 caller 可见集合。

`ssh://hosts` 复用 `list_hosts` 输出口径；`ssh://hosts/{host}` 走 `get_host_info`。

`ssh://policy` 输出当前快照摘要（host_allowlist 数 / risk_levels 数 / features 状态）；`ssh://policy/{host}` 输出该主机维度 effective policy。

`ssh://commands` 列 preset；`ssh://commands/{command}` 详情。

`ssh://audit/recent` 默认最近 200 行；`ssh://audit/search?...` 走 `audit/index`；两者输出经 redact + caller 过滤（非 ops 仅自见）。

`ssh://runbooks` 列 `runbooks/*.md` 元信息（解析首部 yaml frontmatter `name/title/summary/tags`）。`ssh://runbooks/{name}` 返回原文，缺失 → `RESOURCE_NOT_FOUND`。

- [ ] **Step 3: 写 11 个 prompt 模板**

每份 markdown 文件存 `src/ssh_mcp/prompts/builtins/<name>.md`，frontmatter 含 `name/description/arguments(JSON Schema)`，正文用 `$host` / `${service}` 占位（PEP 292 风格）。`registry` 启动期扫目录加载，`prompts/get` 用 `string.Template(text).safe_substitute(arguments)` 渲染——遇缺失参数保持原占位不报错，由 JSON Schema 校验在前置阶段把关。

> 注意：禁止使用 `{{host}}` Jinja 风格占位（与 `string.Template` 不兼容）；如未来需要条件/循环，再换 Jinja 并同步更新本节。

清单：`debug_service_failure / debug_port_unreachable / debug_high_cpu / debug_high_memory / debug_disk_full / debug_nginx_config / debug_postgres_connection / debug_firewall_forwarding / prepare_safe_change / post_change_validation / incident_report`。

- [ ] **Step 4: PolicyEngine 可见性接入**

`prompts/list` 与 `prompts/get` 经 PolicyEngine `is_prompt_visible(name, caller)`；不可见 → list 不返回，`get` → `POLICY_DENIED_PROMPT`。

- [ ] **Step 5: 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_resources_and_prompts.py -v
git add src/ssh_mcp/resources/ src/ssh_mcp/prompts/
git commit -m "resources/prompts: add 10 resource URIs and 11 builtin prompts with policy gating"
```

---

## Task 17: CLI 与启动入口

**Files:**
- Create: `src/ssh_mcp/cli/__main__.py`、`src/ssh_mcp/cli/serve.py`、`src/ssh_mcp/cli/reload.py`
- Test: `tests/integration/test_cli_lifecycle.py`

- [ ] **Step 1: 写失败测试**

```python
async def test_serve_startup_order_audit_unwritable(tmp_path):
    audit_dir = tmp_path / "ro"
    audit_dir.mkdir(); audit_dir.chmod(0o500)
    p = await asyncio.create_subprocess_exec(
        "uv","run","ssh-mcp","serve","--stdio",
        env={"SSH_MCP_AUDIT_DIR": str(audit_dir), **os.environ}, stderr=asyncio.subprocess.PIPE)
    rc = await p.wait()
    assert rc != 0
    assert b"AUDIT_DIR_NOT_WRITABLE" in (await p.stderr.read())

async def test_reload_atomically_swaps_policy(harness):
    await harness.write_policy({"version":1})
    await harness.call_admin_reload()
    snap1 = await harness.call("get_host_info", host="vps", include=["policy"])
    await harness.write_policy({"version":2})
    await harness.call_admin_reload()
    snap2 = await harness.call("get_host_info", host="vps", include=["policy"])
    assert snap1["data"]["policy"]["version"] != snap2["data"]["policy"]["version"]

def test_break_glass_flag_warns(capsys):
    rc = subprocess.run(["uv","run","ssh-mcp","serve","--stdio","--break-glass","--dry-init"],
                        capture_output=True)
    assert b"WARN" in rc.stderr and b"break-glass" in rc.stderr
```

- [ ] **Step 2: 实现 `serve` 启动顺序**

```python
def serve_main(argv):
    args = parse_args(argv)
    # parse_args 中 --config-dir 默认值：
    #   Path(os.getenv("SSH_MCP_CONFIG_DIR", "~/.ssh-mcp")).expanduser()
    cfg = load_config(global_dir=args.config_dir, cli=vars(args))
    _ensure_audit_writable(cfg.audit)       # 不可写 → exit 1 with code AUDIT_DIR_NOT_WRITABLE
    _migrate_sqlite(cfg.server.state_dir)   # state.db schema 迁移
    _probe_key_paths(cfg.hosts)             # YAML hosts 中的 key_path 可读探测
    deps = build_deps(cfg, break_glass=args.break_glass)
    if args.break_glass: log.warning("break-glass enabled")
    if args.dry_init: return 0
    pidfile = Path(cfg.server.state_dir) / "ssh-mcp.pid"
    _write_pidfile(pidfile)                  # mode 0600
    _install_sighup_handler(deps)           # SIGHUP → cfg.replace(load_config(...))
    try:
        asyncio.run(_run_transports(deps, args))
    finally:
        _remove_pidfile(pidfile)
```

- [ ] **Step 3: 实现 `reload` / `POST /admin/reload`**

两条路径：

1. **本机 CLI 路径**：
   - `serve` 启动后写 `pidfile = $SSH_MCP_STATE_DIR/ssh-mcp.pid`（mode 0600）；进程退出钩子清理。
   - `ssh-mcp reload [--pid-file PATH]`：默认从 `$SSH_MCP_STATE_DIR/ssh-mcp.pid` 读 pid，发送 `SIGHUP`。`--pid-file` 显式覆盖。
   - serve 内部注册 SIGHUP handler：调 `cfg.replace(load_config(global_dir=...))`，仅热替换 `policy/hosts/commands`，其它字段变更则 raise + 日志 ERROR 并保留旧快照。

2. **HTTP 远程路径**：
   - `ssh-mcp reload --admin-url http://127.0.0.1:8080 --token $SSH_MCP_BEARER`：POST `/admin/reload`，Header `Authorization: Bearer <token>`。
   - 服务端 `/admin/reload` endpoint 走与 `tools/call` 同一 bearer 鉴权中间件；缺/不匹配 token → 401（与业务一致），不进入 reload 逻辑。
   - **不允许**裸暴露：listen 只绑 `127.0.0.1` 或受信任网段；公网部署必须走反向代理 + mTLS。

两条路径都走 `cfg.replace()` 原子替换；任何阶段失败回滚到旧快照并写 audit `ADMIN_RELOAD_FAILED`。

- [ ] **Step 4: 串联其它 CLI 子命令**

`ssh-mcp trust <host>` / `ssh-mcp approve [--list] [<id>]` / `ssh-mcp audit query|export`，全部通过 `argparse` 子解析器在 `cli/__main__.py` 注册。

- [ ] **Step 5: 跑测试 + 提交**

```bash
uv run pytest tests/integration/test_cli_lifecycle.py -v
git add src/ssh_mcp/cli/
git commit -m "cli: add serve/reload/trust/approve/audit subcommands and startup order"
```

---

## Task 18: 可观测性、文档与发布

**Files:**
- Create: `src/ssh_mcp/observability/{logger.py,metrics.py}`
- Create: `docs/{README.md,CONFIG.md,AUDIT.md,APPROVAL.md,DEPLOY.md}`
- Test: `tests/e2e/test_smoke_all_modules.py`

- [ ] **Step 1: 写失败测试覆盖 metrics 端点 + summary 输出**

```python
async def test_metrics_endpoint(http_client):
    r = await http_client.raw_get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "ssh_mcp_tool_calls_total" in body
    assert "ssh_mcp_tool_duration_ms" in body

def test_startup_summary_printed(tmp_path):
    cfg_dir = tmp_path / "cfg"; cfg_dir.mkdir()
    audit_dir = tmp_path / "audit"; audit_dir.mkdir()
    state_dir = tmp_path / "state"; state_dir.mkdir()
    # 写最小 server.yaml 让 loader 不报错
    (cfg_dir / "server.yaml").write_text("listen: ':0'\n")
    env = {
        **os.environ,
        "SSH_MCP_CONFIG_DIR": str(cfg_dir),
        "SSH_MCP_AUDIT_DIR": str(audit_dir),
        "SSH_MCP_STATE_DIR": str(state_dir),
    }
    rc = subprocess.run(["uv","run","ssh-mcp","serve","--stdio","--dry-init"],
                        capture_output=True, env=env)
    out = rc.stderr.decode()
    assert "tools=" in out and "features=" in out and "audit=" in out
```

- [ ] **Step 2: 写 JSON formatter logger**

```python
# src/ssh_mcp/observability/logger.py
import logging, json, sys
class JsonFormatter(logging.Formatter):
    def format(self, record):
        from ssh_mcp.utils.correlation import current_correlation_id
        d = {"ts": self.formatTime(record), "level": record.levelname,
             "logger": record.name, "msg": record.getMessage(),
             "correlation_id": current_correlation_id()}
        return json.dumps(d, ensure_ascii=False)

def setup_logging():
    h = logging.StreamHandler(sys.stderr); h.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(h); logging.getLogger().setLevel(logging.INFO)
```

- [ ] **Step 3: 写极简 metrics**

```python
# src/ssh_mcp/observability/metrics.py
from collections import defaultdict

class Metrics:
    def __init__(self) -> None:
        self.counters: dict[tuple, int] = defaultdict(int)
        self.histograms: dict[tuple, list[float]] = defaultdict(list)

    def inc(self, name: str, **labels: str) -> None:
        self.counters[(name, tuple(sorted(labels.items())))] += 1

    def observe(self, name: str, value: float, **labels: str) -> None:
        self.histograms[(name, tuple(sorted(labels.items())))].append(value)

    def render_text(self) -> str:
        """渲染 Prometheus 0.0.4 text exposition format。"""
        lines: list[str] = []
        for (name, label_tup), value in self.counters.items():
            label_str = self._fmt_labels(label_tup)
            lines.append(f"{name}{label_str} {value}")
        for (name, label_tup), samples in self.histograms.items():
            label_str = self._fmt_labels(label_tup)
            count = len(samples); total = sum(samples)
            lines.append(f"{name}_count{label_str} {count}")
            lines.append(f"{name}_sum{label_str} {total}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _fmt_labels(label_tup: tuple) -> str:
        if not label_tup: return ""
        parts = [f'{k}="{Metrics._escape(v)}"' for k, v in label_tup]
        return "{" + ",".join(parts) + "}"

    @staticmethod
    def _escape(value: str) -> str:
        """Prometheus 0.0.4 label value 转义：\\ → \\\\、" → \\"、换行 → \\n。"""
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )
```

预定义指标：`ssh_mcp_tool_calls_total{tool,host,result}`、`ssh_mcp_tool_duration_ms{tool}`、`ssh_mcp_policy_decisions_total{decision}`、`ssh_mcp_audit_writes_total{result}`。

- [ ] **Step 4: stdio 启动 summary 打印**

`build_deps` 完成后 → `print(f"ssh-mcp ready tools={len(reg)} features={enabled_set} audit={cfg.audit.dir} store={cfg.server.state_dir}/state.db", file=sys.stderr)`。

- [ ] **Step 5: 写文档**

- `README.md`：60 秒上手（uv install / config / serve / 调用样例）。
- `CONFIG.md`：5 份 yaml 范例 + 配置矩阵（每字段：默认值、热重载是否、来源优先级）。
- `AUDIT.md`：审计字段表 + 查询/导出示例 + redact 行为说明。
- `APPROVAL.md`：闭环示意 + 4 反例错误码表 + break-glass 三重条件。
- `DEPLOY.md`：主机侧硬要求（专用低权用户 / sudoers 白名单 / forced command），明确 MCP 不自动配置。

- [ ] **Step 6: 端到端冒烟测试 + 覆盖率门槛**

`tests/e2e/test_smoke_all_modules.py` 用 docker compose 起 1 bastion + 2 target 容器，对 17 模块每个调一次最便宜的 happy path 工具，断言 envelope `ok=True`。

```bash
uv run pytest --cov=src/ssh_mcp --cov-report=term-missing tests/unit tests/integration
# 总体 ≥ 85%
uv run pytest --cov=src/ssh_mcp/policy --cov-fail-under=95 tests/unit/policy
```

- [ ] **Step 7: 发布 v0.1.0**

> 先 commit、跑测试通过、再打 tag/build；最后两步（push/release）需人工确认。

```bash
# 7.1 提交可观测性 / 文档 / e2e 改动（自动）
git add docs/ src/ssh_mcp/observability/ tests/e2e/
git commit -m "release: add observability, docs, e2e smoke and v0.1.0 prep"

# 7.2 跑完整测试套 + 覆盖率门槛通过（参见 Step 6）
uv run pytest --cov=src/ssh_mcp tests/unit tests/integration

# 7.3 构建 + 本地打 tag（自动）
uv build                       # 产 dist/ wheel + sdist
git tag -a v0.1.0 -m "v0.1.0"

# 7.4 推 tag（⚠️ 人工确认后执行）
git push origin v0.1.0

# 7.5 创建 GitHub Release（⚠️ 人工确认后执行）
gh release create v0.1.0 dist/* --generate-notes
```

---

## 自检清单

- [ ] tasks.md 18 节全部映射到 Task 1-18
- [ ] 16 个 capability spec 的所有 Requirement 在某 Task 中有对应步骤
- [ ] 9 个 Tool Contract 字段（name/description/input_schema/result_schema/readonly/risk_default/timeout_default/output_limits/approval_required_when）每业务 Task 显式注册
- [ ] ToolResult envelope 9 个基础字段（ok/host/exit_code/duration_ms/truncated/cursor/summary/correlation_id/data）+ `error` 平级 + `raw: bool` 可选字段在 Task 3 定义并被后续 Task 复用
- [ ] PolicyEngine 8 段栈 + 4 风险等级 + 5 features 默认全关 → Task 5
- [ ] approval 闭环 4 步 + token 复用/跨工具/过期/mismatch 4 反例 → Task 7
- [ ] file ops 三阶段（validate→backup→atomic apply）+ rollback 重新 PolicyEngine + ROLLBACK_BACKUP_MISSING → Task 13
- [ ] truncated_by_policy 字段命名一致（Task 14）
- [ ] ssh://audit/search 模板暴露 → Task 8（templates/list 测试）+ Task 16（实现）
- [ ] break-glass 三重条件 + forbidden 不可解锁 + audit risk 升级 → Task 5
- [ ] Coverage gates：total ≥ 85%，policy ≥ 95% → Task 18 Step 6




