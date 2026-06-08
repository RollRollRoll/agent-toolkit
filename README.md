# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、
`command` 和 `hook`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
同时通过 `.claude-plugin/` 清单将仓库发布为 Claude Code 插件市场，
供他人下载安装。

## 安装（Claude Code）

在 Claude Code 中执行：

```text
/plugin marketplace add RollRollRoll/agent-toolkit
/plugin install agent-toolkit@agent-toolkit
```

整个工具包作为单一插件 `agent-toolkit` 安装，按需启用方式：

- 插件级：`/plugin` 交互界面，或 `claude plugin enable|disable agent-toolkit`。
- skill 级：在 `/permissions` 中添加 deny 规则，如 `Skill(codebase-analyzer)`。

## 目录结构

```text
agent-toolkit/
  .claude-plugin/
    plugin.json
    marketplace.json
  resources/
    skills/
    mcps/
    commands/
    hooks/
  collections/
  docs/
```

## 目录职责

- `.claude-plugin/`：Claude Code 插件与市场清单。
- `resources/skills/`：存放个人 skill。
- `resources/mcps/`：存放 MCP 配置或服务说明。
- `resources/commands/`：存放自定义 command。
- `resources/hooks/`：存放 hook 定义或说明。
- `collections/`：手动记录资源组合关系。
- `docs/`：存放维护规范和模板。

## 新增资源

1. 在对应的 `resources/<type>/` 下创建资源目录。
2. 添加 `README.md`、资源主体文件和 `metadata.yaml`。
3. 如果资源属于某个组合，更新对应的 `collections/*.yaml`。
4. 手动维护 `metadata.yaml` 的 `updated_at`。
5. 如果资源要随插件发布，更新 `.claude-plugin/plugin.json`
   对应组件数组，并递增 `version`。

具体格式见：

- `docs/conventions.md`
- `docs/resource-template.md`

## 当前非目标

- 不做自动同步到 Codex、Claude 或其他平台。
- 不做 CLI。
- 不做 schema 校验。
- 不做打包、发布、安装流程。
- 不做跨平台格式转换。
