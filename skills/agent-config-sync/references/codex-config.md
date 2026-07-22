# Codex 配置边界

`targets.codex.base` 与各 overlay 的 `set` 直接使用 Codex `config.toml` 原生字段。生成器保持声明顺序、输出合法 TOML，并在写入前重新解析。

本 Skill 只生成用户级 `~/.codex/config.toml`，不管理登录凭据、项目级配置、MCP 独立文件、skills、agents 或会话数据。

