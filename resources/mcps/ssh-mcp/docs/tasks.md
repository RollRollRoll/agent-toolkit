## 1. 工程化基础

- [ ] 1.1 创建 `pyproject.toml`（Python ≥ 3.11，描述、依赖、`ssh-mcp` console-script entry）
- [ ] 1.2 添加运行依赖：`mcp` / `asyncssh` / `aiosqlite` / `pydantic` / `pyyaml` / `httpx` / `anyio` / `python-ulid` / `starlette` / `uvicorn` / `bashlex`
- [ ] 1.3 添加测试/开发依赖：`pytest` / `pytest-asyncio`（asyncio_mode=auto） / `pytest-cov` / `ruff` / `mypy` / `types-PyYAML` / `pre-commit`
- [ ] 1.4 锁定依赖：`uv sync` 生成 `uv.lock` 并提交
- [ ] 1.5 建 `src/ssh_mcp/` 包骨架（`transport/` / `server/` / `policy/` / `operations/` / `ssh/` / `credentials/` / `audit/` / `approval/` / `store/` / `resources/` / `prompts/` / `config/` / `utils/`）
- [ ] 1.6 建 `tests/{unit,integration,e2e,fixtures,support}/` + 共享 conftest
- [ ] 1.7 配置 `ruff` + `mypy --strict`，加入 pre-commit
- [ ] 1.8 配置 GitHub Actions：PR 跑 ruff/mypy/unit/integration，main 夜跑 e2e（docker `linuxserver/openssh-server`）
- [ ] 1.9 编写 `runbooks/` 目录占位 + README，落入 5 份模板（network-debug / nginx-debug / postgres-debug / disk-full / firewall-debug）

## 2. 配置体系（pydantic 模型 + 加载顺序）

- [ ] 2.1 定义 `config.models`：`HostsConfig` / `CommandsConfig` / `PolicyConfig` / `AuditConfig` / `ServerConfig`
- [ ] 2.2 实现加载顺序：默认 → 全局 yaml → 环境变量 → CLI 参数；任何阶段失败 MUST 拒启
- [ ] 2.3 实现 `commands.yaml.allowed_args` → JSON Schema `enum` 自动并入逻辑（D14）
- [ ] 2.4 启动期 WARN：`hosts.yaml.<host>.user == "root"`；`server.yaml.strict_credentials=true` 时升为拒启
- [ ] 2.5 实现 `ssh-mcp reload` / `POST /admin/reload` 原子替换不可变快照（policy/hosts/commands）；其它项不可热重载
- [ ] 2.6 提供 `examples/config/` 含 5 份示例 yaml + `runbooks/` 引用范例
- [ ] 2.7 单元测试：默认值 / 优先级覆盖 / 校验失败拒启 / `allowed_args` 合并

## 3. 工具契约与输出流水线（capability: tool-contract）

- [ ] 3.1 定义 `ToolContract` dataclass：name / description / input_schema / result_schema / readonly / risk_default / timeout_default / output_limits / approval_required_when（9 字段）
- [ ] 3.2 注册期校验 9 字段齐全；缺一拒启 `CONFIG_TOOL_CONTRACT_MISSING_FIELD`
- [ ] 3.3 支持 per-action `risk_default: dict`（如 manage_service / manage_process / manage_file）
- [ ] 3.4 定义 `ToolResult` envelope dataclass（顶层 9 字段 + `error` 平级 + `raw: bool`）
- [ ] 3.5 实现输出流水线：二进制识别（C0 控制字符 → `EXEC_BINARY_OUTPUT` 错误 envelope）→ 字节截断（max_bytes）→ 编码探测（UTF-8 优先，回退 latin-1）→ secret redaction（pattern + custom regex）→ stdout/stderr 分离 → 分页（按行 cursor，超 max_bytes 退化为 bytes cursor）
- [ ] 3.6 实现 `raw=true` 开关：envelope 顶层 `raw=true` + audit 行标记；policy 禁用路径 deny
- [ ] 3.7 单元测试：每工具 envelope 字段断言 / 流水线各阶段（含二进制拒绝 / max_bytes / stderr 保留 / raw audit 标记）/ per-action risk dict

## 4. SSH 连接池（capability: ssh-connection-pool）

- [ ] 4.1 定义 `CredentialProvider` 接口（`resolve(host)` / `list_hosts()`），实现 `YamlCredentialProvider`
- [ ] 4.2 实现 `ssh.pool.ConnectionPool`：`acquire(host)` / `warmup` / `close_all`，单主机 `asyncio.Lock`
- [ ] 4.3 实现 known_hosts 强校验 + 指纹拒覆盖；提供 `ssh-mcp trust <host>` CLI 子命令录入
- [ ] 4.4 实现 ProxyJump（`bastion` 字段）+ `~/.ssh/config` 兜底解析
- [ ] 4.5 配置默认值：连接超时 10s / 命令超时 30s / keepalive 30s / 全局并发 16
- [ ] 4.6 错误码体系：`SSH_CONNECT_HOST_KEY_UNKNOWN` / `_MISMATCH` / `SSH_CONNECT_KEY_UNREADABLE` / `EXEC_TIMEOUT`
- [ ] 4.7 lint 规则禁止 `asyncssh.connect` 直接调用（全局 grep + 单测断言）
- [ ] 4.8 单元测试：用 `asyncssh.SSHServerConnection` 内存 server 跑握手 / 复用 / 串行化 / 超时取消
- [ ] 4.9 集成测试：docker `linuxserver/openssh-server` 跑 ProxyJump 与 known_hosts 拒覆盖

## 5. PolicyEngine（capability: policy-engine）

- [ ] 5.1 定义 `PolicyDecision`（allow / risk / reasons / needs_approval / approval_token / redact_rules）
- [ ] 5.2 实现 8 段规则栈骨架（host_allowlist → cmd/path/service allowlist → arg_schema → deny → risk classify → approval gate → window → rate_limit）
- [ ] 5.3 实现风险等级 4 级 + per-action 拆分声明读取
- [ ] 5.4 实现 per-user / per-env override（取最严者合并）
- [ ] 5.5 实现 maintenance window（含「只读不受 window 约束」例外）
- [ ] 5.6 实现 `features.*` 开关默认全关 + 启动期 WARN 已启用项
- [ ] 5.7 实现 break-glass 三重启用条件 + 审计 risk 升级 + forbidden 不可解锁（不规定是否跳过 approval，等 OQ2）
- [ ] 5.8 实现 rate_limit token bucket（per-tool / per-user / per-host）
- [ ] 5.9 实现策略热重载（原子快照替换）
- [ ] 5.10 单元测试：每子规则一文件一测试；deny 立停断言；覆盖率门槛 ≥ 95%

## 6. 审计链路（capability: audit-pipeline）

- [ ] 6.1 定义 `AuditEvent` schema + `AuditSink` 接口（write / flush / close）
- [ ] 6.2 实现 `JsonlAuditSink`：按 UTC 日期切分 `~/.ssh-mcp/audit/audit-YYYY-MM-DD.jsonl`，mode 0600
- [ ] 6.3 启动期可写探测；不可写直接拒启
- [ ] 6.4 实现 fan-out fail-safe（写失败仅降级日志，不阻塞业务）
- [ ] 6.5 实现 `input_schema.x-redact` 参数脱敏 + `output_summary` 取前 N 行
- [ ] 6.6 实现读侧索引（按 day/tool/host/user/risk 二级索引）
- [ ] 6.7 实现 CLI `ssh-mcp audit query --since/--until/--tool/--host/--user/--risk/--limit`
- [ ] 6.8 实现 CLI `ssh-mcp audit export --format jsonl|csv --out`
- [ ] 6.9 单元测试：跨日切分 / redact 命中 / fan-out 失败不阻塞 / CSV 导出表头一致

## 7. 审批工作流（capability: approval-workflow）

- [ ] 7.1 定义 `ApprovalRequest` + `ApprovalBackend` 接口（request / list_pending / approve / deny / consume）
- [ ] 7.2 实现 `LocalApprovalBackend`（aiosqlite + `~/.ssh-mcp/state.db`）
- [ ] 7.3 实现 `plan_action` 工具：渲染 `confirmation_text=确认在 {env} 主机 {host} 上 {action} {target}`，返回 `plan_id` / `risk` / `expected_argv|expected_changes`
- [ ] 7.4 实现 `manage_approval(action=request|cancel|list)` 工具，默认 `expires_at=30min`
- [ ] 7.5 实现 `apply_approved_action(approval_token, nonce, confirmation_text)`：PolicyEngine 重新校验 + token+nonce 一次性消费
- [ ] 7.6 实现 `confirmation_text` 字符级一致性校验，失败 `APPROVAL_CONFIRMATION_MISMATCH` 写审计
- [ ] 7.7 实现 CLI `ssh-mcp approve <request_id>` / `ssh-mcp approve --list`
- [ ] 7.8 集成测试：plan → request → CLI approve → apply 闭环；token 复用 / 跨工具 / 过期 / mismatch 各一例

## 8. MCP 协议入口（capability: mcp-protocol-surface）

- [ ] 8.1 集成官方 `mcp` SDK：注册 9 个方法 handler（`initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `resources/list` / `resources/read` / `resources/templates/list` / `prompts/list` / `prompts/get`）
- [ ] 8.2 `initialize` 响应 `capabilities` 声明 tools/resources（含 `listChanged`）/prompts
- [ ] 8.3 stdio transport 启动入口（`ssh-mcp serve --stdio`）
- [ ] 8.4 Streamable HTTP transport 启动入口（`ssh-mcp serve --http --listen :8080`）
- [ ] 8.5 HTTP 静态 Bearer token + 反向代理网关认证；缺失返回 401 不进 Dispatcher
- [ ] 8.6 list 类按 caller policy 过滤可见性（不可见不出现，不返 disabled）
- [ ] 8.7 call 类入 Dispatcher 即生成 `correlation_id`（ULID），贯穿 logging / audit / error
- [ ] 8.8 stdio + HTTP 共用单实例后端（registry / PolicyEngine / AuditSink / ApprovalBackend / TaskStore）
- [ ] 8.9 实现 `MCPError {code, message, retryable, data}` 统一错误模型
- [ ] 8.10 集成测试：双 transport 并发 / 401 / 未 init 调用 / list 过滤 / templates/list 含 `ssh://audit/search`

## 9. 主机资产管理（capability: host-inventory）

- [ ] 9.1 实现 `list_hosts(filter)`：tag / env 过滤；输出剔除 key_path/password
- [ ] 9.2 实现 `get_host_info(host, include=[basic,policy,inventory])`
- [ ] 9.3 实现 `test_connection(host)`：经 PolicyEngine；返回 latency_ms / auth_method / banner_redacted / fingerprint_sha256
- [ ] 9.4 定义 `InventorySource` 接口；首版仅实现 `YamlInventorySource`；接口 docstring 注明未来可接 CMDB / Ansible inventory，不注册运行时占位 backend
- [ ] 9.5 实现 `sync_inventory(source)` 工具
- [ ] 9.6 所有工具注册 `ToolContract` 9 字段并通过 registry 启动期校验
- [ ] 9.7 集成测试：4 个工具 happy path / policy deny / audit 字段断言

## 10. 系统巡检与日志（capabilities: system-inspection / log-query）

- [ ] 10.1 实现 `get_system_info(include=[os,uptime,hostname,users,reboot_history])`
- [ ] 10.2 实现 `get_system_metrics(kinds=[cpu,mem,disk,mounts,load,top_processes,kernel_logs])`
- [ ] 10.3 实现 `query_services(name?, filter, include=[status,logs,health])`
- [ ] 10.4 实现 `query_processes(filter?, format=flat|tree, include=[basic,files,ports])`
- [ ] 10.5 实现 `query_journal(source=file|journal, target, mode=tail|grep|range|recent_errors|excerpt, ...)`
- [ ] 10.6 实现 `list_log_files(path?)` 含越权过滤后返回空 + audit `filtered_outside_allowlist`
- [ ] 10.7 所有工具注册 `ToolContract` 9 字段并通过 registry 启动期校验
- [ ] 10.8 集成测试：每工具至少 happy / deny / audit / 错误分类 4 类

## 11. 命令执行（capability: command-execution）

- [ ] 11.1 实现 `list_command_presets(name?)`：返回详情含 `policy_explain`
- [ ] 11.2 实现 `run_command_preset(name, args, mode=run|dry-run)`：argv 渲染 + arg_schema + allowed_args 双校验
- [ ] 11.3 实现 `validate_shell_command(cmd)` / `explain_shell_command(cmd)`（不连 SSH）
- [ ] 11.4 实现 `run_shell_command` / `run_shell_command_with_approval`（默认禁用 + 8 道防护）
- [ ] 11.5 实现命令黑名单（`rm -rf` / `mkfs` / `dd` / `shutdown` / `reboot` / `iptables -F` / `nft flush ruleset` / `docker system prune` / `userdel` / `passwd` / `chmod -R 777` / `chown -R` / `curl|sh` / `wget|sh`）
- [ ] 11.6 实现后台任务防护（`&` / `nohup` / `disown` / `setsid` 拒）
- [ ] 11.7 实现交互 TTY 防护（不分配 PTY）
- [ ] 11.8 所有工具注册 `ToolContract` 9 字段并通过 registry 启动期校验
- [ ] 11.9 集成测试：黑名单 / 后台 / TTY / dry-run / arbitrary_shell 默认拒

## 12. 服务与进程变更（capability: service-and-process-mutation）

- [ ] 12.1 实现 `manage_service(action, name)` 7 个 action（start/stop/restart/reload/enable/disable/daemon_reload），per-action risk
- [ ] 12.2 envelope `data` 包含 `pre_state` / `post_state` / `is_active` / `is_enabled`，失败也写 `pre_state`
- [ ] 12.3 实现 `manage_process(action=kill|nice, pid, ...)`，PID 1 / 自身 PID 强制 deny
- [ ] 12.4 高危确认文案模板渲染含 host + service/pid
- [ ] 12.5 所有工具注册 `ToolContract` 9 字段（含 per-action `risk_default: dict`）并通过 registry 启动期校验
- [ ] 12.6 集成测试：daemon_reload 走审批 / kill 1 拒 / nice before-after / 服务名越白名单 deny

## 13. 文件操作（capability: file-operations）

- [ ] 13.1 实现 `read_file(path, mode=full|range|tail|grep)` / `find_files` / `stat_file(include=[basic,hash,compare_with])` 同主机内
- [ ] 13.2 实现 path 白名单（readable / writable / denied）+ `**/.env` 等 glob
- [ ] 13.3 实现 `apply_patch` 三阶段（validate dry-run → backup → atomic apply）
- [ ] 13.4 实现远端备份目录 `/tmp/ssh-mcp/backups/{operation_id}/`（mode 0700） + `meta.json` 写 `path/sha256/correlation_id`
- [ ] 13.5 实现 `operation_id` 生成 `op-{ts}-{ulid8}` + envelope `data.operation_id` / `backup_path` / `bytes_changed`
- [ ] 13.6 实现 `apply_patch(action=rollback, operation_id)`：重新经 PolicyEngine + `rolled_back_from`；备份缺失 `ROLLBACK_BACKUP_MISSING`
- [ ] 13.7 实现 `write_file(mode=overwrite|append)` 默认禁用 + `mode=overwrite` 风险升一档
- [ ] 13.8 实现 `transfer_file(direction=up|down)` 流式 chunk + `bytes_transferred`
- [ ] 13.9 实现 `manage_file(action=delete|move|chmod|chown)` per-action risk（delete=high, chown=high, move/chmod=medium）
- [ ] 13.10 实现备份保留期清理（注册到 task system，`server.yaml.backup_retention_days` 默认 7）
- [ ] 13.11 所有工具注册 `ToolContract` 9 字段（含 per-action `risk_default: dict`）并通过 registry 启动期校验
- [ ] 13.12 集成测试：validate 失败仍写审计 / atomic apply 不留半文件 / rollback 重新审批 / 备份缺失错误码

## 14. 网络排障（capability: network-diagnostics）

- [ ] 14.1 实现 `probe_network(mode ∈ {ping, traceroute, dns, tcp, http, tls})` + `network_policy.allowed_targets` 白名单
- [ ] 14.2 每 mode 的 result_schema 落地（rtt / cert_chain / dns_records 等）
- [ ] 14.3 实现 `get_network_info(kinds=10 项)` + 防火墙 counter 字段 redact
- [ ] 14.4 实现 `capture_packets(filter, duration, max_packets)` 默认禁用；启用时强制 duration ≤ 60、max_packets ≤ 5000，超限 `data.truncated_by_policy=true`
- [ ] 14.5 所有工具注册 `ToolContract` 9 字段并通过 registry 启动期校验
- [ ] 14.6 集成测试：tls 握手 / 目标越权 / packet capture 入参超限被改写

## 15. 批量与长任务（capabilities: batch-execution / task-management）

- [ ] 15.1 实现 `batch_run(preset, hosts, mode, concurrency<=16, canary={n,fail_fast})`
- [ ] 15.2 实现 canary fail_fast 终止；envelope 报告 `aborted` / `completed_hosts`
- [ ] 15.3 `features.batch_mutation=false` 时仅放行 readonly preset
- [ ] 15.4 实现 `compare_hosts(hosts, dimensions ⊆ {system_info, services, file_hashes, network_info, package_versions})`
- [ ] 15.5 定义 `TaskStore`；实现 `SqliteTaskStore`（aiosqlite，`~/.ssh-mcp/state.db`）
- [ ] 15.6 实现 `manage_task(action=run|cancel|cleanup)`：异步调度 + cancel 优雅取消
- [ ] 15.7 实现 `get_task(task_id?, filter?, include=[status,output])` + cursor 分页输出
- [ ] 15.8 启动期加载未结束任务标记 `recovered`
- [ ] 15.9 实现 `policy.yaml.task.max_duration_minutes` 强制超时取消
- [ ] 15.10 所有工具注册 `ToolContract` 9 字段并通过 registry 启动期校验
- [ ] 15.11 集成测试：canary 中断 / 重启 recovered / output 分页 / 超时取消

## 16. Resources 与 Prompts（capability: mcp-resources-and-prompts）

- [ ] 16.1 实现 10 个 Resource URI handler（`ssh://hosts` / `{host}` / `policy` / `{host}` / `commands` / `{command}` / `audit/recent` / `audit/search` / `runbooks` / `{name}`）
- [ ] 16.2 Resources 全部走 PolicyEngine（host/path/audit 子规则）
- [ ] 16.3 `ssh://audit/recent|search` 经 redact + caller 过滤
- [ ] 16.4 实现 `runbooks/*.md` 加载 + `ssh://runbooks` 列元信息（name/title/summary/tags）
- [ ] 16.5 写入 11 个内置 prompt 模板（`debug_service_failure` / `debug_port_unreachable` / `debug_high_cpu` / `debug_high_memory` / `debug_disk_full` / `debug_nginx_config` / `debug_postgres_connection` / `debug_firewall_forwarding` / `prepare_safe_change` / `post_change_validation` / `incident_report`）
- [ ] 16.6 prompts/list 与 prompts/get 走 PolicyEngine 可见性
- [ ] 16.7 集成测试：prompt 渲染含入参 / runbooks 不存在 404 / audit recent caller 过滤

## 17. CLI 与启动入口

- [ ] 17.1 实现 `ssh-mcp serve [--stdio|--http]` + 启动校验顺序（config → audit sink 可写 → SQLite 迁移 → key_path 探测）
- [ ] 17.2 实现 `ssh-mcp reload` / `POST /admin/reload`
- [ ] 17.3 实现 `ssh-mcp trust <host>`（首次信任录入指纹）
- [ ] 17.4 实现 `ssh-mcp approve <request_id>` / `--list`
- [ ] 17.5 实现 `ssh-mcp audit query|export`
- [ ] 17.6 实现 `--break-glass` flag + 启动期 WARN

## 18. 可观测性、文档与发布

- [ ] 18.1 stdlib `logging` + JSON formatter（默认 stderr，HTTP 模式可配文件）
- [ ] 18.2 内置极简 metrics（counter / histogram）+ HTTP `GET /metrics`
- [ ] 18.3 stdio 启动打印 summary（注册工具数 / 已启用 features / sink / store path）
- [ ] 18.4 编写部署文档：主机侧专用低权用户 / sudoers 白名单 / forced command（部署侧硬要求，MCP 不自动配置）
- [ ] 18.5 编写 README + CONFIG.md + AUDIT.md + APPROVAL.md（5 份 yaml 范例 + 配置矩阵 + 审计字段表 + 审批闭环示意）
- [ ] 18.6 发布 v0.1.0：tag + GitHub Release + uv build wheel/sdist
- [ ] 18.7 端到端验收：跑通审批闭环 + 双 transport + 17 模块各冒烟一次 + 覆盖率门槛（unit+integration ≥ 85% / policy ≥ 95%）
