## ADDED Requirements

### Requirement: manage_task 生命周期
`manage_task(action=run|cancel|cleanup, ...)` MUST 支持启动 / 取消 / 清理三个 action。`run` MUST 返回 `task_id`（ULID）并立即返回（异步执行）；`cancel(task_id)` MUST 优雅取消（asyncio cancel + SSH channel close）；`cleanup` MUST 清除 `state ∈ {completed, failed, canceled}` 且超过保留期的任务记录。

#### Scenario: 启动长任务
- **WHEN** caller 调用 `manage_task(action=run, tool="query_journal", args=...)`
- **THEN** envelope `data.task_id` 非空，`data.state="running"`；调用立即返回不阻塞

#### Scenario: 取消运行中任务
- **WHEN** task `t1` 运行中，caller 调用 `manage_task(action=cancel, task_id="t1")`
- **THEN** task 在 5s 内进入 `state=canceled`，对应 SSH 命令 SIGTERM/SIGKILL 已发送

### Requirement: get_task 状态与输出
`get_task(task_id?, filter?, include=[status,output])` 不传 `task_id` 时 MUST 返回任务列表（可按 `state` / `tool` / `started_after` 过滤）；传 `task_id` 时返回详情。`include=[output]` 时 MUST 经 redact + 截断流水线返回累计输出，并支持 cursor 分页。

#### Scenario: 列表查询
- **WHEN** `filter={state: "running"}`
- **THEN** 返回的所有任务 `state` MUST 等于 `running`

#### Scenario: 输出分页
- **WHEN** task 输出累计 5 MiB，调用 `get_task(task_id, include=[output], cursor=null)`
- **THEN** 第一次返回 `data.output` 不超过 `max_output_bytes`，envelope `truncated=true` 且 `cursor` 非空

### Requirement: SQLite 持久化与重启续命
任务记录 MUST 写入 `~/.ssh-mcp/state.db`（aiosqlite）；进程重启后 MUST 加载未结束（`state ∈ {pending, running}`）任务并标记为 `recovered`，由 caller 决定 cancel 或继续等待结果（已结束的远端进程不重连）。

#### Scenario: 重启后恢复
- **WHEN** ssh-mcp 重启时 SQLite 内有 1 条 `state=running` 任务
- **THEN** 启动后该任务 `state=recovered`，`get_task` 返回 `data.recovered=true`

### Requirement: 不允许无限运行任务
普通 `run_command_preset` / `query_journal` 等同步工具 MUST 受 `timeout_default` 上限约束；`manage_task(action=run)` 是唯一接受长时运行（默认上限由 `policy.yaml.task.max_duration_minutes` 控制，默认 60 分钟）的入口。

#### Scenario: 超时强制取消
- **WHEN** task 运行超过 `task.max_duration_minutes`
- **THEN** 任务 MUST 被自动 cancel，`state=timeout`
