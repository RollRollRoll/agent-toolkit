# 声明格式

声明文件名默认为 `agent-config.yaml`，顶层结构如下：

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

每个 overlay 包含 `name`、`when`、可选 `variables` 和 `set`。`when` 支持 `os`、`runtime`、`hostname`、`profile` 及 `tags.contains`，各条件使用 AND；字符串列表表示匹配其中任意一个值。主机名忽略大小写。

上下文优先级为：自动检测值 < `~/.config/aiconfig/context.yaml` < 命令行 `--profile` / `--tag`。支持变量 `${os}`、`${runtime}`、`${hostname}`、`${user}`、`${home}`、`${profile}`、自定义变量和 `${env:NAME}`；环境变量默认值写作 `${env:NAME:-fallback}`。

