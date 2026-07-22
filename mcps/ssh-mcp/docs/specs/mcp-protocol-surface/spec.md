## ADDED Requirements

### Requirement: 暴露 MCP 协议 9 个方法
系统 SHALL 通过 MCP SDK 暴露以下 9 个 JSON-RPC 方法：`initialize`、`notifications/initialized`、`tools/list`、`tools/call`、`resources/list`、`resources/read`、`resources/templates/list`、`prompts/list`、`prompts/get`。任何未列出的方法 MUST 返回 `MethodNotFound`。

#### Scenario: 客户端调用未支持的方法
- **WHEN** 客户端发送 `method: "tools/cancel"` JSON-RPC 请求
- **THEN** 服务器 MUST 返回 JSON-RPC 错误码 `-32601`（Method not found），并不进入 PolicyEngine

#### Scenario: 客户端发现 URI 模板
- **WHEN** 客户端调用 `resources/templates/list`
- **THEN** 服务器 MUST 返回包含 `ssh://hosts/{host}` / `ssh://policy/{host}` / `ssh://commands/{command}` / `ssh://runbooks/{name}` / `ssh://audit/search{?since,until,tool,host,user,risk,limit}` 模板的列表

### Requirement: 双 transport 共用单实例后端
系统 SHALL 同时启动 stdio 与 Streamable HTTP 两种 transport，且二者 MUST 共用同一份 `registry` / `PolicyEngine` / `AuditSink` / `ApprovalBackend` / `TaskStore` 实例；Transport 层只负责 framing 与 `caller_ctx` 注入，不得各自维护副本。

#### Scenario: stdio 与 HTTP 同进程并发
- **WHEN** 进程同时监听 stdio 与 HTTP 端口，两路客户端各调用一次 `tools/call`
- **THEN** 两次调用 MUST 进入同一个 PolicyEngine 实例并写入同一份 audit sink，order 由到达顺序决定

#### Scenario: HTTP 缺失 Bearer token
- **WHEN** HTTP 请求未携带 `Authorization: Bearer <token>` 或 token 与 `server.yaml` 配置不一致
- **THEN** 服务器 MUST 返回 HTTP `401`，且不进入 Dispatcher，不写业务审计（仅记录鉴权失败日志）

### Requirement: list 类按 caller policy 过滤可见性
`tools/list`、`resources/list`、`prompts/list` 三个方法 MUST 在返回前根据 caller 的 user / env / role 过滤可见项；不可见的项 MUST 完全不出现在返回列表中，不得返回带 `disabled=true` 之类占位。

#### Scenario: 非 ops 角色调用 tools/list
- **WHEN** caller user 在 `policy.yaml` 声明仅可见 `low/medium` 风险工具，调用 `tools/list`
- **THEN** 返回列表 MUST 不包含任何 `risk_default=high` 或 `forbidden` 工具

#### Scenario: 不可见资源探测
- **WHEN** caller 不在 `ssh://audit/recent` 的可见名单内，直接调用 `resources/read` 读取该 URI
- **THEN** 服务器 MUST 返回 `POLICY_DENIED_RESOURCE`，错误信息不得透露资源是否存在

### Requirement: call 类生成 correlation_id
`tools/call`、`resources/read`、`prompts/get` 进入 Dispatcher 时 MUST 生成全局唯一的 `correlation_id`（ULID 或 UUIDv7），并贯穿日志 / 审计 / 错误 `data` 字段，直至响应返回。

#### Scenario: 工具调用成功
- **WHEN** 客户端调用 `tools/call` 名 `list_hosts`
- **THEN** 返回的 ToolResult envelope MUST 含 `correlation_id`，且同一 ID 出现在 stderr JSON 日志、audit JSONL 行、metric 标签中

#### Scenario: 工具调用失败
- **WHEN** 工具调用因 `POLICY_DENIED_*` 失败
- **THEN** 错误响应的 `data.correlation_id` MUST 与 audit 行 `correlation_id` 一致

### Requirement: initialize 协商能力声明
`initialize` 响应 MUST 在 `capabilities` 字段声明本服务器支持 `tools` / `resources`（含 `listChanged: true`）/ `prompts` 三类能力；客户端必须先发 `initialize` 再发任何其它请求。

#### Scenario: 客户端跳过 initialize
- **WHEN** 客户端不发 `initialize` 直接调用 `tools/call`
- **THEN** 服务器 MUST 返回 `-32002`（Server not initialized）并拒绝执行
