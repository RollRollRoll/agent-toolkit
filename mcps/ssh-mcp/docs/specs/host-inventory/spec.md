## ADDED Requirements

### Requirement: list_hosts 过滤与可见性
`list_hosts(filter)` MUST 支持按 `tag` 与 `env` 过滤；返回的 host 对象 MUST 仅含 alias / env / tags / readonly summary，不得包含私钥路径或密码字段。结果 MUST 经 PolicyEngine 按 caller 可见性二次过滤。

#### Scenario: 按 tag 过滤
- **WHEN** caller 调用 `list_hosts({filter: {tag: "edge"}})`
- **THEN** 返回数组 MUST 仅包含 tags 含 `"edge"` 的主机

#### Scenario: 私钥路径不外泄
- **WHEN** 返回任意 host 对象
- **THEN** 该对象 MUST 不含 `key_path` / `password` 字段

### Requirement: get_host_info 多视角拼装
`get_host_info(host, include=[basic,policy,inventory])` MUST 支持按 include 字段选择性返回基础信息、生效策略、资产清单。`include` 默认仅 `basic`。

#### Scenario: 仅 basic
- **WHEN** caller 不传 `include`
- **THEN** 返回 `data` MUST 仅含 `host` / `env` / `tags` / `connectivity_state`，不含 policy / inventory

#### Scenario: 包含 policy
- **WHEN** `include=[policy]`
- **THEN** 返回 `data.policy` MUST 反映该 host 的合并后策略（global + per-env + per-host）

### Requirement: test_connection 不旁路 PolicyEngine
`test_connection(host)` MUST 经 PolicyEngine 检查 host_allowlist；连接成功后 MUST 返回 `latency_ms` / `auth_method` / `server_banner_redacted`，不得返回 host key 指纹原文（仅返回 sha256 摘要）。

#### Scenario: 连通性测试
- **WHEN** caller 调用 `test_connection("test-vps")`
- **THEN** 返回 envelope `data.latency_ms` MUST > 0；audit 行 `tool` 字段 MUST 为 `test_connection`

### Requirement: sync_inventory 走 InventorySource 接口
`sync_inventory(source)` MUST 通过 `InventorySource` 接口对接 YAML / CMDB / Ansible inventory；首版 MUST 提供 YAML 默认实现（`YamlInventorySource`），其它来源仅预留接口。`source` 入参 MUST 校验白名单。

#### Scenario: 未启用的 source
- **WHEN** caller 调用 `sync_inventory(source="cmdb")` 但 `cmdb` 未注册
- **THEN** PolicyEngine 与工具层 MUST 返回 `INVENTORY_SOURCE_NOT_AVAILABLE`，不进入实际同步

#### Scenario: YAML 同步增量
- **WHEN** `hosts.yaml` 新增 1 台主机后调用 `sync_inventory(source="yaml")`
- **THEN** 返回 `data.added=1` / `data.removed=0`，且新主机进入运行期 inventory 快照
