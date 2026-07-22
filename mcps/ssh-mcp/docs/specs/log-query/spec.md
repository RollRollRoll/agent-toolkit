## ADDED Requirements

### Requirement: query_journal 多源多模式聚合
`query_journal(host, source, target, mode, ...)` MUST 支持 `source ∈ {file, journal}`、`mode ∈ {tail, grep, range, recent_errors, excerpt}`。`source=file` 时 `target` 是 path，受 `log_policy.readable_paths` 白名单约束；`source=journal` 时 `target` 是 unit 名。所有输出 MUST 经 redact + 截断流水线。

#### Scenario: file tail
- **WHEN** `source=file, target="/var/log/nginx/error.log", mode=tail, lines=100`
- **THEN** 返回 `data.lines` 长度 ≤ 100，且每行经 secret redact

#### Scenario: file 路径越权
- **WHEN** `source=file, target="/etc/shadow"`
- **THEN** PolicyEngine MUST 返回 `POLICY_DENIED_PATH`

#### Scenario: journal recent_errors
- **WHEN** `source=journal, target="nginx", mode=recent_errors`
- **THEN** 返回 `data.entries` 仅含 `priority<=err`，按时间倒序

#### Scenario: range 模式
- **WHEN** `source=journal, target="nginx", mode=range, since="-1h"`
- **THEN** 返回的所有日志条目时间戳 MUST 落在 (now-1h, now] 区间

### Requirement: list_log_files 受路径策略限制
`list_log_files(host, path?)` MUST 仅返回 `log_policy.readable_paths` 白名单下的可读日志文件；超出白名单 MUST 返回空列表（不暴露存在性），写一行 audit `result_summary="filtered_outside_allowlist"`。

#### Scenario: 白名单内
- **WHEN** `path="/var/log"` 且白名单含 `/var/log/`
- **THEN** 返回 `data.files` 含 `path` / `size_bytes` / `mtime`

#### Scenario: 白名单外
- **WHEN** `path="/root/.ssh"`
- **THEN** 返回 `data.files=[]`，audit 写 `filtered_outside_allowlist`
