# Claude Code settings.json 边界

`targets.claude.base` 与各 overlay 的 `set` 直接使用 Claude Code `settings.json` 原生字段。生成器输出 UTF-8、两空格缩进 JSON，不增加工具元数据。

本 Skill 不管理 `~/.claude.json`、凭据、OAuth Token、项目级设置、hooks 或会话数据。

下列字段属于其他 Claude Code 文件，不允许写入 `settings.json`。校验器从本节读取清单，更新字段时无需修改 Skill 提示词或 Python 常量。

<!-- rejected-fields:start -->
- `autoConnectIde`
- `autoInstallIdeExtension`
- `diffTool`
- `externalEditorContext`
<!-- rejected-fields:end -->

