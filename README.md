# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、
`command` 和 `hook`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
Claude Code 是原始和主要支持平台，通过 `.claude-plugin/` 发布；Codex 作为补充平台，
通过 `.codex-plugin/`、`.agents/plugins/` 与根目录 `skills/` 薄适配入口发布。两平台共用
`resources/skills/` 下的 Skill 主体，不复制两套业务流程。

## 安装（Claude Code）

在 Claude Code 中执行：

```text
/plugin marketplace add RollRollRoll/agent-toolkit
/plugin install agent-toolkit@agent-toolkit
```

整个工具包作为单一插件 `agent-toolkit` 安装，按需启用方式：

- 插件级：`/plugin` 交互界面，或 `claude plugin enable|disable agent-toolkit`。
- skill 级：在 `/permissions` 中添加 deny 规则，如 `Skill(codebase-analyzer)`。

## 安装（Codex）

在 Codex CLI 中执行：

```text
codex plugin marketplace add RollRollRoll/agent-toolkit
codex plugin add agent-toolkit@agent-toolkit
```

也可以在 Codex CLI 的 `/plugins` 或 Codex App 的 Plugins 界面中，从已添加的
`agent-toolkit` marketplace 安装。安装或更新后新开任务，让 Codex 重新加载 Skill。

## 目录结构

```text
agent-toolkit/
  .claude-plugin/
    plugin.json
    marketplace.json
  .codex-plugin/
    plugin.json
  .agents/plugins/
    marketplace.json
  skills/
    <skill-id>/SKILL.md
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
- `.codex-plugin/`：Codex 插件清单。
- `.agents/plugins/`：Codex 仓库级 marketplace 清单。
- `skills/`：Codex 插件发现用的薄适配入口，转交到 canonical Skill 主体。
- `resources/skills/`：存放两平台共用的 canonical Skill 主体。
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
5. 如果 Skill 要随插件发布：
   - 更新 `.claude-plugin/plugin.json` 的 `skills` 数组；
   - 在 `skills/<skill-id>/SKILL.md` 添加 Codex 薄适配入口；
   - 同步递增 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`
     与 `.codex-plugin/plugin.json` 的版本。

具体格式见：

- `docs/conventions.md`
- `docs/resource-template.md`

## 当前非目标

- 不自动改写用户机器上的 Claude Code / Codex 已安装副本。
- 不做 CLI。
- 不做 schema 校验。
- 不做自动打包、发布或安装流程。
- 不做跨平台格式转换。
