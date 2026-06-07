## Why

项目当前为 0→1 状态：仓库仅有 LICENSE 与 OpenSpec scaffold，无业务代码；Notion「🖥️ SSH MCP 完整功能清单」17 模块定稿后，尚不可被 Claude Code / Cursor / Codex 等 MCP 客户端调用。

行业内 SSH 类工具普遍以「直接给 agent 开 shell」方式集成，存在凭据泄漏、误操作、无审计追溯三类系统性风险——与本项目「不让 agent 直接拿 shell、不暴露私钥、所有动作可审计、高危可审批可回滚」原则正面冲突。

本 change 一次性建立洋葱型分层 + 单点 PolicyEngine 安全闸门 + 三段式审批工作流 + 完整审计链路的基础工程，让 17 模块下游工具按 Tool Contract 模板填字段即可批量上线，不必每个工具重做安全治理；同时锁定 stdio + Streamable HTTP 双 transport、4 个扩展点接口（CredentialProvider / InventorySource / AuditSink / ApprovalBackend）与 TaskStore 后端，避免后续接外部系统时破坏性变更。

## What Changes

- **新增工程化基础**：`uv` + `pyproject.toml` + Python 3.11+ + `asyncssh` + `aiosqlite` + 官方 `mcp` SDK + `pydantic`；全新 `src/ssh_mcp/` 包按洋葱型分层组织。
- **新增 MCP 协议入口**：`initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `resources/list` / `resources/read` / `resources/templates/list` / `prompts/list` / `prompts/get` 9 个协议方法；stdio + Streamable HTTP 双 transport 共用同一份 registry / PolicyEngine / AuditSink。
- **新增 PolicyEngine**：`host_allowlist → cmd/path/service allowlist → arg_schema → deny rules → risk classify → approval gate → maintenance_window → rate_limit` 8 段规则栈；任一 deny 立停；`features.*` 默认全关（`arbitrary_shell` / `packet_capture` / `batch_mutation` / `password_auth` / `write_file`）。
- **新增审批工作流**：`plan_action → manage_approval(request) → 人工 approve → apply_approved_action(token, nonce)` 四步闭环；第 4 步 PolicyEngine 重新校验；`confirmation_text` 必须完整粘贴。
- **新增 Tool Contract 标准**：每个工具固化 9 必备字段（`name` / `description` / `input_schema` 含 `x-redact` / `result_schema` / `readonly` / `risk_default` / `timeout_default` / `output_limits` / `approval_required_when`）。
- **新增统一 ToolResult Envelope**：所有工具返回 `{ok, host, exit_code, duration_ms, truncated, cursor, summary, correlation_id, data}` 顶层 9 字段；命令类工具 `data` 内嵌 `stdout`/`stderr`。
- **新增文件变更/备份/回滚模型**：`apply_patch` 三阶段（validate → backup → apply），远端备份目录 `/tmp/ssh-mcp/backups/{operation_id}/`，rollback 重新经 PolicyEngine。
- **新增审计链路**：`JsonlAuditSink` 写侧（按天轮转）+ CLI `ssh-mcp audit query/export` 与 `ssh://audit/*` Resource 读侧；审计读侧不作为 MCP Tool 暴露。
- **新增 17 模块业务工具集**：覆盖主机资产 / SSH 连接 / 命令执行 / 系统巡检 / 服务管理 / 日志 / 文件 / 网络 / 进程 / 批量 / 长任务 / 审批 / Resources / Prompts。
- **新增 CLI**：`ssh-mcp serve`（启动）/ `reload`（热重载）/ `trust`（首次信任主机）/ `approve`（审批）/ `audit query|export`。
- **新增配置体系**：`hosts.yaml` / `commands.yaml` / `policy.yaml` / `audit.yaml` / `server.yaml` 共 5 份；pydantic 校验、热重载白名单。
- **新增测试基础设施**：`pytest` + `pytest-asyncio` + `asyncssh` 内存 server + docker `linuxserver/openssh-server`；覆盖率 unit+integration ≥ 85%、policy 包 ≥ 95%。

## Capabilities

### New Capabilities

- `mcp-protocol-surface`: MCP 9 协议方法入口 + stdio/HTTP 双 transport + 三层鉴权 + correlation_id 注入 + list 类按 caller policy 过滤可见性。
- `policy-engine`: 单点安全闸门，含 8 段规则栈、风险等级（low/medium/high/forbidden）、per-user/per-env override、maintenance window、break-glass、`features.*` 开关、高危命令黑名单。
- `tool-contract`: Tool Contract 9 必备字段标准 + 统一 ToolResult Envelope schema + 输出处理流水线（编码探测 / 截断 / redact / 分页）。
- `ssh-connection-pool`: asyncssh 连接池、密钥认证、known_hosts 强校验、ProxyJump、连接/命令超时、keepalive、单主机串行化、凭据隔离。
- `host-inventory`: 主机资产管理工具（`list_hosts` / `get_host_info` / `test_connection` / `sync_inventory`）+ `CredentialProvider` 与 `InventorySource` 接口及 YAML 默认实现。
- `command-execution`: 预设命令（`list_command_presets` / `run_command_preset`）+ 任意 shell 工具集（`run_shell_command*` / `validate_shell_command` / `explain_shell_command`）+ 8 道防护层。
- `system-inspection`: 系统/服务/进程只读查询（`get_system_info` / `get_system_metrics` / `query_services` / `query_processes`）。
- `service-and-process-mutation`: 主机状态变更（`manage_service` 7 action / `manage_process` kill+nice），按 action 单独评估风险。
- `log-query`: 统一日志查询（`query_journal` 跨 file/journal × tail/grep/range/recent_errors）+ `list_log_files`。
- `file-operations`: 文件只读（`read_file` / `find_files` / `stat_file`）+ 文件变更（`apply_patch` 三阶段 / `write_file` / `transfer_file` / `manage_file`）+ operation_id 备份/回滚模型。
- `network-diagnostics`: 主动探测（`probe_network` 6 模式）+ 本机网络快照（`get_network_info` 10 维）+ 抓包（`capture_packets` 默认关）。
- `batch-execution`: 多主机预设执行（`batch_run` canary+concurrency）+ 主机配置对比（`compare_hosts` 5 维）。
- `task-management`: 长任务生命周期（`manage_task` run/cancel/cleanup）+ 任务查询（`get_task` 状态/输出）+ SQLite 持久化。
- `approval-workflow`: 审批四步闭环（`plan_action` / `manage_approval` request|cancel|list / `apply_approved_action`）+ token+nonce 一次性 + `ApprovalBackend` 接口与 SQLite 默认实现。
- `audit-pipeline`: 审计写入（`AuditSink` 接口 + `JsonlAuditSink` 默认按天轮转）+ 审计读侧（CLI `audit query/export` + `ssh://audit/*` Resource）+ caller 过滤 + redact。
- `mcp-resources-and-prompts`: `ssh://hosts` / `ssh://policy` / `ssh://commands` / `ssh://audit` / `ssh://runbooks` 资源族（runbooks 来自仓库 `runbooks/*.md`）+ 11 个 `debug_*` / `prepare_safe_change` / `post_change_validation` / `incident_report` 内置 prompt。

### Modified Capabilities

- 无（仓库为 0→1 全新工程，`openspec/specs/` 当前为空，本 change 不修改既有 spec）。

## Impact

- **代码**：全新 `src/ssh_mcp/` 包，按层组织子模块（`transport/` / `server/` / `policy/` / `operations/` / `ssh/` / `credentials/` / `audit/` / `approval/` / `store/` / `resources/` / `prompts/` / `config/` / `utils/`）；新增 `runbooks/*.md` 内置运维手册。
- **依赖**：新增 `mcp`（官方 SDK）/ `asyncssh` / `aiosqlite` / `pydantic` / `pyyaml` / `httpx`（HTTP transport）/ `pytest` 系列；不引入 `authlib`，OAuth 完整流程留待 v0.2 评估（见 OQ1）；锁定 Python ≥ 3.11；`uv` + `uv.lock`。
- **API/Surface**：对外暴露 MCP 协议 9 方法 + ~25 个 Tool（按 D10 能力地图） + ~10 个 Resource URI + 11 个 Prompt + `ssh-mcp` CLI 5 个子命令。
- **配置**：新增 5 份 yaml；首次启动需 `ssh-mcp trust <host>` 录入指纹；`server.yaml.backup_retention_days` 默认 7 天清理远端备份。
- **运行时基础设施**：`~/.ssh-mcp/state.db`（SQLite，approval + task）+ `~/.ssh-mcp/audit/*.jsonl`（按天轮转）+ 远端 `/tmp/ssh-mcp/backups/{operation_id}/`（mode 0700）。
- **CI**：unit + integration 每 PR 跑（fake transport，无 docker 依赖）；E2E（`linuxserver/openssh-server`）仅 main 夜跑。
- **不影响**：现有部署（无）；不引入 OpenTelemetry SDK；不做 Web UI；不做跨主机原子事务；不自动配置主机侧账号 / sudoers / forced command（部署文档化要求）。
- **Rollback 策略**：纯新增项目，rollback = 停止进程 + 移除 systemd unit；用户数据（SQLite state、JSONL 审计、远端备份）保留供事后审计。
