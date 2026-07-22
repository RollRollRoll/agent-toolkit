# 本地审阅界面

先生成导入计划，再启动界面：

```bash
aiconfig import inspect \
  --source codex=~/.codex/config.toml \
  --source claude=~/.claude/settings.json
aiconfig ui --plan .agent-config/import-plan.yaml --output agent-config.yaml --open
```

界面提供以下能力：

- 展示全部来源、自动去重结果、冲突、敏感字段和越界字段。
- 按目标和状态筛选，并逐项选择 `keep`、`take`、`union`、`set` 或 `exclude`。
- 把决策即时写回导入计划，冲突全部解决后预览事实 YAML、Codex TOML 与 Claude JSON。
- 下载预览，或生成 `agent-config.yaml`；已有文件必须再次确认，覆盖前自动备份。
- 联网读取 Codex 与 Claude Code 配置 Schema 的字段说明、类型、允许值和默认值。

## 网络与缓存

- Codex Schema：`https://developers.openai.com/codex/config-schema.json`
- Claude Code Schema：`https://json.schemastore.org/claude-code-settings.json`
- Schema 默认缓存 24 小时，位置为 `~/.config/aiconfig/docs-cache.json`。
- 刷新失败但存在旧缓存时，界面标记“离线缓存”；没有缓存时显示错误，不编造字段说明。
- 点击官方 Schema 链接会打开外部网页，但不会在 URL 中携带配置路径或配置值。

## 本地安全边界

服务只监听 `127.0.0.1`，并为每次启动生成随机会话令牌。令牌进入浏览器后保存在当前标签页会话中，并从地址栏移除；所有本地 API 都要求令牌。界面资源不依赖 CDN，不上传导入计划，也不提供远程部署模式。

默认端口为 `8765`；端口冲突时可指定其他端口，或使用 `--port 0` 自动分配。按 `Ctrl-C` 停止服务。只有用户明确希望打开浏览器时才使用 `--open`。
