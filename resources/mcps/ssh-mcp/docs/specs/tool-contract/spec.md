## ADDED Requirements

### Requirement: Tool Contract 9 必备字段
每个 Tool 注册到 registry 时 MUST 声明 9 个字段：`name`、`description`、`input_schema`（JSON Schema，字段级 `x-redact` 标注审计脱敏）、`result_schema`、`readonly`（bool）、`risk_default`（`low`/`medium`/`high`/`forbidden`）、`timeout_default`（秒）、`output_limits`（`{max_bytes, max_lines}`）、`approval_required_when`（表达式）。任一字段缺失 MUST 在启动期拒启。

#### Scenario: 缺字段的 Tool 注册
- **WHEN** registry 加载工具时发现某 Tool 缺 `risk_default`
- **THEN** 启动 MUST 失败并打印 `CONFIG_TOOL_CONTRACT_MISSING_FIELD: risk_default` 错误

#### Scenario: per-action 工具的 risk_default
- **WHEN** `manage_service` 工具按 action（start/stop/restart/...）拆分声明 risk
- **THEN** registry MUST 接受 dict 形式 `risk_default: {start: low, restart: medium, daemon_reload: high}`

### Requirement: 统一 ToolResult Envelope
所有工具调用返回的 ToolResult MUST 顶层包含 9 字段：`ok`（bool）、`host`（host alias 或 null）、`exit_code`（int 或 null）、`duration_ms`（int）、`truncated`（bool）、`cursor`（string 或 null）、`summary`（string）、`correlation_id`（string）、`data`（object，结构由 `result_schema` 约束）。错误时 MUST 附 `error: {code, message, retryable}` 平级字段且 `ok=false`。

#### Scenario: 命令类工具返回
- **WHEN** `run_command_preset` 成功执行 `df -h`
- **THEN** envelope MUST 含 `ok=true`、`exit_code=0`、`data.stdout` 与 `data.stderr` 字符串字段

#### Scenario: 非命令类工具返回
- **WHEN** `list_hosts` 成功返回主机清单
- **THEN** envelope `exit_code` MUST 为 `null`，`data` 为 host 对象数组

#### Scenario: 工具失败
- **WHEN** 工具因 `POLICY_DENIED_HOST` 失败
- **THEN** envelope MUST `ok=false` 且含 `error.code="POLICY_DENIED_HOST"`、`error.retryable=false`

### Requirement: 输出处理流水线
所有工具的输出 MUST 顺序经过：二进制识别（C0 控制字符 `\x00-\x08\x0b\x0c\x0e-\x1f` 出现 → `EXEC_BINARY_OUTPUT`） → 大小检查（超限 → 截断 + `truncated=true`） → 编码探测（UTF-8 优先，回退 latin-1） → secret redaction（pattern + custom regex） → stdout/stderr 分离 → 分页（按行 cursor）→ envelope 写出。`max_output_bytes` 默认 256 KiB，`max_output_lines` 默认 1000，可被 `policy.yaml` per-tool 覆盖。

#### Scenario: 输出超限
- **WHEN** 命令产生 1 MiB stdout
- **THEN** envelope `truncated=true`、`cursor` 非空、`data.stdout` MUST 不超过配置上限

#### Scenario: secret 命中
- **WHEN** 输出包含 `AKIA[A-Z0-9]{16}` AWS access key 模式
- **THEN** 返回的 stdout 与 audit `output_summary` 中该字段 MUST 被替换为 `<REDACTED>`

#### Scenario: 二进制输出
- **WHEN** 命令输出含 C0 控制字符（如 NUL `\x00`；ELF 二进制因内含大量 NUL 字节同样触发）
- **THEN** envelope `ok=false` 且 `error.code=EXEC_BINARY_OUTPUT`；非 UTF-8 但不含 C0 控制字符的文本（如 latin-1 编码日志）MUST 正常返回，不触发此错误

### Requirement: raw output 显式开关
工具调用方可在入参声明 `raw=true` 请求未脱敏原始输出，但 PolicyEngine MUST 可在 `policy.yaml` per-tool 禁用此开关；启用时 envelope MUST 增加 `raw: true` 字段，audit 行 MUST 强制标记 `raw=true`。

#### Scenario: policy 禁用 raw
- **WHEN** `policy.yaml.tools.run_command_preset.allow_raw=false`，caller 入参 `raw=true`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_RAW_OUTPUT`
