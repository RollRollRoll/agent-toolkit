# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、
`command` 和 `hook`。

第一阶段只作为个人知识库使用，重点是让资源清晰、独立、可维护。
暂不绑定任何插件市场格式，也不提供 CLI、打包、发布或自动同步能力。

## 目录结构

```text
agent-toolkit/
  resources/
    skills/
    mcps/
    commands/
    hooks/
  collections/
  docs/
```

## 目录职责

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

具体格式见：

- `docs/conventions.md`
- `docs/resource-template.md`

## 当前非目标

- 不做插件市场 manifest。
- 不做自动同步到 Codex、Claude 或其他平台。
- 不做 CLI。
- 不做 schema 校验。
- 不做打包、发布、安装流程。
- 不做跨平台格式转换。
