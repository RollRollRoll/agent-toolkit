# Agent Toolkit Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地第一阶段个人知识库型项目结构，用于管理 `skill`、`mcp`、`command` 和 `hook` 资源。

**Architecture:** 仓库采用资源独立、组合清单独立的结构。`resources/` 负责四类资源目录，`collections/` 负责手动组合清单，`docs/` 负责维护规范和模板；不引入 CLI、schema 校验、打包或发布流程。

**Tech Stack:** Markdown、YAML、JSON 示例配置、Git。

---

## File Structure

本计划会创建或修改以下文件：

- Modify: `README.md`
  - 说明项目定位、目录结构、新增资源方式和当前非目标。
- Create: `resources/skills/.gitkeep`
  - 保留空的 skill 资源目录。
- Create: `resources/mcps/.gitkeep`
  - 保留空的 MCP 资源目录。
- Create: `resources/commands/.gitkeep`
  - 保留空的 command 资源目录。
- Create: `resources/hooks/.gitkeep`
  - 保留空的 hook 资源目录。
- Create: `collections/.gitkeep`
  - 保留空的资源组合目录。
- Create: `docs/conventions.md`
  - 记录目录职责、命名规则、元数据字段和维护流程。
- Create: `docs/resource-template.md`
  - 提供新增资源和 collection 时可复制的模板。

不创建示例资源，避免把示例误认为真实内容。

## Task 1: 更新项目 README

**Files:**

- Modify: `README.md`

- [ ] **Step 1: 覆盖 README 为项目入口说明**

将 `README.md` 内容替换为：

````markdown
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
````

- [ ] **Step 2: 验证 README 内容**

Run:

```bash
sed -n '1,120p' README.md
```

Expected:

```text
# agent-toolkit
```

并且输出中包含：

```text
个人 agent 工具资源仓库
```

- [ ] **Step 3: 提交 README 修改**

提交前必须按 AGENTS.md 的危险操作确认机制，获得用户对 `git commit`
的明确确认。

Run:

```bash
git add README.md
git commit -m "Update project overview"
```

Expected:

```text
[main <hash>] Update project overview
```

## Task 2: 创建资源和组合目录

**Files:**

- Create: `resources/skills/.gitkeep`
- Create: `resources/mcps/.gitkeep`
- Create: `resources/commands/.gitkeep`
- Create: `resources/hooks/.gitkeep`
- Create: `collections/.gitkeep`

- [ ] **Step 1: 创建目录和 .gitkeep 文件**

Run:

```bash
mkdir -p resources/skills resources/mcps resources/commands resources/hooks collections
touch resources/skills/.gitkeep resources/mcps/.gitkeep resources/commands/.gitkeep resources/hooks/.gitkeep collections/.gitkeep
```

- [ ] **Step 2: 验证目录存在**

Run:

```bash
find resources collections -maxdepth 2 -type f | sort
```

Expected:

```text
collections/.gitkeep
resources/commands/.gitkeep
resources/hooks/.gitkeep
resources/mcps/.gitkeep
resources/skills/.gitkeep
```

- [ ] **Step 3: 提交目录结构**

提交前必须按 AGENTS.md 的危险操作确认机制，获得用户对 `git commit`
的明确确认。

Run:

```bash
git add resources collections
git commit -m "Add resource directories"
```

Expected:

```text
[main <hash>] Add resource directories
```

## Task 3: 新增维护规范文档

**Files:**

- Create: `docs/conventions.md`

- [ ] **Step 1: 创建 docs/conventions.md**

创建 `docs/conventions.md`，内容为：

````markdown
# 维护规范

本文档记录 `agent-toolkit` 第一阶段的目录、命名和维护约定。

## 项目定位

本仓库用于管理个人创建的 agent 工具资源，包括：

- `skill`
- `mcp`
- `command`
- `hook`

第一阶段只作为个人知识库使用，不绑定插件市场格式。

## 目录职责

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
  content.md
  metadata.yaml
```

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

## 新增 collection 流程

1. 在 `collections/` 下创建 `<collection-id>.yaml`。
2. 填写 `id`、`name`、`description` 和资源引用。
3. 只引用已存在资源的 `id`。

## 第一阶段非目标

- 不做插件市场 manifest。
- 不做自动同步到 Codex、Claude 或其他平台。
- 不做 CLI。
- 不做 schema 校验。
- 不做打包、发布、安装流程。
- 不做跨平台格式转换。
````

- [ ] **Step 2: 验证规范文档**

Run:

```bash
sed -n '1,220p' docs/conventions.md
```

Expected:

```text
# 维护规范
```

并且输出中包含：

```text
resources/skills/<skill-id>/
```

- [ ] **Step 3: 提交维护规范**

提交前必须按 AGENTS.md 的危险操作确认机制，获得用户对 `git commit`
的明确确认。

Run:

```bash
git add docs/conventions.md
git commit -m "Add resource conventions"
```

Expected:

```text
[main <hash>] Add resource conventions
```

## Task 4: 新增资源模板文档

**Files:**

- Create: `docs/resource-template.md`

- [ ] **Step 1: 创建 docs/resource-template.md**

创建 `docs/resource-template.md`，内容为：

````markdown
# 资源模板

新增资源时，从本文件复制对应模板，并替换其中的示例值。

## skill

目录：

```text
resources/skills/<skill-id>/
  README.md
  content.md
  metadata.yaml
```

`README.md`：

```markdown
# Example Skill

## 用途

说明这个 skill 解决什么问题。

## 触发场景

- 说明适合使用它的场景。

## 使用方式

说明如何阅读、复制或迁移这个 skill。
```

`content.md`：

```markdown
# Example Skill

## Instructions

在这里编写 skill 主体内容。
```

`metadata.yaml`：

```yaml
id: example-skill
name: Example Skill
type: skill
description: 示例 skill
tags: []
status: draft
created_at: 2026-06-07
updated_at: 2026-06-07
```

## mcp

目录：

```text
resources/mcps/<mcp-id>/
  README.md
  config.example.json
  metadata.yaml
```

`README.md`：

```markdown
# Example MCP

## 用途

说明这个 MCP 配置或服务解决什么问题。

## 依赖

- 说明需要的运行环境或账号。

## 配置方式

说明如何使用 `config.example.json`。
```

`config.example.json`：

```json
{
  "name": "example-mcp",
  "command": "example-command",
  "args": []
}
```

`metadata.yaml`：

```yaml
id: example-mcp
name: Example MCP
type: mcp
description: 示例 MCP
tags: []
status: draft
created_at: 2026-06-07
updated_at: 2026-06-07
```

## command

目录：

```text
resources/commands/<command-id>/
  README.md
  command.md
  metadata.yaml
```

`README.md`：

```markdown
# Example Command

## 用途

说明这个 command 解决什么问题。

## 参数

- 说明输入参数或上下文要求。

## 使用场景

- 说明适合使用它的场景。
```

`command.md`：

```markdown
# Example Command

在这里编写 command 主体内容。
```

`metadata.yaml`：

```yaml
id: example-command
name: Example Command
type: command
description: 示例 command
tags: []
status: draft
created_at: 2026-06-07
updated_at: 2026-06-07
```

## hook

目录：

```text
resources/hooks/<hook-id>/
  README.md
  hook.md
  metadata.yaml
```

`README.md`：

```markdown
# Example Hook

## 触发时机

说明 hook 在什么时候触发。

## 输入输出

- 说明输入。
- 说明输出。

## 注意事项

- 说明使用限制。
```

`hook.md`：

```markdown
# Example Hook

在这里编写 hook 主体内容。
```

`metadata.yaml`：

```yaml
id: example-hook
name: Example Hook
type: hook
description: 示例 hook
tags: []
status: draft
created_at: 2026-06-07
updated_at: 2026-06-07
```

## collection

文件：

```text
collections/<collection-id>.yaml
```

内容：

```yaml
id: example-toolkit
name: Example Toolkit
description: 示例资源组合
resources:
  skills:
    - example-skill
  mcps:
    - example-mcp
  commands:
    - example-command
  hooks:
    - example-hook
notes: ""
```
````

- [ ] **Step 2: 验证模板文档**

Run:

```bash
sed -n '1,260p' docs/resource-template.md
```

Expected:

```text
# 资源模板
```

并且输出中包含：

```text
collections/<collection-id>.yaml
```

- [ ] **Step 3: 提交资源模板**

提交前必须按 AGENTS.md 的危险操作确认机制，获得用户对 `git commit`
的明确确认。

Run:

```bash
git add docs/resource-template.md
git commit -m "Add resource templates"
```

Expected:

```text
[main <hash>] Add resource templates
```

## Task 5: 最终验证

**Files:**

- Read: `README.md`
- Read: `docs/conventions.md`
- Read: `docs/resource-template.md`
- Read: `docs/superpowers/specs/2026-06-07-agent-toolkit-structure-design.md`

- [ ] **Step 1: 检查关键路径**

Run:

```bash
find . -maxdepth 3 -type f | sort
```

Expected output includes:

```text
./.gitignore
./LICENSE
./README.md
./collections/.gitkeep
./docs/conventions.md
./docs/resource-template.md
./resources/commands/.gitkeep
./resources/hooks/.gitkeep
./resources/mcps/.gitkeep
./resources/skills/.gitkeep
```

- [ ] **Step 2: 检查未引入工具链文件**

Run:

```bash
find . -maxdepth 2 \( -name package.json -o -name pyproject.toml -o -name Cargo.toml -o -name go.mod \) -print
```

Expected:

```text
```

- [ ] **Step 3: 检查非目标没有被实现**

Run:

```bash
find . -maxdepth 3 \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.sh" \) -print
```

Expected:

```text
```

- [ ] **Step 4: 检查工作区状态**

Run:

```bash
git status --short
```

Expected:

```text
```

如果前面每个任务都已提交，最终工作区应为空。
