# Declaration format

The declaration file is named `agent-config.yaml` by default. Its top-level structure is:

```yaml
apiVersion: agent-config/v1
variables: {}
targets:
  codex:
    output: "~/.codex/config.toml"
    base: {}
    overlays: []
  claude:
    output: "~/.claude/settings.json"
    base: {}
    overlays: []
```

Each overlay contains `name`, `when`, optional `variables`, and `set`. `when` supports `os`, `runtime`, `hostname`,
`profile`, and `tags.contains`. Conditions are combined with AND; a list of strings matches any one of its values. Hostnames are case-insensitive.

Context precedence is: auto-detected values < `~/.config/aiconfig/context.yaml` < command-line `--profile` / `--tag`. Supported variables are `${os}`,
`${runtime}`, `${hostname}`, `${user}`, `${home}`, `${profile}`, custom variables, and `${env:NAME}`.
Write an environment variable default as `${env:NAME:-fallback}`.

