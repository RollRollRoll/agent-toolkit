## ADDED Requirements

### Requirement: 预设命令清单查询
`list_command_presets(name?)` 不传 `name` 时 MUST 返回所有预设的概览（name / readonly / risk / argv 模板 / allowed_args 摘要）；传 `name` 时 MUST 返回该预设详情 + PolicyEngine 解释（生效的 deny 规则、是否走审批）。

#### Scenario: 全量列表
- **WHEN** caller 调用 `list_command_presets()`
- **THEN** 返回 `data.presets` MUST 与 `commands.yaml` 当前快照一致，按字母序排列

#### Scenario: 单条详情含策略解释
- **WHEN** caller 调用 `list_command_presets("disk_usage")`
- **THEN** 返回 `data.policy_explain` MUST 含 `risk` / `requires_approval` / `denied_reasons`（若有）

### Requirement: 预设命令执行
`run_command_preset(name, args, mode=run|dry-run)` MUST 严格按 `commands.yaml` 渲染 `argv`，参数 MUST 通过 `arg_schema` + `allowed_args` 双重校验。`mode=dry-run` MUST 仅返回渲染后的 argv 与策略判定，不实际 SSH 执行。`readonly` 由预设元数据自描述，PolicyEngine MUST 据此判定是否要审批。

#### Scenario: 参数枚举越界
- **WHEN** preset `service_status` 的 `allowed_args.service=[nginx,postgresql]`，caller 传 `service=mysql`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_ARG`，不进入 SSH 执行

#### Scenario: dry-run 输出
- **WHEN** caller 用 `mode=dry-run` 调用同一 preset
- **THEN** envelope `data` MUST 含 `rendered_argv` 与 `policy_decision`，但 `exit_code=null`、`stdout=""`

### Requirement: 任意 shell 默认禁用
`run_shell_command` / `run_shell_command_with_approval` / `validate_shell_command` / `explain_shell_command` 4 个工具 MUST 默认禁用（`features.arbitrary_shell=false`）；启用后 MUST 强制叠加 8 道防护：命令黑名单 / arg_schema / 必走审批 / 强制审计 / 命令超时上限 / 输出大小上限 / 禁后台任务（`&` `nohup` `disown` `setsid`）/ 禁交互 TTY。

#### Scenario: 默认调用拒绝
- **WHEN** `features.arbitrary_shell=false`，caller 调用 `run_shell_command`
- **THEN** 返回 `POLICY_DENIED_FEATURE_DISABLED`

#### Scenario: 黑名单命中
- **WHEN** 启用 arbitrary_shell 后 caller 提交 `rm -rf /var/log`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_COMMAND_BLOCKED` 并写审计

#### Scenario: 后台任务防护
- **WHEN** caller 提交 `nohup long-task &`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_BACKGROUND_PROHIBITED`

### Requirement: 解释与校验工具不实际执行
`validate_shell_command(cmd)` 与 `explain_shell_command(cmd)` MUST 仅做静态分析（risk 评估 / 影响摘要），不连接任何 host，不写 SSH 通道。

#### Scenario: 离线评估
- **WHEN** caller 调用 `validate_shell_command("systemctl restart nginx")`
- **THEN** envelope `host=null`、`exit_code=null`，`data.risk` 与 `data.reasons` 非空
