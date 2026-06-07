## ADDED Requirements

### Requirement: 每次 ToolCall 写一行审计
PolicyEngine 决策完成后（无论放行或 deny）MUST 通过 `AuditSink` 写一行 JSONL 记录。记录字段 MUST 含：`time`（ISO8601）、`correlation_id`、`client`、`user`、`tool`、`host`、`params`（按 `input_schema.x-redact` 脱敏）、`risk`、`approved`、`approval_token`（若有）、`exit_code`、`duration_ms`、`error_kind`（若有）、`output_summary`（前 N 行）、`raw`（bool）。

#### Scenario: 放行调用
- **WHEN** 工具调用成功
- **THEN** audit JSONL 行 MUST 含 `approved=true`（或 `false` 若 risk<medium 不需审批）、`exit_code` 与业务结果一致

#### Scenario: deny 调用
- **WHEN** PolicyEngine 在任意阶段 deny
- **THEN** audit 行 MUST 含 `error_kind` 前缀 `POLICY_DENIED_*`，且 `exit_code=null`

#### Scenario: 参数脱敏
- **WHEN** 工具入参中含 `input_schema` 标注 `x-redact: true` 的字段
- **THEN** audit `params` 中该字段值 MUST 被替换为 `<REDACTED>`

### Requirement: JsonlAuditSink 默认按天轮转
`JsonlAuditSink` 默认 MUST 按 UTC 日期切分文件（路径 `~/.ssh-mcp/audit/audit-YYYY-MM-DD.jsonl`），文件 MUST 以 mode 0600 创建。启动期 MUST 探测 sink 可写，不可写直接拒启。

#### Scenario: 跨日切分
- **WHEN** 服务进程跨过 UTC 0 点
- **THEN** 后续审计 MUST 写入新日期文件，前一文件保持只读

#### Scenario: 不可写拒启
- **WHEN** 启动时 audit 目录不可写
- **THEN** 进程 MUST 立即退出并输出 `CONFIG_AUDIT_SINK_UNWRITABLE`

### Requirement: 审计读侧（CLI + Resource）
`ssh-mcp audit query --since --until --tool --host --user --risk --limit` 与 `ssh-mcp audit export --format jsonl|csv --out` MUST 直接读取 JSONL 文件 + 索引；同时 `ssh://audit/recent` 与 `ssh://audit/search?...` Resource MUST 返回同一查询层结果，二者 MUST 经过 redact 流水线 + caller 过滤。

#### Scenario: CLI 按工具过滤
- **WHEN** `ssh-mcp audit query --tool manage_service --since 2026-05-01`
- **THEN** stdout 仅含 `tool="manage_service"` 且 `time >= 2026-05-01` 的行

#### Scenario: CSV 导出
- **WHEN** `ssh-mcp audit export --format csv --out ./out.csv`
- **THEN** 输出文件首行为 CSV 表头，每行 1 条审计记录

#### Scenario: caller 过滤
- **WHEN** 非 ops 角色 user 调用 `ssh://audit/recent`
- **THEN** Resource 返回的行 MUST 仅含 `user=该caller` 的记录

### Requirement: 审计读侧不作为 MCP Tool 暴露
audit 查询 / 导出 MUST 不暴露为 MCP Tool（`tools/list` 不得列出 `query_audit` / `export_audit`），仅通过 CLI 与 `ssh://audit/*` Resource 提供。

#### Scenario: tools/list 不含审计读
- **WHEN** caller 调用 `tools/list`
- **THEN** 返回的 tools 列表 MUST 不含任何名为 `query_audit` / `export_audit` 的工具

### Requirement: AuditSink 接口拓展点
项目 MUST 定义 `AuditSink` 接口（`write / flush / close`），首版仅实现 `JsonlAuditSink`；接口 MUST 允许后续接入 Loki / ELK / Splunk（不在首版交付）。Sink fan-out 失败 MUST 不阻塞业务调用，但启动期不可写直接拒启。

#### Scenario: 写入失败异步
- **WHEN** 业务调用过程中 audit sink 写入抛 IOError
- **THEN** 业务 envelope 仍 MUST 正常返回；错误降级写 stderr 日志
