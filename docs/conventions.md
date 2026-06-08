# 维护规范

本文档记录 `agent-toolkit` 第一阶段的目录、命名和维护约定。

## 项目定位

本仓库用于管理个人创建的 agent 工具资源，包括：

- `skill`
- `mcp`
- `command`
- `hook`

以个人知识库为主，同时通过 `.claude-plugin/` 清单
将仓库发布为 Claude Code 插件市场。

## 目录职责

- `.claude-plugin/`：Claude Code 插件清单（`plugin.json`）
  与市场清单（`marketplace.json`）。
- `resources/skills/`：个人 skill。
- `resources/mcps/`：MCP 配置或服务说明。
- `resources/commands/`：自定义 command。
- `resources/hooks/`：hook 定义或说明。
- `collections/`：资源组合清单。
- `docs/`：维护规范和模板。

## 命名规则

- 资源目录名使用小写 kebab-case。
- 资源目录名必须与 `metadata.yaml` 的 `id` 一致。
- collection 文件名必须与 collection 的 `id` 一致。
- 资源名应表达用途，不默认添加平台名前缀。
- 暂不使用多级分类目录。

## 资源文件约定

### skill

```text
resources/skills/<skill-id>/
  README.md
  SKILL.md
  metadata.yaml
  references/
  docs/
```

说明：

- `SKILL.md` 为 skill 主体，保留平台原生格式（含 frontmatter），
  可直接复制到目标平台使用。
- `references/` 可选，存放 skill 引用的辅助文件。
- `docs/` 可选，存放该资源的设计与演进记录。

### mcp

```text
resources/mcps/<mcp-id>/
  README.md
  config.example.json
  metadata.yaml
```

### command

```text
resources/commands/<command-id>/
  README.md
  command.md
  metadata.yaml
```

### hook

```text
resources/hooks/<hook-id>/
  README.md
  hook.md
  metadata.yaml
```

## metadata.yaml 字段

```yaml
id: example-id
name: Example Name
type: skill
description: 简短说明
tags: []
status: draft
created_at: 2026-06-07
updated_at: 2026-06-07
```

字段说明：

- `id`：资源唯一标识，必须与目录名一致。
- `name`：资源展示名称。
- `type`：资源类型，只能是 `skill`、`mcp`、`command`、`hook`。
- `description`：一句话说明资源用途。
- `tags`：人工检索标签。
- `status`：资源状态，建议使用 `draft`、`active`、`archived`。
- `created_at`：创建日期。
- `updated_at`：最后维护日期。

## 新增资源流程

1. 在对应 `resources/<type>/` 下创建资源目录。
2. 添加该类型约定的主体文件、`README.md` 和 `metadata.yaml`。
3. 如果该资源属于某个组合，手动更新对应 `collections/*.yaml`。
4. 更新 `metadata.yaml` 的 `updated_at`。
5. 如果资源要随插件发布，更新 `.claude-plugin/plugin.json`
   对应组件数组（`skills` / `commands` / `hooks` / `mcpServers`），
   按语义化版本递增 `version`，并用
   `claude plugin validate . --strict` 校验。

## 新增 collection 流程

1. 在 `collections/` 下创建 `<collection-id>.yaml`。
2. 填写 `id`、`name`、`description` 和资源引用。
3. 只引用已存在资源的 `id`。

## 第一阶段非目标

- 不做自动同步到 Codex、Claude 或其他平台。
- 不做 CLI。
- 不做 schema 校验。
- 不做打包、发布、安装流程。
- 不做跨平台格式转换。
