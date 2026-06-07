## Context

ssh-mcp 旨在以 MCP 协议（Tools / Resources / Prompts）封装一组生产级 SSH 运维能力，供 Claude Code / Cursor / Codex 等 MCP 客户端调用。

- **范围**：基于 Notion「🖥️ SSH MCP 完整功能清单」17 大模块，一次性落地全部能力（brainstorm.md Q1）。
- **当前状态**：仓库已初始化、有 LICENSE 与 OpenSpec scaffold；尚无业务代码；本 change 为 0→1 基础工程。
- **核心约束**：
  - 严格默认安全姿态：不让 agent 直接拿 shell；不暴露私钥；不默认允许 root / 写 / 批量变更。
  - 所有动作可审计；高危动作可确认、可回滚。
  - 同时支持 stdio 与 Streamable HTTP 两种 transport；stdio 用于本地接入，HTTP 用于远程。
  - 鉴权三层模型：Client→Server / Server→SSH Host / SSH Host 内部权限——三层职责必须清晰切分。
- **Stakeholders**：项目主（chenjinfan）；下游 MCP 客户端用户；目标 SSH 主机的运维方。

## Goals / Non-Goals

**Goals:**

1. 完整覆盖 Notion 17 模块功能清单；工具粒度按文档「合并后」的列表设计（如 `query_journal` 吞 7 个）。
2. 同时暴露 Tools / Resources / Prompts，与 MCP 规范对齐。
3. 提供单一 `PolicyEngine` 安全闸门，业务代码无法旁路。
4. 提供完整审计链路（落盘 + sink 拓展点），高危动作经 `plan_action → manage_approval → apply_approved_action` 三段式工作流。
5. stdio + Streamable HTTP 双 transport 首版同时可用。
6. 关键扩展点（`CredentialProvider` / `AuditSink` / `ApprovalBackend` / `InventorySource`）首版只实现默认后端，但接口预留。

**Non-Goals:**

1. **多进程并发**：首版单进程纯异步；多进程协调留待后续。
2. **OpenTelemetry SDK 集成**：首版只用内置极简 metrics；YAGNI。
3. **OAuth 完整 issuer / refresh 流程**：首版 HTTP 只支持静态 Bearer token + 反向代理网关认证；OAuth 全流程见 Open Questions。
4. **外部凭据 / 审批 / 审计 sink 的具体实现**：首版只交付接口与默认后端（YAML / JSONL file / 本地 SQLite）。
5. **Web UI / 仪表盘**：CLI + MCP resources 已足够；不做独立前端。
6. **跨主机变更原子事务**：批量变更只提供 canary + concurrency，不保证全部成功或全部回滚。
7. **主机侧账号 / sudoers / forced command 的自动化配置**：那是部署侧文档化要求，MCP 不负责。

## Decisions

### D1：洋葱型分层架构

- **选择**：Transport → Dispatcher → **PolicyEngine（必经闸门）** → OperationHandler → Backends（ConnectionPool / CredentialProvider / AuditSink / ApprovalBackend / TaskStore）。
- **理由**：PolicyEngine 是唯一安全闸门，业务无法旁路；扩展点集中在最外层；每层可独立单测。
- **已考虑 alternative**：
  - 插件总线 + middleware：策略可被旁路、与「严格默认」冲突，过度设计。
  - 扁平 service 集合：每个 operation 手动调用 policy，极易漏调；扩展点无处安放。

### D2：实现语言与依赖管理

- **选择**：Python 3.11+ / 官方 `mcp` SDK / `uv` + `pyproject.toml` + `uv.lock`。
- **理由**：Python 运维生态最成熟；`uv` 解析快、锁质量高；3.11+ 提供 `TaskGroup` / `except*` / `Self`。
- **已考虑 alternative**：Node + 官方 SDK（运维脚本生态弱）；Go + 社区 SDK（SDK 不稳）；Poetry / pip+requirements（解析慢、锁质量低）。

### D3：SSH 库与运行时

- **选择**：`asyncssh` + 纯异步运行时；SQLite 走 `aiosqlite`；同步库用 `asyncio.to_thread`。
- **理由**：原生 asyncio，与 mcp SDK 同模型；连接池 / 并发 / 超时 / 取消天然支持。
- **已考虑 alternative**：paramiko（同步，需线程池，混部成本高）；openssh + subprocess（控制粒度差、跨平台不稳）。

### D4：Transport 范围与鉴权三层

- **选择**：stdio + Streamable HTTP 双 transport 同时上线。
  - **第 1 层（Client→Server）**：HTTP 走静态 Bearer token + 反向代理网关认证（首版）；stdio 走环境变量。
  - **第 2 层（Server→SSH Host）**：私钥 + `known_hosts` 强校验 + ProxyJump + 连接池。
  - **第 3 层（SSH Host 内部）**：MCP 不负责自动配置，但**部署文档强制要求**：专用低权用户、sudoers 白名单、可选 `forced command`。配置加载时若发现 `user: root`，启动期 WARN；可在 policy 中升级为拒启。
- **理由**：覆盖本地与远程接入；三层职责切分清晰，防止越权穿透。
- **已考虑 alternative**：仅 stdio（远程不可用）；HTTP 直接做 OAuth issuer（首版超工，推迟）。

### D5：默认安全姿态

- **选择**：严格默认。
  - `allow_write=false`（per host 显式开启）。
  - `features.arbitrary_shell=false`、`features.packet_capture=false`、`features.batch_mutation=false`。
  - 中高危操作必走 `plan_action → manage_approval(request) → 人工 approve → apply_approved_action(token, nonce)`，第 4 步 PolicyEngine **重新校验**，token + nonce 一次性。
- **理由**：与 Notion 文档原则完全对齐；任何放宽都需要在 policy.yaml 显式声明。
- **已考虑 alternative**：宽松默认（违背原则）；一律审批（影响只读体验）。
- **`confirmation_text` 模板**：`plan_action` 阶段由 PolicyEngine 按固定模板渲染：`确认在 {env} 主机 {host} 上 {action} {target}`（如「确认在 prod 主机 po0-cne 上 restart nginx」）。`apply_approved_action.confirmation_text` 入参必须**完整一致粘贴**该字符串才放行；任何字符差异立即 `APPROVAL_CONFIRMATION_MISMATCH` 并写审计。`high` 风险与 `break-glass` 模式强制启用；`medium` 由 `policy.yaml` 控制是否启用。

### D6：连接行为默认值

- **选择**：
  - 认证：默认仅密钥；密码认证由 `features.password_auth=false` 控制。
  - `known_hosts` 强校验（`StrictHostKeyChecking=yes` 等价），首次连接需显式 `trust_on_first_use` 开关。
  - 解析 `~/.ssh/config`（可被 host 配置覆盖）。
  - ProxyJump 链路通过 `bastion` 字段配置。
  - 连接超时 10s、命令默认超时 30s（per-tool 可覆盖）、keepalive 30s。
  - 全局并发上限 16；**单主机串行化**（`asyncio.Lock`）保证不会同时改一台机。
  - 凭据隔离：agent 只见 host alias，不接触私钥路径或密码。
- **理由**：与 Notion §2 全部要点对齐；默认值贴近 OpenSSH 习惯。

### D7：凭据 / 主机清单 / 审批 / 审计 / 任务存储

- **选择**：每条都是「默认实现 + 接口拓展点」组合。
  - `CredentialProvider`：默认 `YamlCredentialProvider`，接口预留 Vault / AWS Secrets Manager / 1Password。
  - `InventorySource`（用于 `sync_inventory`）：默认 YAML；接口预留 CMDB / Ansible inventory。
  - `AuditSink`：默认 `JsonlAuditSink`（按天轮转，本地落盘）；接口预留 Loki / ELK / Splunk。
  - `ApprovalBackend`：默认 `LocalApprovalBackend`（SQLite 持久化 + ssh-mcp CLI approve 子命令）；接口预留外部审批系统。
  - `TaskStore`：默认 `SqliteTaskStore`（`aiosqlite`，路径 `~/.ssh-mcp/state.db`）。
- **理由**：首版零外部依赖即可闭环；后续接入零侵入。
- **已考虑 alternative**：内存队列（重启丢任务）；直接外部 sink（首版引依赖太重）。

### D7.5：审计读侧能力（查询 / 导出）

- **背景**：Notion §14 显式要求「审计查询」与「审计导出（JSONL/CSV）」；D7 只覆盖了写侧（`AuditSink`），需要单列读侧。
- **选择**：
  - **CLI**：`ssh-mcp audit query --since <ts> --until <ts> --tool <name> --host <h> --user <u> --risk <lvl> --limit N`、`ssh-mcp audit export --format jsonl|csv --out <path>`。读路径直读 `JsonlAuditSink` 落盘文件 + 索引。
  - **Resource**：`ssh://audit/recent?limit=N`（已在 D10 row 16）扩展为 `ssh://audit/search?since=...&tool=...&...`，复用同一 PolicyEngine + redact 流水线。
  - **caller 过滤**：默认按 `per-user policy` 决定可见范围；ops 角色全见，其他角色仅自见（具体粒度见 OQ4）。
- **理由**：让审计真正可消费而不只可写；CLI 与 Resource 走同一查询层，避免读路径分裂。
- **边界声明**：审计查询 / 导出**不作为 MCP Tool 暴露**——属管理面能力，仅通过 CLI 与 `ssh://audit/*` Resource 提供，避免 agent 通过工具调用绕过 caller 过滤或被诱导拉取超量审计上下文。

### D8：PolicyEngine 规则栈

- **顺序**：`host_allowlist → command/path/service allowlist → arg_schema 校验 → deny rules → risk classify → approval gate → maintenance_window → rate_limit`，任一 deny 立停。
- **风险等级**：`low` / `medium` / `high` / `forbidden`；`medium+` 默认要审批，`high` 要求精确确认文案，`forbidden` 直接拒。
- **per-user / per-env override**：在全局策略基础上叠加；prod 默认更严。
- **maintenance window**：`policy.yaml` 可声明每主机或每环境的允许窗口；高危操作在窗口外直接 deny。
- **break-glass mode**：默认关；启用需 `policy.yaml` 显式声明 + 命令行 `--break-glass` + 双重确认；启用即升级审计 risk 级别并强制写紧急原因字段。

### D9：任意 shell 与高危命令防护

- **选择**：默认禁用；启用时强制叠加 8 道防护。
  - 命令黑名单（含但不限于 `rm -rf` / `mkfs` / `dd` / `shutdown` / `reboot` / `iptables -F` / `nft flush ruleset` / `docker system prune` / `userdel` / `passwd` / `chmod -R 777` / `chown -R` / `curl|sh` / `wget|sh`）。
  - 参数 schema 校验。
  - 人工审批必走。
  - 审计强制开启。
  - 命令超时强制有上限。
  - 输出大小强制有上限。
  - 禁止后台任务（`&` / `nohup` / `disown` / `setsid` 拒绝）。
  - 禁止交互式命令（不分配 TTY；`sudo -S` 类需走 preset）。
- **理由**：与 Notion §3.2 完全对齐；不在工具层而在 policy 层实现，便于审计与覆盖测试。

### D9.5：Tool Contract 标准结构

- **背景**：D10 能力地图只列了工具名与关键策略，spec / tasks 阶段每个 operation 自由发挥会导致字段缺失（漏 audit、漏 timeout、漏 schema）。需要固化每个 Tool 必须声明的契约字段。
- **必备字段**（精简至 9 个）：
  | 字段 | 说明 |
  |------|------|
  | `name` | 工具唯一标识，与 D10 能力地图一致 |
  | `description` | 单句中文描述，面向 agent |
  | `input_schema` | JSON Schema；含字段级 `x-redact` 标注哪些参数进 audit 时脱敏 |
  | `result_schema` | 在 D11.5 envelope 内的 `data` 字段子结构 |
  | `readonly` | bool，PolicyEngine 用来判断 `allow_write` 闸门 |
  | `risk_default` | `low`/`medium`/`high`/`forbidden`，per-action 工具按 action 拆分声明 |
  | `timeout_default` | 秒；可被 policy per-tool 覆盖（默认 30s） |
  | `output_limits` | `{max_bytes, max_lines}`，可被 policy 覆盖（默认 256 KiB / 1000 行） |
  | `approval_required_when` | 表达式：何时强制走审批（如 `risk >= medium` 或 `env == prod`） |
- **省略说明**：
  - `policy_checks` 不作为工具自描述字段——PolicyEngine 按规则栈自决，避免工具内声明与 policy.yaml 冲突。
  - `audit_fields` 与 `input_schema.x-redact` 合并，参数审计可见性由 schema 单一来源决定。
- **理由**：单一契约让 spec/tasks 阶段每个工具的验收清单可机械生成；防止"只落工具名"漏字段。

### D10：工具粒度与「能力地图」

- **选择**：按 Notion「吞并后」的工具粒度落地，每模块对应一个 operations 子模块。完整能力地图：

  | # | 模块 | 工具 / 资源 / Prompt | 关键策略 |
  |---|------|---------------------|----------|
  | 0 | MCP 基础 | initialize / notifications/initialized / tools/list / tools/call / resources/list / resources/read / resources/templates/list / prompts/list / prompts/get / stdio + HTTP | 三层鉴权 |
  | 1 | 主机资产 | `list_hosts` / `get_host_info` / `test_connection` / `sync_inventory` | host_allowlist |
  | 2 | SSH 连接 | （隐式于连接池，无独立工具） | 连接默认值 D6 |
  | 3.1 | 预设命令 | `list_command_presets` / `run_command_preset` | preset readonly 自描述 |
  | 3.2 | 任意 shell | `run_shell_command` / `run_shell_command_with_approval` / `validate_shell_command` / `explain_shell_command` | 默认关 + 8 道防护 |
  | 4 | 系统信息 | `get_system_info` / `get_system_metrics` | 只读、低风险 |
  | 5 | 服务管理 | `query_services` / `manage_service`(start/stop/restart/reload/enable/disable/daemon_reload) | service_allowlist + per-action 风险 |
  | 6 | 日志 | `query_journal`(file/journal × tail/grep/range/recent_errors) / `list_log_files` | path_allowlist + redact |
  | 7.1 | 文件只读 | `read_file` / `find_files` / `stat_file` | path_allowlist |
  | 7.2 | 文件写入 | `apply_patch`(apply/rollback) / `write_file` / `transfer_file`(up/down) / `manage_file`(delete/move/chmod/chown) | writable_paths + per-action 风险 |
  | 8 | 网络排障 | `probe_network`(ping/traceroute/dns/tcp/http/tls) / `get_network_info` / `capture_packets` | capture 默认关 + duration/max_packets 上限 |
  | 9 | 进程资源 | `query_processes` / `manage_process`(kill/nice) | per-action 风险 |
  | 10 | 批量 | `batch_run`(canary={n,fail_fast} + concurrency) / `compare_hosts`(dimensions ∈ `{system_info, services, file_hashes, network_info, package_versions}`) | 默认仅只读 |
  | 11 | 长任务 | `manage_task`(run/cancel/cleanup) / `get_task` | SQLite 持久化 |
  | 12 | 策略 | （配置层，非工具） | 见 D8 |
  | 13 | 审批 | `plan_action` / `manage_approval`(request/cancel/list) / `apply_approved_action` | token+nonce 一次性 |
  | 14 | 审计 | （AuditSink，非工具） | JSONL 默认 |
  | 15 | 输出处理 | （流水线，见 D11） | 截断 / 分页 / redact |
  | 16 | Resources | `ssh://hosts` / `ssh://hosts/{host}` / `ssh://policy` / `ssh://policy/{host}` / `ssh://commands` / `ssh://commands/{command}` / `ssh://audit/recent` / `ssh://audit/search` / `ssh://runbooks` / `ssh://runbooks/{name}` | 走同一套 PolicyEngine |
  | 17 | Prompts | `debug_service_failure` / `debug_port_unreachable` / `debug_high_cpu` / `debug_high_memory` / `debug_disk_full` / `debug_nginx_config` / `debug_postgres_connection` / `debug_firewall_forwarding` / `prepare_safe_change` / `post_change_validation` / `incident_report` | 模板可被 policy 限制可见性 |

- **理由**：单一来源对照 Notion 文档逐项，验收时可直接 grep 比对。

### D11：输出处理流水线

- **顺序**：`raw bytes → 编码探测（失败 → BinaryRejected）→ size check（超限截断 + truncated=true）→ secret redaction（pattern + custom regex）→ stdout/stderr 分离 → 分页（cursor 形式，按行）→ ToolResult.output / audit.output_summary（仅前 N 行）`。
- **默认值**：`max_output_bytes=256 KiB`；`max_output_lines=1000`；可被 policy per-tool 覆盖。
- **raw output option**：调用方可显式请求未脱敏原始输出，但 policy 层可禁用此开关；启用时审计强制标记 `raw=true`。

### D11.5：统一 ToolResult Envelope

- **背景**：D11 只覆盖 raw bytes 流水线，未约束最终返回结构。各工具自行设计 envelope 会让客户端无法统一处理 `truncated` / `cursor` / 错误重试。
- **Envelope schema**（所有 Tool 必返回）：
  ```json
  {
    "ok": true,
    "host": "test-vps",
    "exit_code": 0,
    "duration_ms": 123,
    "truncated": false,
    "cursor": null,
    "summary": "...",
    "correlation_id": "9f3c...",
    "data": { /* 工具特定，结构由 Tool Contract.result_schema 约束 */ }
  }
  ```
- **字段语义**：
  - `ok`：业务成功 = `true`；任何 `MCPError` = `false` 且伴随 `error: {code, message, retryable}` 字段（与 envelope 顶层平级）。
  - `host`：操作目标 host alias；不涉及主机的工具（如 `list_hosts`）置 `null`。
  - `exit_code`：命令类工具必填；非命令类置 `null`。
  - `duration_ms`：从 PolicyEngine 放行到 Operation 返回的耗时。
  - `truncated`：D11 流水线超限截断时为 `true`，配合 `cursor` 给下一页拉取标记。
  - `cursor`：分页 token；不分页或最后一页为 `null`。
  - `summary`：单句中文摘要，进 audit `output_summary`。
  - `correlation_id`：见 D13；贯穿日志 / 审计 / 错误。
  - `data`：工具特定结果，结构由 D9.5 `result_schema` 约束。命令类工具的 `data` 至少含 `{stdout, stderr}`。
- **约束**：
  - 命令类工具必须返回 `stdout` / `stderr` / `exit_code`（在 envelope 与 `data` 中各司其职）。
  - 非命令类工具仍必须返回 `ok` / `correlation_id`，`exit_code` 置 `null`。
  - `cursor` 分页仅适用于按行可切的输出（log / file / process list）；二进制或结构化结果不分页，超限直接 `truncated=true`。
  - `raw output option` 启用时 envelope 增加 `raw: true` 标记，并要求 policy 显式允许。
- **理由**：客户端单点解析；spec / tests 可直接断言 envelope 字段；审计字段从 envelope 一次性映射，免去每工具自描述。

### D12：Resources / Prompts 走同一套 Policy

- **Resources**：每个 URI 视为一次 read 操作，进入 PolicyEngine（host/path/audit 子规则）。`ssh://audit/recent` 走 redact 流水线，并按 caller 过滤可见字段。
- **Prompts**：`prompts/list` 与 `prompts/get` 同样过策略；prompt 里的可执行步骤渲染时，每步仍是普通 ToolCall，必经 PolicyEngine。
- **跨切面行为规范**：
  - **list 类（`tools/list` / `resources/list` / `prompts/list`）**：返回前按 caller policy 过滤可见项；不可见的工具/资源/prompt 在列表中**完全不出现**（不返回"被禁用"占位），避免泄露存在性。
  - **call 类（`tools/call` / `resources/read` / `prompts/get`）**：进入 Dispatcher 即生成 `correlation_id`，注入日志/审计/错误 data，贯穿整条调用链。
  - **transport 共用**：stdio 与 HTTP 共用同一份 registry / PolicyEngine / AuditSink 实例，不允许各自维护副本；Transport 层只负责 framing 与 caller_ctx 注入。
- **理由**：避免 Resources / Prompts 成为绕过 policy 的旁路；统一 list 过滤与 correlation_id 注入语义。

### D12.5：Runbooks 资源载体

- **背景**：Notion §16 的 `ssh://runbooks/{name}` 与 §17 的 11 个 `debug_*` Prompts **不是同一类对象**——前者是供模型阅读的运维手册（resource，markdown 文档），后者是结构化工作流模板（prompt）。
- **选择**：
  - 仓库内置 `runbooks/` 目录，每条手册一个 markdown 文件（如 `runbooks/network-debug.md`、`runbooks/nginx-debug.md`）。
  - `ssh://runbooks` 列出 `runbooks/*.md` 的元信息（name / title / summary / tags）；`ssh://runbooks/{name}` 返回对应文件原文。
  - Runbooks 与 Prompts 各自独立分发，可交叉引用：runbook markdown 内可链接 `prompt://debug_service_failure`；prompt 模板内可指向 `ssh://runbooks/network-debug` 作为补充阅读。
  - 手册更新走 git 提交流程；运行时只读，不支持工具内编辑。
- **理由**：明确载体后实现可直接照写；避免 runbooks 与 prompts 边界模糊导致重复或遗漏。

### D13：错误处理与可观测性

- **错误模型**：统一 `MCPError {code, message, retryable, data}`。前缀：`CONFIG_*` / `AUTH_*` / `POLICY_DENIED_*` / `APPROVAL_*` / `SSH_CONNECT_*` / `EXEC_*`（含 `EXEC_TIMEOUT` / `EXEC_OUTPUT_TOO_LARGE` / `EXEC_BINARY_OUTPUT`）/ `ARG_*` / `INTERNAL_*`。
- **审计触发**：`POLICY_DENIED_*` 必须写审计；`EXEC_TIMEOUT` 把已执行时长放 `data`。
- **日志**：stdlib `logging` + JSON formatter（默认 stderr，HTTP 模式可配文件）。
- **指标**：内置极简 counter / histogram；HTTP transport 暴露 `GET /metrics`；stdio 启动打印 summary。
- **`correlation_id`**：每条 ToolCall 生成，贯穿日志 / 审计 / 错误 data。
- **不引入**：OpenTelemetry SDK（YAGNI）。

### D13.5：文件变更、备份与回滚模型

- **背景**：Notion §7.2 要求 `apply_patch` 默认 `validate+backup` 后再 apply、`action=rollback` 复用同一工具。design.md 此前只在能力地图列了 `apply/rollback`，未约束备份位置、`operation_id` 生命周期、rollback 重新审批、校验失败的审计语义。本节固化文件变更类工具（`apply_patch` / `write_file` / `transfer_file` / `manage_file`）的统一模型。
- **operation_id 与备份位置**：
  - 每次文件变更生成 `operation_id`（与 `correlation_id` 不同——一次 ToolCall = 一个 correlation_id；一次实际写盘 = 一个 operation_id），格式 `op-{yyyyMMddHHmmss}-{ulid8}`。
  - 远端备份目录：`/tmp/ssh-mcp/backups/{operation_id}/`，由 MCP 在主机首次写入时按需创建（mode `0700`，owner = SSH 连接用户）。备份内容含 `meta.json`（原文件 path / size / sha256 / mtime / `correlation_id`）+ 原文件副本。
  - 备份保留期默认 7 天，由 `server.yaml.backup_retention_days` 控制；后台清理任务复用 `manage_task` 跑（启动期注册）。
  - 备份目录可被 `policy.yaml.file_policy.backup_root` 覆盖；不允许放入 `denied_paths`。
- **`apply_patch` 三阶段**：
  1. **validate**（默认开）：在远端 `dry-run` 应用 patch（`patch --dry-run` 或等价 diff 校验），失败立即返回 `EXEC_PATCH_INVALID`，**写文件不发生**，但**审计必须写**（含 patch 摘要与失败原因）。
  2. **backup**（默认开）：将目标文件复制到 `{backup_root}/{operation_id}/`，并把 `operation_id` 写入 envelope `data.operation_id`。
  3. **apply**：原子写入（同目录 `path.tmp` + `os.rename`，确保失败不留半文件）。
- **rollback 语义**：
  - 入参必须是 `operation_id`，不接受任意 patch 反转——避免误操作。
  - rollback **重新经过 PolicyEngine**（host/path 白名单 + risk + approval gate），即使原 apply 已审批，rollback 仍按 `medium`+ 风险评估；prod 环境 rollback 默认要审批。
  - rollback 也生成新的 `operation_id`，并把原 `operation_id` 记入 envelope `data.rolled_back_from`，形成可追溯链。
  - 备份缺失（已超保留期或被清理）→ `APPROVAL_*` 不发生，直接 `ROLLBACK_BACKUP_MISSING`。
- **风险与默认值**：
  - `apply_patch.apply` 默认 `medium`；`apply_patch.rollback` 默认 `medium`。
  - `write_file` **默认禁用**（`features.write_file=false`），启用时风险**不低于 medium**；`mode=overwrite` 比 `mode=append` 风险高一档。
  - `transfer_file.up` 默认 `medium`；`transfer_file.down` 默认 `low`（数据出主机，但不改主机状态）。
  - `manage_file` 按 action 单独评估：`delete=high` / `move=medium` / `chmod=medium` / `chown=high`。
  - 高危 action 强制走 `plan_action → manage_approval → apply_approved_action`，且 `confirmation_text` 必须含目标 path。
- **审计字段**：所有文件变更类工具的 envelope `data` 必含 `operation_id`、`backup_path`（无备份则 `null`）、目标 `path`、`bytes_changed`；审计映射这四项 + envelope 顶层。
- **理由**：把"备份/回滚"这条链路从工具层下沉到统一模型，避免 4 个工具各自实现导致语义漂移；`operation_id` 让事后审计与 rollback 操作有唯一句柄。

### D14：配置 schema 与热重载

- **文件**：`hosts.yaml` / `commands.yaml` / `policy.yaml` / `audit.yaml` / `server.yaml`。
- **加载顺序**：默认 → 全局 yaml → 环境变量 → CLI 参数；pydantic 校验，失败拒启。
- **`commands.yaml` 简写**：支持 `allowed_args: {arg_name: [enum_values]}`，等价于 JSON Schema `properties.{arg_name}.enum`。同一 preset 内 `allowed_args` 与显式 `arg_schema` 共存时，`allowed_args` 自动并入 schema 的 `enum` 约束；冲突时以更严者为准。
- **热重载**：`policy.yaml` / `hosts.yaml` / `commands.yaml` 通过 `ssh-mcp reload` 或 `POST /admin/reload` 原子替换不可变快照。
- **不可热重载**：transport / listen / oauth issuer / sqlite path / sink 后端类型——这些必须重启。

### D15：测试策略

- **框架**：`pytest` + `pytest-asyncio`（`asyncio_mode=auto`）。
- **不 mock asyncssh**：单元用 fake transport（`asyncssh.SSHServerConnection` 内存 server）；集成 + E2E 用 docker `linuxserver/openssh-server`。
- **policy 子规则一文件一测试**；17 类 operations 各自集成测试套件，每工具至少：happy path / policy deny / audit 记录 / 错误分类。
- **审批闭环 E2E**：plan → request → CLI approve → apply → 验证执行 + 审计。
- **覆盖率门槛**：unit + integration ≥ 85%，policy 包 ≥ 95%。
- **TDD 纪律**：plan.md 阶段由 `superpowers:test-driven-development` 钉死。
- **CI 节奏**：unit + integration 每次 PR；E2E（docker）仅 main 夜跑。

## Risks / Trade-offs

- [Risk] 17 模块单 change 体量大，proposal/tasks/plan 都会很厚，验收周期长 → **Mitigation**：tasks.md 按层分组（先 transport+policy+ssh，再 17 类 operations 顺次落），plan.md 用 micro-step + 频繁 commit；专职跟踪进度。
- [Risk] HTTP transport 鉴权复杂度（OAuth issuer / JWT / refresh）首版易超工 → **Mitigation**：首版只支持静态 Bearer token + 反向代理网关认证；OAuth 全流程留 Open Questions。
- [Risk] SQLite 单文件并发写串行 → **Mitigation**：仅 task store + approval store 写，QPS 低；多进程方案不在首版范围。
- [Risk] docker E2E 在 CI 启动慢 → **Mitigation**：E2E 仅 main 夜跑，PR 阶段跑 unit + integration（fake transport）。
- [Risk] Resources / Prompts 旁路 PolicyEngine → **Mitigation**：D12 明确二者必经 PolicyEngine；`ssh://audit/recent` 走 redact + caller 过滤。
- [Risk] 任意 shell + 抓包等高危误开 → **Mitigation**：`features.*` 全部默认关；启用需 `policy.yaml` 显式声明 + 启动期 WARN。
- [Risk] 主机侧 SSH 用户配置失误（root / 无 sudoers 限制） → **Mitigation**：配置加载时 `user: root` 强制 WARN；部署文档强制要求专用低权用户 + sudoers 白名单 + 可选 forced command；可在 policy 中升级为拒启。
- [Risk] 工具粒度合并后 per-action 风险升级（如 `manage_service` 的 daemon_reload）容易被低估 → **Mitigation**：D8 明确 per-action 风险等级，policy.yaml 必须按 action 单独声明，不允许整工具级 `risk: low`。
- [Risk] 凭据泄漏（YAML 私钥路径出现在审计 / 输出） → **Mitigation**：审计参数脱敏白名单制（只允许列出的字段进 audit.params）；输出脱敏 pattern 强制开启；agent 永不接触私钥路径。
- [Trade-off] 洋葱型分层导致简单工具调用栈 4-5 跳深 → 接受：换来安全闸门唯一性与可测性。
- [Trade-off] 全量 17 模块单 change 而非分阶段 → 接受：用户明确要求一次到位；后续不再拆分。
- [Trade-off] 首版无外部凭据 / 审批 / 审计 sink → 接受：通过接口预留零侵入接入；MVP 先闭环。

## Migration Plan

本 change 是 0→1 全新仓库工程化落地，**不涉及现有部署变更**，但首次发布需注意：

1. **依赖与运行时**：`uv sync` 安装；要求 Python 3.11+。
2. **首次启动校验顺序**：
   - 加载 `server.yaml` / `hosts.yaml` / `commands.yaml` / `policy.yaml` / `audit.yaml`，pydantic 校验失败立即拒启。
   - 校验 `AuditSink` 可写（不可写直接拒启）。
   - 校验 `TaskStore` SQLite 路径可写并迁移 schema。
   - HTTP transport 启动时校验 token 配置非空。
   - 探测每台 host 的 `key_path` 文件存在与权限（不可读 → 启动期 ERROR；可降级为 WARN 由 `server.yaml.strict_credentials` 控制）。
3. **首次连接信任**：默认 `known_hosts` 强校验；初次接入新主机需走 `ssh-mcp trust <host>` 子命令显式录入指纹。
4. **审批闭环验证**：发布前必须跑通 `plan_action → manage_approval(request) → ssh-mcp approve → apply_approved_action`。
5. **Rollback 策略**：纯新增项目，rollback = 停止进程 + 移除 systemd unit；用户数据（SQLite state、JSONL 审计）保留供事后审计。
6. **升级路径预留**：所有扩展点接口（CredentialProvider / AuditSink / ApprovalBackend / InventorySource）首版即定型；后续接入外部服务为「新增 backend 类」而非破坏性变更。

## Open Questions

- **OQ1（HTTP 鉴权终态）**：首版采用静态 Bearer token + 反向代理网关；MCP 授权规范要求的 OAuth issuer / JWT 校验 / refresh token 是否在 v0.2 内补齐？是否引入 `authlib`？
- **OQ2（break-glass 双签机制）**：紧急模式启用是否要求两人 CLI 操作（一人发起一人确认），还是单人 + 写 reason 即可？默认偏严还是偏松？
- **OQ3（`stat_file.compare_with` 跨主机比较）**：是否允许跨主机比较两个文件 hash？跨主机意味着同时持两条连接，是否给出独立 `compare_files_across_hosts` 工具或仅保留同主机内比较？
- **OQ4（Resources caller 过滤粒度）**：`ssh://audit/recent` 是否需要按 caller user 过滤为「只看到自己产生的审计」？还是 ops 角色看全部、其他角色看自己？per-user policy 如何与 audit 可见性叠加？
- **OQ5（Prompts 安全元数据）**：内置 11 个 runbook 是否需要每条声明所需 risk 上限 / 涉及的 host tag 范围，让 PolicyEngine 在 `prompts/get` 阶段先判可见性？
- **OQ6（外部审批 backend 接口形态）**：`ApprovalBackend` 抽象方法签名是否足以承接 PagerDuty / Slack interactive / Jira workflow 三类后端的差异？首版接口要不要预留 webhook 回调 URL？
- **OQ7（policy.yaml 维护体验）**：风险等级 / per-action / per-user / per-env / window 多维叠加易写错；是否需要 `ssh-mcp policy explain <tool> <host> <user>` 子命令做规则求解可视化？
- **OQ8（SQLite 路径与多实例）**：默认 `~/.ssh-mcp/state.db` 在多实例（同机两个 ssh-mcp 守护）会冲突；是否在 `server.yaml` 强制要求显式 `state_dir` 当 `--instance-id` 非默认时？
