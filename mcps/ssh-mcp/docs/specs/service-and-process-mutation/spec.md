## ADDED Requirements

### Requirement: manage_service per-action 风险声明
`manage_service(host, action, name)` 的 `action ∈ {start, stop, restart, reload, enable, disable, daemon_reload}` MUST 在 `Tool Contract.risk_default` 按 action 单独声明风险等级；`policy.yaml` MUST 允许进一步覆盖每 action 的风险与 allowlist；不允许整工具级单一 risk。

#### Scenario: daemon_reload 默认 high
- **WHEN** caller 未配 `policy.yaml.tools.manage_service` 且调用 `action=daemon_reload`
- **THEN** PolicyEngine MUST 按 `high` 处理（精确确认文案 + 审批）

#### Scenario: 服务名不在 allowlist
- **WHEN** `policy.yaml.allowed_services=[nginx, postgresql]`，caller 调用 `name=mysql`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_SERVICE`

### Requirement: manage_service 输出标准化
`manage_service` 操作完成后 envelope `data` MUST 含 `action`、`name`、`pre_state`、`post_state`、`is_active`、`is_enabled`，无论成功失败；失败时 `error.code` 进入 envelope 错误字段，但 `data.pre_state` 仍 MUST 写入。

#### Scenario: restart 成功
- **WHEN** `action=restart, name=nginx` 成功
- **THEN** `data.pre_state="active"` / `data.post_state="active"` / `data.action="restart"`

### Requirement: manage_process per-action 风险
`manage_process(host, action, pid, ...)` 的 `action ∈ {kill, nice}` MUST 按 action 单独评估风险；`kill` 默认 `high`（要审批 + 精确确认 PID + 进程命令行预览），`nice` 默认 `medium`。

#### Scenario: kill PID 1
- **WHEN** caller 调用 `manage_process(action=kill, pid=1)`
- **THEN** PolicyEngine MUST 直接 deny（特殊保护 PID 列表，含 1 / 当前 ssh-mcp 自身 PID）

#### Scenario: nice 调整
- **WHEN** caller 调用 `manage_process(action=nice, pid=1234, value=10)` 在审批通过后
- **THEN** envelope `data.before_nice` 与 `data.after_nice` MUST 都填写

### Requirement: 高危确认文案含目标
所有 `manage_service` / `manage_process` 的高危 action（`risk >= high`）的 `confirmation_text` MUST 含目标 host alias + 目标 service/pid，PolicyEngine 按固定模板渲染：`确认在 {env} 主机 {host} 上 {action} {target}`。

#### Scenario: 模板渲染
- **WHEN** `plan_action(tool=manage_service, host=po0-cne, action=restart, name=nginx)`
- **THEN** 返回的 `confirmation_text` MUST 等于 `确认在 prod 主机 po0-cne 上 restart nginx`
