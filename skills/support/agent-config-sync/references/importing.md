# 导入现有配置

## 选择交互方式

用户未明确偏好时，先询问是否启动本地前端页面，并等待用户选择。用户同意后以前端作为主要审阅与决策入口；用户拒绝，或 UI 启动失败、页面不可访问、当前环境无法操作页面时，说明原因并切换为逐项问答。前端可用时不要同时在对话中重复询问相同决策。

## 两阶段流程

显式提供一份或多份来源，同一目标可重复：

```bash
aiconfig import inspect \
  --source codex=~/.codex/config.toml \
  --source codex=./backup/config.toml \
  --source claude=~/.claude/settings.json
```

命令默认生成 `.agent-config/import-plan.yaml`。审阅并解决冲突后生成事实文件：

```bash
aiconfig import generate --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

用户选择前端后，启动本地审阅界面完成逐项决策、预览和生成：

```bash
aiconfig ui --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

命令会输出带会话令牌的本地地址；只有用户明确要求自动打开浏览器时才增加 `--open`。界面与手工编辑使用同一份计划格式，决策规则完全一致。联网说明、缓存和本地安全边界见 [本地审阅界面](ui.md)。

使用问答降级时，按计划中的冲突顺序逐项展示候选来源和值，等待用户明确选择 `take`、`union`、`set` 或 `exclude`，再把决定写回计划。不得自行决定，也不得自动合并不同数组。

已有计划或事实文件默认不覆盖；只有用户明确同意时才使用 `--force`。首版只把多份同目标配置归并到 `base`，不推导 overlay，也不跨 Codex 与 Claude Code 合并字段。

## 归并与去重

- 对象递归归并。
- 相同标量或相同完整数组只保留一次，并记录全部来源。
- 不同标量、不同数组或对象与非对象的类型差异标记为 `conflict`。
- 数组不自动取并集，避免破坏命令参数等有顺序语义的字段。
- 疑似秘密标记为 `sensitive`，Claude 越界字段标记为 `out-of-scope`；两者不把原值写入计划并默认剔除。

配置项路径使用 JSON Pointer，例如 `/permissions/allow`。键中的 `~` 写作 `~0`，`/` 写作 `~1`。

## 决策动作

- `keep`：保留无冲突值。
- `take`：从冲突候选中选择一个 `source`。
- `union`：对冲突数组按来源顺序做稳定并集，只去除完全相同的元素。
- `set`：使用 `selectedValue` 明确设置值。
- `exclude`：剔除配置项。
- `unresolved`：未决冲突；阻止生成事实文件。

示例：

```yaml
- path: /model
  status: conflict
  candidates:
    - sources: [codex-1]
      value: gpt-5
    - sources: [codex-2]
      value: gpt-5.1
  action: take
  source: codex-1
```

在目标的 `excludes` 中填写 JSON Pointer 可剔除整个子树：

```yaml
targets:
  codex:
    excludes:
      - /model_providers/custom
```

也可在生成时临时增加剔除项：

```bash
aiconfig import generate --exclude codex=/model_providers/custom
```

不得把 `sensitive` 或 `out-of-scope` 改为保留。需要环境变量占位符时，在导入完成后显式编辑 `agent-config.yaml` 并重新校验。
