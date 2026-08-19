# 本地审阅界面

## 默认交互入口

用户未明确偏好时，先询问是否启动本地前端页面，并等待用户选择。用户同意后启动界面，并以前端作为主要操作入口；页面可用时不要同时通过对话逐项提问。只有用户明确希望自动打开浏览器时才使用 `--open`。

用户拒绝，或 UI 启动失败、页面不可访问、当前环境无法操作页面时，简要说明原因并降级为逐项问答，不要反复尝试启动 UI。问答使用与界面相同的 `keep`、`take`、`union`、`set`、`exclude` 决策规则。

先生成导入计划，再启动界面：

```bash
aiconfig import inspect \
  --source codex=~/.codex/config.toml \
  --source claude=~/.claude/settings.json
aiconfig ui --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

界面提供以下能力：

- 展示全部来源、自动去重结果、冲突、敏感字段和越界字段。
- 按目标和状态筛选，并逐项选择 `keep`、`take`、`union`、`set` 或 `exclude`。
- 根据条目状态、本机路径和 Schema 默认值给出保留或剔除建议及理由，但不自动替用户修改决策；冲突项只建议先解决冲突，不替用户选择来源。
- 桌面端滚动配置项列表时，右侧详情保持在当前视口内；选择条目不会把页面跳回详情区顶部。
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
