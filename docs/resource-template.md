# 资源模板

新增资源时，从本文件复制对应模板，并替换其中的示例值。

## skill

目录：

```text
skills/<skill-id>/
  README.md
  SKILL.md
  metadata.yaml
  references/
  docs/
  scripts/
  assets/
```

Claude Code 和 Codex 共用这个完整目录。`references/`、`docs/`、`scripts/` 和
`assets/` 子目录可选，按需添加；`SKILL.md` 使用相对路径引用这些 supporting files。

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

`SKILL.md`：

```markdown
---
name: example-skill
description: 说明何时应触发本 skill。
---

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
mcps/<mcp-id>/
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
commands/<command-id>/
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
hooks/<hook-id>/
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
