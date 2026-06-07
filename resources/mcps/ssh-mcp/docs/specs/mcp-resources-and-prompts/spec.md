## ADDED Requirements

### Requirement: 资源 URI 族
项目 MUST 暴露以下 Resource URI：`ssh://hosts`、`ssh://hosts/{host}`、`ssh://policy`、`ssh://policy/{host}`、`ssh://commands`、`ssh://commands/{command}`、`ssh://audit/recent`、`ssh://audit/search`、`ssh://runbooks`、`ssh://runbooks/{name}`。每个 URI MUST 进入 PolicyEngine（host/path/audit 子规则）；不可见者 MUST 不在 `resources/list` 中出现。

#### Scenario: 列表过滤
- **WHEN** caller 不在 `ssh://audit/recent` 可见名单
- **THEN** `resources/list` 返回结果 MUST 不含该 URI 项

#### Scenario: hosts 资源
- **WHEN** caller 调用 `resources/read` URI=`ssh://hosts`
- **THEN** 返回 `contents` MUST 与 `list_hosts` 工具相同口径（不含私钥路径）

### Requirement: Runbooks 内置 markdown
`ssh://runbooks` MUST 列出仓库 `runbooks/*.md` 文件元信息（`name` / `title` / `summary` / `tags`）；`ssh://runbooks/{name}` MUST 返回对应 markdown 文件原文。Runbooks 与 Prompts 各自独立维护；运行时只读，不允许工具内编辑。

#### Scenario: 列出 runbooks
- **WHEN** caller 调用 `resources/read` URI=`ssh://runbooks`
- **THEN** 返回 JSON 数组，每元素含 `name` / `title` / `summary` / `tags`

#### Scenario: 缺失文件
- **WHEN** caller 调用 `ssh://runbooks/not-exist`
- **THEN** 返回 `RESOURCE_NOT_FOUND`

### Requirement: 内置 11 个 prompts
`prompts/list` MUST 返回以下 11 个内置 prompt：`debug_service_failure` / `debug_port_unreachable` / `debug_high_cpu` / `debug_high_memory` / `debug_disk_full` / `debug_nginx_config` / `debug_postgres_connection` / `debug_firewall_forwarding` / `prepare_safe_change` / `post_change_validation` / `incident_report`。每个 prompt 模板 MUST 在 `prompts/get` 时按 caller 入参渲染。

#### Scenario: 列出 prompts
- **WHEN** caller 调用 `prompts/list`
- **THEN** 返回数组长度为 11，每元素含 `name` / `description` / `arguments`（schema）

#### Scenario: 渲染 prompt
- **WHEN** caller 调用 `prompts/get` 名 `debug_service_failure`，args=`{host: "test-vps", service: "nginx"}`
- **THEN** 返回 `messages` 数组的内容 MUST 含 `host=test-vps` 与 `service=nginx`

### Requirement: Prompts 走 PolicyEngine
`prompts/list` 与 `prompts/get` MUST 经过 PolicyEngine 可见性过滤；prompt 模板内引用的 ToolCall 在客户端实际执行时 MUST 仍各自进入 PolicyEngine（不被 prompt 上下文豁免）。

#### Scenario: 不可见 prompt
- **WHEN** caller 不在某 prompt 的可见名单
- **THEN** `prompts/list` MUST 不含该 prompt；直接 `prompts/get` 返回 `POLICY_DENIED_PROMPT`

### Requirement: ssh://audit/recent redact
`ssh://audit/recent` 与 `ssh://audit/search` 返回前 MUST 经过 audit redact 流水线，并按 caller 过滤可见字段（非 ops 仅自见）。

#### Scenario: 非 ops 调用
- **WHEN** caller user 角色非 ops
- **THEN** 返回 `contents` MUST 仅含 `user=该caller` 的审计行
