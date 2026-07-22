## ADDED Requirements

### Requirement: get_system_info 聚合
`get_system_info(host, include=[os,uptime,hostname,users,reboot_history])` MUST 按 include 选择性返回 OS/内核/架构 / hostname / uptime / 当前登录用户 / 最近重启历史；默认 `include=[os,uptime,hostname]`。

#### Scenario: 默认调用
- **WHEN** caller 不传 `include`
- **THEN** 返回 `data` MUST 含 `os` / `uptime_seconds` / `hostname` 三键，不含 `users` 或 `reboot_history`

#### Scenario: 重启历史
- **WHEN** `include=[reboot_history]`
- **THEN** `data.reboot_history` MUST 为时间戳数组（最近 N 条，N 由 policy 控制）

### Requirement: get_system_metrics 多指标
`get_system_metrics(host, kinds=[cpu,mem,disk,mounts,load,top_processes,kernel_logs])` MUST 按 kinds 返回各项指标；每类 kind 的 schema MUST 在 `result_schema` 显式声明；`kernel_logs` MUST 经 redact 与截断。

#### Scenario: cpu+mem 子集
- **WHEN** `kinds=[cpu,mem]`
- **THEN** `data.cpu` 含 `usage_pct` / `core_count`；`data.mem` 含 `used_bytes` / `total_bytes`

#### Scenario: 内核日志截断
- **WHEN** `kinds=[kernel_logs]` 且日志超 `max_output_lines`
- **THEN** envelope `truncated=true`，`data.kernel_logs` MUST 不超过上限

### Requirement: query_services 只读查询
`query_services(host, name?, filter={state?,enabled?}, include=[status,logs,health])` 不传 `name` 时 MUST 返回服务列表（可按 active/failed/enabled 过滤）；传 `name` 时返回单服务详情。`include=[logs]` 时 MUST 走 `query_journal` 同款 redact + 截断流水线。

#### Scenario: 列失败服务
- **WHEN** `filter={state: "failed"}`
- **THEN** 返回 `data.services` MUST 仅含 `ActiveState=failed` 服务

#### Scenario: 单服务健康
- **WHEN** `name="nginx"`、`include=[health]`
- **THEN** `data.health` 含 `is_active` / `is_enabled` / `last_active_exit_code`

### Requirement: query_processes 进程视图
`query_processes(host, filter?, format=flat|tree, include=[basic,files,ports])` MUST 默认 `format=flat`、`include=[basic]`。`include=[files]` 列出打开文件，`include=[ports]` 列出监听端口；进程数超 `max_output_lines` MUST 截断 + cursor 分页。

#### Scenario: 进程树
- **WHEN** `format=tree`
- **THEN** 返回 `data.tree` MUST 是嵌套对象，每节点含 `pid` / `cmdline` / `children`

#### Scenario: 端口归属
- **WHEN** `filter={name: "nginx"}`、`include=[ports]`
- **THEN** `data.processes[*].ports` MUST 列出该进程占用的 LISTEN 端口
