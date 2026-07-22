---
name: agent-config-sync
description: 声明式管理并跨 Windows、Linux、macOS 与 WSL 同步 Codex ~/.codex/config.toml 和 Claude Code ~/.claude/settings.json。用于初始化、检测、校验、渲染、预览差异、应用、检查状态或诊断 agent-config.yaml；不用于凭据、登录状态、项目级配置、~/.claude.json、skills、agents、hooks 或 MCP 配置。
---

完整读取并严格执行 [Agent Config Sync 主体](../../resources/skills/agent-config-sync/SKILL.md)。
后续相对引用以该主体文件所在目录为基准解析。本文件只作为 Codex 插件的薄适配入口，不改变 Claude Code 使用的原始 Skill。

