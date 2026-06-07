## ADDED Requirements

### Requirement: 8 段规则栈顺序固定
PolicyEngine MUST 按以下顺序执行规则：`host_allowlist → command/path/service allowlist → arg_schema 校验 → deny rules → risk classify → approval gate → maintenance_window → rate_limit`。任一阶段 deny SHALL 立即停止后续阶段，并返回对应 `POLICY_DENIED_*` 错误码。

#### Scenario: host 不在白名单
- **WHEN** 工具调用目标 host 不在 `hosts.yaml` 列表
- **THEN** PolicyEngine MUST 在 `host_allowlist` 阶段返回 `POLICY_DENIED_HOST`，不再执行后续 7 段规则

#### Scenario: deny 规则命中
- **WHEN** `run_command_preset` 的 argv 渲染结果命中 `policy.yaml.deny.command_patterns` 的 `rm -rf /`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_COMMAND` 且写审计

### Requirement: 风险等级与审批闸门
PolicyEngine MUST 支持 4 级风险（`low` / `medium` / `high` / `forbidden`）。`medium` 与 `high` 默认强制进入审批工作流；`high` 还 MUST 要求精确确认文案匹配；`forbidden` MUST 直接拒绝且不可被审批解锁。

#### Scenario: high 风险无审批 token
- **WHEN** caller 直接调用 `apply_patch.apply` 且未提供 `approval_token`
- **THEN** PolicyEngine MUST 返回 `APPROVAL_REQUIRED` 并指示走 `plan_action → manage_approval`

#### Scenario: forbidden 操作
- **WHEN** caller 启用了 break-glass 模式后调用某个 `risk: forbidden` 命令
- **THEN** PolicyEngine MUST 仍然返回 `POLICY_DENIED_FORBIDDEN`，break-glass 不可解锁此级

### Requirement: per-user / per-env override 叠加
`policy.yaml` MUST 支持在全局策略上叠加 per-user 与 per-env override；同一规则同时存在多层声明时 MUST 取最严者（更严的 risk、更小的 allowlist、更短的 window）。

#### Scenario: prod 环境收紧
- **WHEN** 全局允许 `manage_service.restart` 为 `medium`，但 `policy.yaml.envs.prod.upgrade_risk: {manage_service.restart: high}`
- **THEN** prod 主机调用 `manage_service.restart` MUST 按 `high` 走精确确认

### Requirement: maintenance window 窗口控制
`policy.yaml` MUST 允许声明每主机 / 每环境的允许变更窗口；高危操作（`risk >= medium`）在窗口外 MUST 直接 deny，只读操作不受窗口约束。

#### Scenario: 窗口外的 restart
- **WHEN** prod 主机配置窗口 `02:00-04:00`，caller 在 14:00 调用 `manage_service.restart`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_WINDOW`

#### Scenario: 窗口外的只读
- **WHEN** 同一主机在窗口外被调用 `get_system_info`
- **THEN** 调用 MUST 放行（`risk: low` 不受 window 约束）

### Requirement: features 开关默认关
配置 `features.arbitrary_shell` / `features.packet_capture` / `features.batch_mutation` / `features.password_auth` / `features.write_file` 默认 MUST 全部为 `false`；启用任一开关 MUST 在 `policy.yaml` 显式声明，且服务器启动时对每个被启用的开关写一行 `WARN` 日志。

#### Scenario: 未启用任意 shell
- **WHEN** `features.arbitrary_shell=false`，caller 调用 `run_shell_command`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_FEATURE_DISABLED`

### Requirement: break-glass 紧急模式
break-glass 模式 MUST 满足三重条件才能启用：`policy.yaml` 显式声明 + 启动 CLI `--break-glass` + 调用方写入紧急原因字段。启用后 MUST 升级所有审计行的 `risk` 标签且强制写 `break_glass_reason`。

#### Scenario: 启用 break-glass 仍拒 forbidden
- **WHEN** break-glass 启用，caller 调用任意 `risk: forbidden` 操作
- **THEN** 仍 MUST 返回 `POLICY_DENIED_FORBIDDEN`

#### Scenario: 缺紧急原因
- **WHEN** break-glass 启用但调用未带 `break_glass_reason`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_BREAKGLASS_REASON_MISSING`

### Requirement: rate_limit 限流
PolicyEngine MUST 支持 per-tool / per-user / per-host 三个维度的 token bucket 限流；超限 MUST 返回 `POLICY_DENIED_RATE_LIMIT`，错误信息含下次可用时间戳。

#### Scenario: 工具调用超频
- **WHEN** 同一 caller 在 1 秒内对同一工具调用超过 `policy.yaml.rate_limit.{tool}.qps`
- **THEN** 第超限次调用 MUST 返回 `POLICY_DENIED_RATE_LIMIT`
