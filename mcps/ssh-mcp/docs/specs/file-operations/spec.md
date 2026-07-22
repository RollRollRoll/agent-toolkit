## ADDED Requirements

### Requirement: 文件只读三件套
`read_file(path, mode=full|range|tail|grep, ...)` / `find_files(path, name?, content?, recursive?, include_dir_listing?)` / `stat_file(path, include=[basic,hash,compare_with?])` 三个工具 MUST 经 PolicyEngine 检查 `file_policy.readable_paths`；超出白名单 MUST 返回 `POLICY_DENIED_PATH`。`stat_file.compare_with` 仅支持同主机内比较（跨主机比较见 Open Question）。

#### Scenario: read_file range
- **WHEN** `path="/etc/nginx/nginx.conf", mode=range, lines=[100,200]`
- **THEN** 返回 `data.lines` 含第 100–200 行，超出文件长度时返回到 EOF

#### Scenario: 路径越权
- **WHEN** `path="/etc/shadow"`
- **THEN** PolicyEngine 返回 `POLICY_DENIED_PATH`

#### Scenario: stat_file 同主机比较
- **WHEN** `path="/etc/nginx/nginx.conf", include=[hash, compare_with: "/etc/nginx/nginx.conf.bak"]`
- **THEN** 返回 `data.hash`（sha256）与 `data.compare.identical: bool`

### Requirement: apply_patch 三阶段执行
`apply_patch(path, diff, action=apply|rollback, validate=true, backup=true)` 在 `action=apply` 时 MUST 顺序执行：(1) **validate**（远端 dry-run），失败立即返回 `EXEC_PATCH_INVALID` 且 MUST 写审计但不写文件；(2) **backup**，将原文件复制到 `/tmp/ssh-mcp/backups/{operation_id}/`（mode 0700）；(3) **apply**，原子写入（同目录 `.tmp` + `os.rename`）。返回 envelope `data` MUST 含 `operation_id` / `backup_path` / `bytes_changed`。

#### Scenario: validate 失败不写文件
- **WHEN** patch 与目标文件无法对齐
- **THEN** 返回 `EXEC_PATCH_INVALID`，主机文件 mtime 不变，且对应 audit 行存在

#### Scenario: 成功 apply
- **WHEN** validate + backup + apply 全部成功
- **THEN** envelope `data.operation_id` 非空，`{backup_root}/{operation_id}/meta.json` 存在并含 `path` / `sha256` / `correlation_id`

### Requirement: rollback 重新经 PolicyEngine
`apply_patch(action=rollback, operation_id=...)` MUST 重新经过 PolicyEngine（含 risk + approval gate），即使原 apply 已经审批过；rollback 也 MUST 生成新的 `operation_id`，并把原 `operation_id` 写入新 envelope 的 `data.rolled_back_from`。备份缺失 MUST 返回 `ROLLBACK_BACKUP_MISSING`。

#### Scenario: 备份已被清理
- **WHEN** 原 `operation_id` 的备份目录已被清理任务删除
- **THEN** 返回 `ROLLBACK_BACKUP_MISSING`，不进入 PolicyEngine 的审批闸门

#### Scenario: prod rollback 仍要审批
- **WHEN** prod 主机调用 rollback 且 policy.yaml 对 rollback 声明 `medium`
- **THEN** PolicyEngine 返回 `APPROVAL_REQUIRED`

### Requirement: write_file 默认禁用与风险
`write_file(path, content, mode=overwrite|append)` MUST 默认禁用（`features.write_file=false`）；启用后风险 MUST 不低于 `medium`，`mode=overwrite` 风险 MUST 比 `mode=append` 高一档。

#### Scenario: 未启用调用
- **WHEN** `features.write_file=false`，caller 调用
- **THEN** 返回 `POLICY_DENIED_FEATURE_DISABLED`

### Requirement: transfer_file 双向语义
`transfer_file(direction=up|down, local, remote)` MUST 支持上传 / 下载；`up` 默认 `medium`、`down` 默认 `low`；`up` MUST 经 `writable_paths` 校验，`down` MUST 经 `readable_paths` 校验；超大文件 MUST 走 chunk 流式传输并在 envelope `data.bytes_transferred` 报告。

#### Scenario: 下载只读路径
- **WHEN** `direction=down, remote="/var/log/nginx/access.log"`
- **THEN** 经 `readable_paths` 通过后下载到本地 `local`，`data.bytes_transferred` 等于文件实际大小

### Requirement: manage_file per-action 风险
`manage_file(action, path, ...)` 的 `action ∈ {delete, move, chmod, chown}` MUST 按 action 单独评估：`delete=high`、`move=medium`、`chmod=medium`、`chown=high`。`delete` 与 `chown` 高危确认文案 MUST 含目标路径。

#### Scenario: delete 走审批
- **WHEN** `action=delete, path="/opt/app/config/old.conf"`
- **THEN** PolicyEngine 返回 `APPROVAL_REQUIRED`，且 `confirmation_text` 含 `delete /opt/app/config/old.conf`
