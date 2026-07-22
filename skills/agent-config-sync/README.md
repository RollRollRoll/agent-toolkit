# Agent Config Sync

## 用途

从可纳入版本控制的 `agent-config.yaml`，按操作系统、运行环境、主机、profile 和 tag 生成：

- `~/.codex/config.toml`
- `~/.claude/settings.json`

生成过程支持条件 overlay、变量替换、深度合并、差异预览、备份、原子写入和本地修改保护。

也可先把用户明确提供的一份或多份现有 Codex/Claude Code 配置归并为可审阅计划，在用户选择冲突来源、数组并集或剔除项后生成 `agent-config.yaml`。首版不自动推导多机器 overlay。

## 使用方式

直接运行 Skill 附带脚本：

```bash
python3 scripts/aiconfig.py --help
```

也可在本目录安装为 Python 项目后使用 `aiconfig` 命令。声明示例位于 `assets/agent-config.example.yaml`。

从现有配置生成声明：

```bash
python3 scripts/aiconfig.py import inspect \
  --source codex=~/.codex/config.toml \
  --source claude=~/.claude/settings.json
python3 scripts/aiconfig.py import generate
```

也可在浏览器中审阅来源、冲突与导出结果，并查询配置项说明：

```bash
python3 scripts/aiconfig.py ui --open
```

界面只监听 `127.0.0.1`，不会上传配置。联网说明来自公开配置 Schema，并在本地缓存 24 小时。详见 `references/ui.md`。

## 安全边界

本 Skill 不同步凭据、Token、登录状态、`~/.claude.json`、项目级配置或 MCP/skills/agents/hooks 文件。
