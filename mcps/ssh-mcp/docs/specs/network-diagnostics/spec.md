## ADDED Requirements

### Requirement: probe_network 主动探测 6 模式
`probe_network(host, mode, target, ...)` MUST 支持 `mode ∈ {ping, traceroute, dns, tcp, http, tls}`；每种 mode 的 result_schema MUST 显式声明（如 ping 含 `rtt_ms_avg/min/max/loss_pct`，tls 含 `protocol/cipher/cert_chain[*].subject`）。所有 mode MUST 受 `network_policy.allowed_targets` 白名单约束（domain glob 或 IP 段）。

#### Scenario: ping 默认参数
- **WHEN** `mode=ping, target="8.8.8.8"`（在白名单）
- **THEN** 返回 `data.rtt_ms_avg` 与 `data.loss_pct` 非空

#### Scenario: 目标越权
- **WHEN** `mode=tcp, target="10.0.0.1:22"` 且不在白名单
- **THEN** PolicyEngine 返回 `POLICY_DENIED_TARGET`

#### Scenario: tls 握手
- **WHEN** `mode=tls, target="example.com:443"`
- **THEN** `data.protocol` ∈ {`TLSv1.2`, `TLSv1.3`}，`data.cert_chain[0].subject` 非空

### Requirement: get_network_info 本机网络快照
`get_network_info(host, kinds=[interfaces, routes, sockets, conntrack, addresses, ports, firewall_nft, firewall_iptables, forwarding, firewall_policy])` MUST 按 kinds 选择性返回 10 类网络信息；`firewall_*` 输出 MUST 经 redact（隐藏 mark / counter 类敏感字段，可由 policy 控制开放）。

#### Scenario: 默认快照
- **WHEN** caller 不传 `kinds`
- **THEN** 默认 `kinds=[interfaces, routes, addresses, ports]` 四项

#### Scenario: 防火墙规则查询
- **WHEN** `kinds=[firewall_nft]`
- **THEN** 返回 `data.firewall_nft` 为 nft 规则文本，counter 字段已脱敏为 `<REDACTED>`

### Requirement: capture_packets 默认禁用与上限
`capture_packets(host, filter, duration, max_packets)` MUST 默认禁用（`features.packet_capture=false`）；启用后 MUST 强制 `duration<=60s` 且 `max_packets<=5000`，超过 MUST 由 PolicyEngine 截断到上限并在 envelope `data.truncated_by_policy=true`。

#### Scenario: 未启用
- **WHEN** `features.packet_capture=false`
- **THEN** 返回 `POLICY_DENIED_FEATURE_DISABLED`

#### Scenario: 入参超限
- **WHEN** `duration=300, max_packets=100000`
- **THEN** PolicyEngine MUST 强制改写为 `duration=60, max_packets=5000`，envelope `data.truncated_by_policy=true`
