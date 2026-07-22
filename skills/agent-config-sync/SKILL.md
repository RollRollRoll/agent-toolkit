---
name: agent-config-sync
description: 从一份或多份现有配置抽取可审阅的 agent-config.yaml，并跨 Windows、Linux、macOS 与 WSL 声明式同步 Codex ~/.codex/config.toml 和 Claude Code ~/.claude/settings.json。用于导入、去重、解决冲突、剔除配置项、初始化、检测、校验、渲染、预览差异、应用、检查状态或诊断；不用于凭据、登录状态、项目级配置、~/.claude.json、skills、agents、hooks 或 MCP 配置。
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

从已有配置抽取事实时：

1. 用户未明确交互偏好时，先询问是否启动本地前端页面，并等待用户选择；用户已明确要求使用或不使用前端时不要重复询问。
2. 对用户明确提供的每个文件运行 `aiconfig import inspect --source <target>=<path>`，同一目标可重复传入。
3. 读取生成的 `.agent-config/import-plan.yaml`，说明自动去重项、冲突、敏感字段和越界字段。
4. 用户选择前端时运行 `aiconfig ui`，把页面作为主要审阅与决策入口；提供带会话令牌的本地地址，只有用户明确要求自动打开浏览器时才使用 `--open`。页面可用时不要同时通过对话逐项提问。
5. 用户拒绝前端，或 UI 启动失败、页面不可访问、当前环境无法操作页面时，说明降级原因并改用问答：逐项展示冲突候选，让用户明确选择 `take`、`union`、`set` 或 `exclude`。不要自行选择来源或合并不同数组。
6. 将页面或问答中的决定写入计划后运行 `aiconfig import generate`，或由本地界面生成。未解决冲突时停止。
7. 运行 `aiconfig validate` 和 `aiconfig plan`，确认生成声明的效果。

`import inspect` 只归并同一目标的多份配置，不推导多机器 overlay。Codex 与 Claude Code 配置始终分别处理。详细计划格式和决策规则见 [导入现有配置](references/importing.md)。

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
- 归并现有配置：`aiconfig import inspect --source codex=<path> --source claude=<path>`
- 根据确认计划生成声明：`aiconfig import generate`
- 可视化审阅导入计划：`aiconfig ui [--open]`
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
- 不静默覆盖导入计划或已有 `agent-config.yaml`。
- 不把不同数组自动合并；只在用户明确选择 `union` 后执行稳定并集。
- UI 只监听回环地址，不上传配置；联网说明只读取公开 Schema，不发送配置路径或值。

## 按需读取参考

- 编写或解释声明时读取 [声明格式](references/declaration-format.md)。
- 从现有文件抽取、去重、解决冲突或剔除字段时读取 [导入现有配置](references/importing.md)。
- 启动可视化审阅或解释联网说明来源时读取 [本地审阅界面](references/ui.md)。
- 处理覆盖、数组操作或删除时读取 [合并规则](references/merge-rules.md)。
- 解释目标边界时读取 [Codex 配置](references/codex-config.md) 或 [Claude 设置](references/claude-settings.md)。
- 遇到稳定错误码时读取 [故障排查](references/troubleshooting.md)。
