## ADDED Requirements

### Requirement: batch_run 多主机预设执行
`batch_run(preset, hosts, mode=run|dry-run, concurrency?, canary?)` MUST 仅接受**预设命令名**（不接受任意 shell）；`hosts` MUST 全部经 host_allowlist 校验；`concurrency` 默认 4、上限 16；`canary={n, fail_fast=true}` 时 MUST 先在前 `n` 台执行，失败时 `fail_fast=true` 立即停止后续 host。

#### Scenario: 仅只读 preset 默认放行
- **WHEN** `features.batch_mutation=false`，caller 调用 `preset=disk_usage`（readonly）
- **THEN** 放行执行；返回 `data.results[*]` 含每 host 的结果

#### Scenario: 默认拒变更 preset
- **WHEN** `features.batch_mutation=false`，caller 调用 `preset=service_restart`（非 readonly）
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_FEATURE_DISABLED`

#### Scenario: canary fail_fast
- **WHEN** `canary={n=2, fail_fast=true}`，第 2 台失败
- **THEN** 不再调度剩余 hosts，envelope `data.aborted=true` 且 `data.completed_hosts=2`

#### Scenario: dry-run
- **WHEN** `mode=dry-run, hosts=[h1,h2,h3]`
- **THEN** envelope `data.results[*]` 含 `rendered_argv` 与 `policy_decision`，无 SSH 实际连接

### Requirement: compare_hosts 多维度对比
`compare_hosts(hosts, dimensions)` MUST 支持 `dimensions ⊆ {system_info, services, file_hashes, network_info, package_versions}`；返回 `data.diff` MUST 按 dimension 分组列出差异（identical / different / only_in[*] 三种状态）。

#### Scenario: 系统信息对比
- **WHEN** `hosts=[h1, h2], dimensions=[system_info]`
- **THEN** `data.diff.system_info` 含逐字段（os/kernel/uptime）的对比结果
