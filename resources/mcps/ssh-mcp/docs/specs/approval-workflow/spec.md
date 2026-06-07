## ADDED Requirements

### Requirement: 四步审批闭环
高危操作 MUST 走 `plan_action(...) → manage_approval(action=request, plan_id=...) → 人工 approve → apply_approved_action(approval_token, nonce, confirmation_text)` 四步；`apply_approved_action` 在 PolicyEngine 阶段 MUST **重新校验**全部规则（不复用 plan 阶段的判定结果），且 token + nonce 一次性使用。

#### Scenario: 复用 token
- **WHEN** 同一 `approval_token + nonce` 第二次调用 `apply_approved_action`
- **THEN** PolicyEngine MUST 返回 `APPROVAL_TOKEN_CONSUMED`

#### Scenario: token 跨工具
- **WHEN** 工具 A 的 token 被尝试用于工具 B
- **THEN** PolicyEngine MUST 返回 `APPROVAL_TOKEN_MISMATCH`

#### Scenario: 重新校验失败
- **WHEN** plan 时窗口在 `02:00-04:00`，apply 时已超出窗口
- **THEN** `apply_approved_action` MUST 返回 `POLICY_DENIED_WINDOW`，token 标记为 `consumed`（不允许复试）

### Requirement: plan_action 返回 risk 与 confirmation_text
`plan_action(tool, args)` 返回的 envelope `data` MUST 含 `plan_id`、`risk` 等级、`confirmation_text`（按 `确认在 {env} 主机 {host} 上 {action} {target}` 模板渲染）、`expected_argv`（命令类）或 `expected_changes`（文件类）；不实际执行 SSH。

#### Scenario: medium 风险计划
- **WHEN** caller 调用 `plan_action(tool=manage_service, host=test-vps, action=restart, name=nginx)`
- **THEN** `data.risk="medium"`，`data.confirmation_text` 与目标渲染模板严格一致

### Requirement: manage_approval 生命周期
`manage_approval(action=request|cancel|list, ...)` MUST 支持发起 / 取消 / 列出待审。`request` MUST 落 SQLite 持久化（含 `request_id` / `plan_id` / `risk` / `expires_at` / `confirmation_text` / `state`），并通过 `LocalApprovalBackend` 接受 CLI `ssh-mcp approve` 子命令的批准。`expires_at` 默认 30 分钟。

#### Scenario: 列出待审
- **WHEN** caller 调用 `manage_approval(action=list, filter={state: "pending"})`
- **THEN** 返回 `data.requests` 仅含 `state=pending` 且未过期项

#### Scenario: 审批过期
- **WHEN** request 超过 `expires_at` 后 caller 用对应 token 调用 apply
- **THEN** 返回 `APPROVAL_EXPIRED`

### Requirement: confirmation_text 完整一致
`apply_approved_action.confirmation_text` 入参 MUST 与 plan 阶段渲染的字符串**完整一致**（含空格 / 标点 / 顺序）；任何字符差异 MUST 返回 `APPROVAL_CONFIRMATION_MISMATCH` 并写审计。

#### Scenario: 多空格
- **WHEN** plan 文案 `确认在 prod 主机 po0-cne 上 restart nginx`，apply 入参多一个空格
- **THEN** 返回 `APPROVAL_CONFIRMATION_MISMATCH`

### Requirement: ApprovalBackend 接口
项目 MUST 定义 `ApprovalBackend` 接口（`request / list_pending / approve / deny / consume`），首版仅实现 `LocalApprovalBackend`；接口 MUST 允许后续接入 PagerDuty / Slack / Jira（不在首版交付）。

#### Scenario: 默认后端
- **WHEN** 启动时未配置 `approval.backend`
- **THEN** 使用 `LocalApprovalBackend`（SQLite + CLI `approve` 子命令）

### Requirement: break-glass 紧急模式约束
break-glass 模式启用 MUST 同时满足三重条件：(1) `policy.yaml` 显式声明启用；(2) 进程启动 CLI 带 `--break-glass`；(3) 调用方写入 `break_glass_reason` 字段。启用后 audit 行 MUST 标记 `break_glass=true` 并记录 `break_glass_reason`，且涉及操作的 `risk` 标签 MUST 升级一档。本 spec **不规定**是否跳过人工 approve 步骤——是否需要双签 / 单签 + 原因待 design.md OQ2 关闭后再以独立 spec 增量补齐。

#### Scenario: 缺紧急原因
- **WHEN** break-glass 启用但 `apply_approved_action` 调用未带 `break_glass_reason`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_BREAKGLASS_REASON_MISSING`

#### Scenario: forbidden 不可解锁
- **WHEN** break-glass 启用，caller 调用任意 `risk: forbidden` 操作
- **THEN** 仍 MUST 返回 `POLICY_DENIED_FORBIDDEN`，break-glass 不允许越过 forbidden

#### Scenario: 审计标记升级
- **WHEN** break-glass 启用下成功执行某 medium 操作
- **THEN** 对应 audit 行 `break_glass=true`、`break_glass_reason` 非空、`risk` 标签 MUST 升级一档（`medium → high`）
