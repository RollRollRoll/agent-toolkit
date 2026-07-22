# Brainstorm — ssh-mcp-foundation

> Raw capture of `superpowers:brainstorming`. 决策日志格式，不强制结构。
> design.md 会从本档萃取并重组成 Context / Goals / Decisions / Risks / Migration。

---

## 背景（Context）

- 目标：基于 Notion 文档「🖥️ SSH MCP 完整功能清单」（17 大模块），从零实现一个生产可用的 SSH MCP server。
- 项目位置：`/Users/chenjinfan/Project/ssh_mcp`，仓库已初始化、有 LICENSE 与 OpenSpec scaffold（`superpowers-bridge` schema）。
- 资产范围确认：用户明确要求**全量 17 模块一次成 change**，不分阶段。
- Notion 文档关键约束：
  - 不让 agent 直接拿 shell；不把私钥暴露给模型；不默认允许 root；不默认允许写；不默认允许批量变更。
  - 所有动作必须可审计；所有高危动作必须可确认、可回滚。
  - MCP server 同时暴露 Tools / Resources / Prompts。
  - 鉴权三层模型：Client→Server（HTTP=OAuth/token，stdio=env）、Server→SSH（私钥/known_hosts/ProxyJump/连接池）、SSH 内部权限（专用用户/sudoers/forced command）。

---

## 决策链

### Q1 — 首个 OpenSpec change 的范围
- 选项：Phase 1 最小骨架 / Phase 1+2 合并 / 全量 17 模块
- **决策：全量 17 模块一次成 change。**
- 取舍：proposal/tasks 会很大；但用户希望一次到位，后续不再拆分。承担实施周期长、验收复杂的代价。

### Q2 — 实现语言
- 选项：Python+官方 mcp SDK / Node+官方 SDK / Go+社区 SDK
- **决策：Python 3.11+ + 官方 mcp SDK。**
- 取舍：Python 生态最成熟，paramiko/asyncssh 可选；运维脚本生态天然 Python；与 Ansible/Fabric 互动顺畅。

### Q3 — SSH 库
- 选项：asyncssh / paramiko（同步，需线程池） / openssh+subprocess
- **决策：asyncssh。**
- 取舍：原生 asyncio，与 mcp SDK 同为 async；连接池/并发/超时/取消天然支持，避免线程异步混部。

### Q4 — Transport 范围
- 选项：仅 stdio / stdio + Streamable HTTP
- **决策：stdio + HTTP 一起做。**HTTP 端配 OAuth/token 鉴权，stdio 端走环境变量。
- 取舍：覆盖远程接入；HTTP 鉴权/会话/SSE 兼容工作量翻倍以上，但用户接受。

### Q5 — 默认安全姿态
- 选项：严格默认 / 宽松默认 / 一律审批
- **决策：严格默认。** `allow_write=false`、`arbitrary_shell=false`、中高危必走 `plan_action → manage_approval → apply_approved_action`。
- 取舍：与 Notion 文档原则完全对齐。

### Q6 — 凭据与主机配置
- 选项：YAML+本地私钥 / 集成外部凭据管理器 / YAML+provider 拓展点
- **决策：YAML+provider 拓展点。** 默认实现读 YAML，但定义 `CredentialProvider` 接口，未来可接 Vault/AWS Secrets Manager/1Password。
- 取舍：首版无外部依赖，后续接入零侵入。

### Q7 — 审计落盘
- 选项：本地 JSONL+sink 拓展点 / stdout 只写 / 直接外部 sink
- **决策：本地 JSONL（按天轮转）+ `AuditSink` 接口。** 首版只实现 file sink。
- 取舍：与 Notion「审计查询/导出/外部审计集成」要求对齐；接口预留 Loki/ELK/Splunk。

### Q8 — 任务管理与批量执行的持久化
- 选项：内存队列 / SQLite 持久化 / 不做任务系统
- **决策：SQLite 持久化（aiosqlite）。** 默认 `~/.ssh-mcp/state.db`。
- 取舍：进程重启不丢任务/审批，多一个依赖与 schema 维护成本。

### Q9 — 审批后端
- 选项：本地内置审批队列 / 集成外部审批系统 / 本地+backend 拓展点
- **决策：本地内置审批队列。** SQLite 落盘；通过 ssh-mcp CLI 子命令在终端 approve；后续可加 backend 拓展点。
- 取舍：首版零外部依赖，能闭环；与 Q6/Q7「+ 拓展点」节奏一致。

### Q10 — 依赖管理与打包
- 选项：uv+pyproject / Poetry / pip+requirements.txt
- **决策：uv + pyproject.toml + uv.lock。**
- 取舍：解析快、锁质量高、社区迁移趋势一致。

### Q11 — Python 最低版本
- 选项：3.11+ / 3.12+ / 3.10+
- **决策：Python 3.11+。** 用 TaskGroup / except* / Self。

### Q12 — 运行时架构
- 选项：纯异步 / 混合线程池 / 多进程并发
- **决策：纯异步。** SQLite 走 aiosqlite，sync 库用 `asyncio.to_thread` 包装。

### Q13 — 总体架构
- 选项：A 洋葱型分层 / B 插件总线 / C 扁平 service 集合
- **决策：方案 A — 洋葱型分层。**
- 取舍：
  - 优点：Policy 是唯一安全闸门，无法被业务旁路；扩展点（provider/sink/backend）集中在最外层；每层职责单一可独立单测。
  - 缺点：简单工具调用栈较深（4-5 跳），值得。
  - 弃用 B：plugin+middleware 模型策略可被旁路，与「严格默认」冲突；过度设计。
  - 弃用 C：扁平 service 模型策略调用靠手动，极易漏调；扩展点无处安放。

### Q14 — 审计读侧能力（查询 / 导出）形态
- 选项：A 作为 MCP Tool 暴露（`query_audit` / `export_audit`） / B 仅 CLI + Resource（`ssh-mcp audit query|export` + `ssh://audit/search`）/ C 不做读侧（只写）
- **决策：方案 B。**
- 取舍：
  - Notion §14 显式要求「审计查询 + 审计导出 JSONL/CSV」，方案 C 漏需求。
  - 方案 A 让 agent 可以通过工具调用拉审计，存在被诱导拉取超量上下文 / 绕过 caller 过滤的风险，违背「不让 agent 直接拿管理面」原则。
  - 方案 B 把读侧定位为「管理面」：CLI 给运维人，Resource 给模型只读上下文（走 redact + caller 过滤）；CLI 与 Resource 共用同一查询层，避免读路径分裂。
- 边界：审计查询 / 导出**不作为 MCP Tool**，硬约束写入 design.md D7.5。

### Q15 — Tool Contract 字段固化
- 选项：A 不固化（每工具自描述） / B 固化全套 11 字段（含 `policy_checks` / `audit_fields`） / C 固化精简 9 字段
- **决策：方案 C — 9 个必备字段。**
- 取舍：
  - 方案 A 在 spec/tasks 阶段会出现「只落工具名」漏字段（schema/timeout/output_limits 缺失），返工成本大。
  - 方案 B 的 `policy_checks` 与 PolicyEngine 规则栈职责重叠，工具自带声明易与 `policy.yaml` 冲突；`audit_fields` 与 `input_schema` 的脱敏白名单重叠。
  - 方案 C 把 `policy_checks` 让给 PolicyEngine 自决；`audit_fields` 合并进 `input_schema.x-redact` 作为单一来源，保留 9 字段刚好覆盖 spec/tests 的机械验收清单。
- 字段定型见 design.md D9.5。

### Q16 — 统一 ToolResult Envelope
- 选项：A 不约束（每工具自定义返回） / B 统一 envelope + `data` 子结构 / C 协议层 raw passthrough
- **决策：方案 B。**
- 取舍：
  - 方案 A 让客户端无法统一处理 `truncated` / `cursor` / `correlation_id` / 错误重试，spec 阶段每工具一套契约。
  - 方案 C 等于把 envelope 责任推给 mcp SDK，但 SDK 不知道 SSH 命令语义（exit_code / host / duration），仍要业务层补字段。
  - 方案 B 顶层固化 9 字段（`ok` / `host` / `exit_code` / `duration_ms` / `truncated` / `cursor` / `summary` / `correlation_id` / `data`），命令类工具 `data` 内嵌 `stdout`/`stderr`；非命令类 `exit_code` 置 `null`。
- 字段定型见 design.md D11.5。

### Q17 — Runbooks 资源载体
- 选项：A 仓库内置 markdown 文件 / B 从 Prompts 渲染 / C 外部 wiki 链接
- **决策：方案 A — 仓库内置 `runbooks/*.md`。**
- 取舍：
  - Notion §16 的 `ssh://runbooks/{name}` 与 §17 的 `debug_*` Prompts 不是同一类对象（一个是文档，一个是工作流模板），方案 B 会让两者混淆且重复维护。
  - 方案 C 引外部依赖、首版 YAGNI、且离线场景不可用。
  - 方案 A 让手册更新走 git 提交流程；运行时只读；与 Prompts 各自独立，可交叉引用（runbook 内可链 `prompt://...`）。
- 落地见 design.md D12.5。

### Q18 — 文件变更备份/回滚模型
- 选项：A 不做备份（rollback = patch 反转） / B 远端主机受控目录备份 / C 拉回本地备份
- **决策：方案 B — `/tmp/ssh-mcp/backups/{operation_id}/`，远端落盘。**
- 取舍：
  - 方案 A 对 `manage_file(delete)` 这类无 patch 的动作不可用；patch 反转在二进制或大文件场景不可靠。
  - 方案 C 涉及把潜在敏感文件拉回 MCP 主机，违反「凭据/数据隔离」原则；网络抖动也容易半途。
  - 方案 B 备份仅留在目标主机，权限 `0700` + 专用用户隔离；`operation_id` 作为唯一句柄串联 apply/rollback/audit；保留期由 `server.yaml.backup_retention_days` 控制（默认 7 天），后台清理走 `manage_task`。
  - rollback 必须**重新经过 PolicyEngine**（risk + approval），即使原 apply 已审批；备份缺失直接 `ROLLBACK_BACKUP_MISSING`。
- 落地见 design.md D13.5。

---

## 设计取舍要点（供 design.md 萃取）

### D1 — 分层结构
```
Transport (stdio + HTTP/OAuth)
   ↓
Dispatcher (registry + routing + ratelimit)
   ↓ 必经
Policy Engine (host/cmd/path/service allowlist + arg schema + deny + risk + approval gate + window)
   ↓ 仅放行后
Operation Handlers (17 模块业务)
   ↓
Backends:
  ConnectionPool (asyncssh)
  CredentialProvider (YAML 默认 + 接口)
  AuditSink (JSONL 默认 + 接口)
  ApprovalBackend (本地默认 + 接口)
  TaskStore (SQLite/aiosqlite)
```

### D2 — 源码组织
- `src/ssh_mcp/` 包；按层分子包：`transport/`、`server/`、`policy/`、`operations/`、`ssh/`、`credentials/`、`audit/`、`approval/`、`store/`、`resources/`、`prompts/`、`config/`、`utils/`。
- `operations/` 按 17 类业务一个文件，与 Notion 文档「工具吞并」后的工具粒度对齐（如 `query_journal` 吞 7 个）。
- `tests/` 三层：unit / integration / e2e；`fixtures/`（含测试用 ed25519 私钥）、`support/`（fake SSH server、docker_ssh、最小 MCP client、内存 audit collector）。

### D3 — 核心数据流（一次 ToolCall）
1. Transport 解析 JSON-RPC → ToolCall(call_id, name, args, caller_ctx)
2. Dispatcher 查 registry，走 ratelimit
3. Policy.engine.check：host_allowlist → command/path/service allowlist → arg_schema → deny → risk classify → approval gate → window check（任一 deny 立停）
4. Operation.execute：渲染 argv、ssh.pool.acquire、命令执行
5. ssh.connection.run：分离 stdout/stderr、超时、output 截断、二进制拒绝、secret redaction
6. ToolResult 打包；redact 二次过滤
7. Audit.recorder.record（同步写本地 JSONL，异步 fan-out）
8. Dispatcher 回传 → Transport 写出

### D4 — 关键不变量
- Operation 不能直接 new SSH 连接，必须经 `ssh.pool.acquire`。
- Policy 决策对象穿透到 Audit（risk/approval 不重新推导）。
- Approval 工作流：`plan_action` → `manage_approval(request)` → 人工 approve → `apply_approved_action(token, nonce)`，**第 4 步 Policy 重新校验**，token+nonce 一次性。
- Audit 落盘失败不阻塞业务，但启动期 sink 不可写直接拒启。
- Resources / Prompts 也走同一套 Policy。

### D5 — 模块接口（design.md 细化）
- `OperationHandler`（kind ∈ tool/resource/prompt；name；risk_default；readonly；arg_schema；result_schema；execute）。
- `PolicyDecision`（allow/risk/reasons/needs_approval/approval_token/redact_rules）；`PolicyEngine.check / reload`。
- `ConnectionPool.acquire / warmup / close_all`，单主机串行化用 asyncio.Lock；持有 CredentialProvider。
- `CredentialProvider.resolve / list_hosts`；`YamlCredentialProvider` 默认。
- `AuditEvent`（time/client/user/tool/host/params 脱敏/risk/approved/approval_token/exit_code/duration_ms/error_kind/output_summary）；`AuditSink.write/flush/close`；`JsonlAuditSink` 默认。
- `ApprovalRequest`（request_id/token/nonce/plan/risk/expires_at/state/confirmation_text）；`ApprovalBackend.request/list_pending/approve/deny/consume`；`LocalApprovalBackend` 默认。

### D6 — 配置 schema
- `HostsConfig`（hosts.yaml）、`CommandsConfig`（commands.yaml）、`PolicyConfig`（policy.yaml，全局+per_user/per_env override）、`AuditConfig`、`ServerConfig`。
- 加载顺序：默认 → 全局 yaml → 环境变量 → CLI 参数；pydantic 校验，失败拒启。
- 热重载：policy/hosts/commands.yaml 可热重载（`ssh-mcp reload` / `POST /admin/reload`），原子替换不可变快照；transport/listen/oauth issuer/sqlite path/sink 后端类型不可热重载。

### D7 — 错误处理
- 统一 `MCPError {code, message, retryable, data}`。
- 类别前缀：`CONFIG_*`、`AUTH_*`、`POLICY_DENIED_*`、`APPROVAL_*`、`SSH_CONNECT_*`、`EXEC_*`（含 timeout、output_too_large、binary_output）、`ARG_*`、`INTERNAL_*`。
- 内部异常不直接序列化给 client；`POLICY_DENIED_*` 必须写 audit；`EXEC_TIMEOUT` 把已执行时长放 data。

### D8 — 可观测性
- 应用日志：stdlib logging + JSON formatter（默认 stderr，HTTP 模式可配文件）。
- 审计日志：AuditSink（JSONL）独立通道。
- 指标：内置极简 counter/histogram，HTTP transport 暴露 `GET /metrics`；stdio 模式启动时打印 summary。
- 不引入 OpenTelemetry SDK（首版 YAGNI）。
- 每条 ToolCall 生成 `correlation_id`，贯穿日志/审计/错误 data。

### D9 — 输出处理流水线
`raw bytes → 编码探测（失败 → BinaryRejected）→ size check（超限截断 + truncated=true）→ secret redaction（pattern + custom regex）→ stdout/stderr 分离 → ToolResult.output / audit.output_summary（仅前 N 行）`。
`max_output_bytes` 默认 256 KiB，可被 policy per-tool 覆盖。

### D10 — 测试策略
- 框架：pytest + pytest-asyncio（asyncio_mode=auto）。
- 不 mock asyncssh：单元用 fake transport（asyncssh.SSHServerConnection 内存 server），集成 + E2E 用 docker `linuxserver/openssh-server`。
- Policy 各子规则一文件一测试。
- 17 类 Operation 各自集成测试套件，每工具至少：happy path、policy deny、audit 记录、错误分类。
- 审批闭环 E2E：plan → request → CLI approve → apply → 验证执行+审计。
- 覆盖率门槛：unit+integration ≥ 85%，policy 包 ≥ 95%。
- TDD 纪律：plan.md 阶段由 `superpowers:test-driven-development` 钉死。

### D11 — Tool Contract 标准结构（Q15 落地）
- 每个 Tool 必须声明 9 个字段：`name` / `description` / `input_schema`（含 `x-redact`） / `result_schema` / `readonly` / `risk_default` / `timeout_default` / `output_limits` / `approval_required_when`。
- `policy_checks` 不入工具自描述——PolicyEngine 按规则栈自决；避免与 `policy.yaml` 双源。
- `audit_fields` 合并进 `input_schema.x-redact`，参数审计可见性单一来源。
- spec/tasks 验收清单可由 9 字段机械生成。

### D12 — 统一 ToolResult Envelope（Q16 落地）
- 顶层 9 字段：`ok` / `host` / `exit_code` / `duration_ms` / `truncated` / `cursor` / `summary` / `correlation_id` / `data`；错误时附 `error: {code, message, retryable}`。
- 命令类工具 `data` 内嵌 `stdout` / `stderr`；非命令类 `exit_code = null`。
- `cursor` 仅适用于按行可切的输出；二进制或结构化结果超限直接 `truncated=true`。
- `raw output option` 启用时 envelope 增加 `raw: true`，policy 可禁用。
- 审计字段从 envelope 一次性映射，免去每工具自描述。

### D13 — 文件变更/备份/回滚模型（Q18 落地）
- 受影响工具：`apply_patch` / `write_file` / `transfer_file` / `manage_file`。
- `operation_id`（与 `correlation_id` 不同）= 一次实际写盘；远端备份 `/tmp/ssh-mcp/backups/{operation_id}/`，mode `0700`，保留期默认 7 天（后台清理走 `manage_task`）。
- `apply_patch` 三阶段：validate（dry-run）→ backup → apply（atomic rename）。validate 失败不写文件但**必须写审计**。
- rollback 入参只接受 `operation_id`，**重新经 PolicyEngine**（即使原 apply 已审批）；备份缺失 → `ROLLBACK_BACKUP_MISSING`。
- 风险分级：`apply_patch.apply/rollback=medium` / `write_file=medium+` / `transfer_file.up=medium`、`down=low` / `manage_file.delete=high` / `move=medium` / `chmod=medium` / `chown=high`。
- `confirmation_text` 高危必须含目标 path。

### D14 — 跨切面行为规范（Q14/Q15 副产物）
- list 类（`tools/list` / `resources/list` / `prompts/list`）按 caller policy 过滤可见项；不可见项**完全不出现**，避免泄露存在性。
- call 类（`tools/call` / `resources/read` / `prompts/get`）入 Dispatcher 即生成 `correlation_id`，注入日志/审计/错误 data。
- stdio 与 HTTP 共用同一份 registry / PolicyEngine / AuditSink 实例，不允许各自维护副本；Transport 层只负责 framing 与 caller_ctx 注入。

### D15 — Runbooks 资源载体（Q17 落地）
- 仓库 `runbooks/*.md` 内置载入；`ssh://runbooks` 列元信息（name/title/summary/tags），`ssh://runbooks/{name}` 返回原文。
- 与 §17 Prompts 各自独立，可交叉引用（markdown 内链 `prompt://...`，prompt 模板内链 `ssh://runbooks/...`）。
- 手册更新走 git，运行时只读。

---

## 风险与开放问题（供 design.md 进一步处理）

- **R1 17 模块单 change 体量大**：proposal/tasks/plan 都会很厚，验收周期长。Mitigation：tasks.md 分组细化、plan.md 用 micro-step + 频繁 commit；按层（先 transport+policy+ssh，再 operations 各模块）拉时间线。
- **R2 HTTP transport 鉴权复杂度**：OAuth issuer/JWT 校验/refresh 在首版易超工。Mitigation：先支持静态 token + 外部网关认证模式，OAuth 完整流程留 design.md 决议。
- **R3 SQLite 单文件并发**：aiosqlite 串行写。Mitigation：单进程内只有 task store + approval store 写，QPS 低，可接受；多进程方案不在首版范围。
- **R4 docker 在 CI 启动慢**：E2E 仅在 main 夜跑。
- **R5 Resources/Prompts 走 Policy 的方式**：尚未细化（读资源也要看 caller 权限），design.md 需明确。
- **R6 任意 shell + 抓包等高危默认禁用**：features 开关默认关，policy.yaml 显式声明启用。
- **R7 Resources 提供敏感信息**（如 audit/recent）：需要 redact 与 per-caller 过滤。

---

## 终态

- 用户接受方案 A、源码结构、数据流、模块接口、错误处理与可观测性、测试策略五节。
- 进入 design.md 阶段，将以上决策与取舍重组为 Context / Goals / Non-Goals / Decisions / Risks / Migration / Open Questions。
