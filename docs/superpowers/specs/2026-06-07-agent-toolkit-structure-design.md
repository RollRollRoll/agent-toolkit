# Agent Toolkit 项目结构设计

日期：2026-06-07

## 背景

`agent-toolkit` 用于管理个人创建的 agent 工具资源，包括 `skill`、`mcp`、
`command` 和 `hook`。

第一阶段定位为个人知识库型资源仓库。重点是让资源清晰、独立、可维护，
暂不绑定任何插件市场格式，也不引入 CLI、构建、打包或发布流程。

## 已确认选择

- 项目第一阶段选择“内容仓库优先”。
- 项目第一阶段选择“只做个人知识库”。
- 资源未来可能组合成插件包，但第一阶段只手动记录组合关系。

## 目标

- 为四类资源提供稳定、清晰的目录边界。
- 每个资源都能独立维护、阅读和复用。
- 使用轻量元数据支持人工检索和未来扩展。
- 使用 `collections/` 手动记录资源组合关系。
- 保持结构简单，不为未实现的平台注册能力提前设计复杂抽象。

## 非目标

第一阶段不做以下内容：

- 插件市场 manifest。
- 自动同步到 Codex、Claude 或其他平台。
- CLI。
- schema 校验。
- 打包、发布、安装流程。
- 跨平台格式转换。

## 推荐目录结构

```text
agent-toolkit/
  README.md
  LICENSE
  .gitignore

  resources/
    skills/
      <skill-id>/
        README.md
        content.md
        metadata.yaml

    mcps/
      <mcp-id>/
        README.md
        config.example.json
        metadata.yaml

    commands/
      <command-id>/
        README.md
        command.md
        metadata.yaml

    hooks/
      <hook-id>/
        README.md
        hook.md
        metadata.yaml

  collections/
    <collection-id>.yaml

  docs/
    conventions.md
    resource-template.md
```

## 目录职责

### resources/

`resources/` 存放所有可复用资源。每类资源使用单独子目录：

- `resources/skills/`：个人 skill。
- `resources/mcps/`：MCP 配置或服务说明。
- `resources/commands/`：自定义 command。
- `resources/hooks/`：hook 定义或说明。

每个资源都使用独立目录。目录名即资源 `id`，使用小写 kebab-case。

### collections/

`collections/` 存放资源组合清单。

一个 collection 只描述“哪些资源属于同一组”，不承担插件市场注册、
发布或安装职责。

示例：

```yaml
id: writing-toolkit
name: Writing Toolkit
description: 写作相关的个人 agent 工具集合
resources:
  skills:
    - writing-style
  mcps: []
  commands:
    - draft-outline
  hooks: []
notes: ""
```

### docs/

`docs/` 存放项目维护规范和模板。

- `docs/conventions.md`：命名、目录职责、状态字段、新增资源流程。
- `docs/resource-template.md`：新增资源时复制使用的模板说明。

## 资源文件约定

### skill

```text
resources/skills/<skill-id>/
  README.md
  content.md
  metadata.yaml
```

- `README.md`：说明用途、触发场景、使用方式。
- `content.md`：skill 主体内容。
- `metadata.yaml`：资源元数据。

### mcp

```text
resources/mcps/<mcp-id>/
  README.md
  config.example.json
  metadata.yaml
```

- `README.md`：说明用途、依赖、配置方式。
- `config.example.json`：示例配置，不存放敏感信息。
- `metadata.yaml`：资源元数据。

### command

```text
resources/commands/<command-id>/
  README.md
  command.md
  metadata.yaml
```

- `README.md`：说明用途、参数、使用场景。
- `command.md`：command 主体内容。
- `metadata.yaml`：资源元数据。

### hook

```text
resources/hooks/<hook-id>/
  README.md
  hook.md
  metadata.yaml
```

- `README.md`：说明触发时机、输入输出、注意事项。
- `hook.md`：hook 主体内容。
- `metadata.yaml`：资源元数据。

## 元数据约定

所有资源统一使用轻量 `metadata.yaml`。

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

字段含义：

- `id`：资源唯一标识，必须与目录名一致。
- `name`：资源展示名称。
- `type`：资源类型，只能是 `skill`、`mcp`、`command`、`hook`。
- `description`：一句话说明资源用途。
- `tags`：人工检索标签。
- `status`：资源状态，建议使用 `draft`、`active`、`archived`。
- `created_at`：创建日期。
- `updated_at`：最后维护日期。

## 命名规则

- 目录名和 `id` 使用小写 kebab-case。
- 资源目录名应表达用途，不使用平台名作为默认前缀。
- collection 文件名与 collection `id` 保持一致。
- 暂不引入多级分类，避免目录层级过深。

## 维护流程

新增资源：

1. 在对应 `resources/<type>/` 下创建资源目录。
2. 添加该类型约定的主体文件、`README.md` 和 `metadata.yaml`。
3. 如果该资源属于某个组合，手动更新对应 `collections/*.yaml`。
4. 更新 `metadata.yaml` 的 `updated_at`。

新增 collection：

1. 在 `collections/` 下创建 `<collection-id>.yaml`。
2. 填写 `id`、`name`、`description` 和资源引用。
3. 只引用已存在资源的 `id`。

## 验证标准

结构落地后应满足：

- 根目录保留 `README.md`、`LICENSE`、`.gitignore`。
- 存在 `resources/skills/`、`resources/mcps/`、`resources/commands/`、
  `resources/hooks/`。
- 存在 `collections/`。
- 存在 `docs/conventions.md` 和 `docs/resource-template.md`。
- `README.md` 能说明项目定位和新增资源方式。
- 未引入不必要的工具链文件。

## 后续扩展

如果未来需要注册到插件市场，可以在不破坏现有结构的基础上新增：

- 市场专用 manifest 生成规则。
- 资源和 collection 的校验脚本。
- 打包或同步脚本。
- 平台适配层文档。

这些能力不属于第一阶段。
