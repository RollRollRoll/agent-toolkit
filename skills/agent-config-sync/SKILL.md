---
name: agent-config-sync
description: 声明式管理并跨 Windows、Linux、macOS 与 WSL 同步 Codex ~/.codex/config.toml 和 Claude Code ~/.claude/settings.json。用于初始化、检测、校验、渲染、预览差异、应用、检查状态或诊断 agent-config.yaml；不用于凭据、登录状态、项目级配置、~/.claude.json、skills、agents、hooks 或 MCP 配置。
---

# Agent Config Sync

只把 `agent-config.yaml` 视为事实来源。使用随 Skill 附带的确定性 CLI 生成配置，禁止直接拼接 TOML/JSON 后覆盖用户文件。

## 定位 CLI

优先运行已安装的 `aiconfig`。若命令不可用，运行本 Skill 目录中的：

```bash
python3 scripts/aiconfig.py
```

所有命令默认从当前目录向上查找 `agent-config.yaml`，也可传 `--config <path>`。

## 标准工作流

只读分析时：

1. 运行 `aiconfig detect`。
2. 运行 `aiconfig validate`，失败即停止。
3. 运行 `aiconfig plan`。
4. 说明命中的 overlay、应用顺序、目标路径、差异和警告。

用户明确要求应用、更新或写入时：

1. 依次运行 `detect`、`validate`、`plan`。
2. 校验失败时停止，给出错误码和修复建议。
3. 运行 `aiconfig apply [codex|claude]`。
4. 运行 `aiconfig status [codex|claude]`。
5. 报告变更文件和备份路径。

不要仅因用户要求“检查、比较、分析”而执行 `apply`。目标文件有上次应用后的本地修改时，不要自行增加 `--force`；解释冲突并等待用户明确授权。

## 常用任务

- 初始化声明：`aiconfig init`
- 查看环境：`aiconfig detect` 或 `aiconfig detect --json`
- 校验全部/单个目标：`aiconfig validate [codex|claude]`
- 渲染到 `.agent-config/generated/`：`aiconfig render [codex|claude]`
- 预览匹配和差异：`aiconfig plan [codex|claude]`
- 应用全部/单个目标：`aiconfig apply [codex|claude]`
- 检查同步状态：`aiconfig status [codex|claude]`

## 配置边界

- 分别保留 `targets.codex` 与 `targets.claude` 的原生语义，不发明跨工具权限映射。
- 只管理 `~/.codex/config.toml` 与 `~/.claude/settings.json`。
- 不读取、复制或写入 Token、OAuth 状态、凭据、会话、缓存、日志或 `~/.claude.json`。
- 不修改项目级 `.codex/config.toml`、`.claude/settings.json`。
- 不在校验失败后继续应用。
- 不绕过备份、原子写入或本地修改检测。

## 按需读取参考

- 编写或解释声明时读取 [声明格式](references/declaration-format.md)。
- 处理覆盖、数组操作或删除时读取 [合并规则](references/merge-rules.md)。
- 解释目标边界时读取 [Codex 配置](references/codex-config.md) 或 [Claude 设置](references/claude-settings.md)。
- 遇到稳定错误码时读取 [故障排查](references/troubleshooting.md)。

