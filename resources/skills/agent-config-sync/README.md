# Agent Config Sync

## 用途

从可纳入版本控制的 `agent-config.yaml`，按操作系统、运行环境、主机、profile 和 tag 生成：

- `~/.codex/config.toml`
- `~/.claude/settings.json`

生成过程支持条件 overlay、变量替换、深度合并、差异预览、备份、原子写入和本地修改保护。

## 使用方式

直接运行 Skill 附带脚本：

```bash
python3 scripts/aiconfig.py --help
```

也可在本目录安装为 Python 项目后使用 `aiconfig` 命令。声明示例位于 `assets/agent-config.example.yaml`。

## 安全边界

本 Skill 不同步凭据、Token、登录状态、`~/.claude.json`、项目级配置或 MCP/skills/agents/hooks 文件。

