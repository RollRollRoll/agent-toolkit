## ADDED Requirements

### Requirement: 唯一连接入口
所有 Operation MUST 通过 `ssh.pool.acquire(host)` 获取连接，不得直接构造 `asyncssh.connect`。Pool MUST 复用已建立的连接，并在 `close_all()` 时统一释放。

#### Scenario: Operation 旁路连接池
- **WHEN** 任何 Operation 代码尝试直接调用 `asyncssh.connect`
- **THEN** lint / 单元测试 MUST 失败（通过模块级导入限制或运行期断言）

#### Scenario: 同 host 复用
- **WHEN** 两个并发 Operation 都需要连 `test-vps`，且现有 `asyncssh` 连接 alive
- **THEN** Pool MUST 返回同一个 connection handle，不建立第二条 TCP 连接

### Requirement: 密钥认证默认与 known_hosts 强校验
首版 MUST 默认仅支持密钥认证，密码认证由 `features.password_auth` 控制；known_hosts 校验 MUST 等价于 OpenSSH `StrictHostKeyChecking=yes`。新主机首次连接 MUST 通过显式 `ssh-mcp trust <host>` CLI 录入指纹，禁止运行期自动信任。

#### Scenario: 未录入指纹的新主机
- **WHEN** Pool 首次连接 `new-host` 且 known_hosts 无对应条目
- **THEN** 连接 MUST 失败并返回 `SSH_CONNECT_HOST_KEY_UNKNOWN`，引导执行 `ssh-mcp trust`

#### Scenario: 指纹变更
- **WHEN** 已录入主机的 host key 变更
- **THEN** 连接 MUST 失败并返回 `SSH_CONNECT_HOST_KEY_MISMATCH`，不允许覆盖

### Requirement: ProxyJump 与 SSH config 解析
Pool MUST 通过 `bastion` 字段支持 ProxyJump 链路；当 `hosts.yaml` 未显式声明字段时 MUST 回退读取 `~/.ssh/config` 解析结果，host 配置覆盖 ssh_config。

#### Scenario: 跳板机链路
- **WHEN** `hosts.yaml.po0-cne.bastion = "jump-host"`
- **THEN** Pool MUST 先建立到 `jump-host` 的连接，再通过其建立到 `po0-cne` 的连接

### Requirement: 超时与 keepalive 默认
连接超时默认 10s、命令超时默认 30s（per-tool 可被 `Tool Contract.timeout_default` 与 `policy.yaml` 覆盖）、keepalive 默认 30s。命令超时 MUST 抛 `EXEC_TIMEOUT` 并把已执行时长放入错误 `data.elapsed_ms`。

#### Scenario: 命令长时间无返回
- **WHEN** 工具执行的 SSH 命令超过 timeout
- **THEN** Pool MUST 取消该命令并返回 `EXEC_TIMEOUT`，连接保留供下次复用

### Requirement: 全局并发与单主机串行化
Pool MUST 限制全局并发连接数（默认 16，可配）；同一 host 上的 Operation MUST 通过 `asyncio.Lock` 串行化执行，保证不会并发修改同一台机器。

#### Scenario: 同主机并发请求
- **WHEN** 两个 Operation 同时请求对 `po0-cne` 执行 `manage_service.restart`
- **THEN** 第二个请求 MUST 等待第一个完成后再执行（FIFO 顺序），不得并发

### Requirement: 凭据隔离
Pool MUST 通过 `CredentialProvider` 解析私钥路径或密码，agent 入参与 ToolResult / audit / 日志 MUST 仅出现 host alias，不得出现真实私钥路径或密码字符串。

#### Scenario: 审计行不含私钥路径
- **WHEN** 任意工具调用产生 audit 行
- **THEN** 该行 JSON MUST 不包含 `key_path` 字段，host 字段 MUST 是 alias

#### Scenario: 错误信息脱敏
- **WHEN** SSH 连接失败（如私钥读取错误）
- **THEN** 返回的 `error.message` MUST 不含私钥绝对路径，仅返回 `SSH_CONNECT_KEY_UNREADABLE` 与 host alias
