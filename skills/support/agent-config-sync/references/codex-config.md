# Codex configuration boundaries

`targets.codex.base` and each overlay's `set` use native Codex `config.toml` fields directly. The generator keeps the declaration order, outputs valid TOML, and re-parses it before writing.

This skill only generates the user-level `~/.codex/config.toml`. It does not manage login credentials, project-level config, standalone MCP files, skills, agents, or session data.

