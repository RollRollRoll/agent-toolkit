# Glossary

## 通知插件

- **Agent**：触发通知的编码代理，取值 Claude Code 或 Codex CLI。
- **项目（Project）**：会话 cwd 所在 git 仓库根目录名；不在 git 仓库时为 cwd 末级目录名。
- **会话（Session）**：Agent 提供的 `session_id`；通知中显示前 8 位作为会话短 ID。
- **通知事件（Notification Event）**：由 Agent 原始 hook payload 归一化得到的统一事件，类型为下列之一：
  - **回合完成**：Agent 结束当前回合（Codex 中与「等待输入」合并为「回合结束，等待输入」）。
  - **等待输入**：Agent 空闲等待用户回复（仅 Claude Code 原生支持）。
  - **需要授权**：Agent 请求人工批准某个操作。
  - **异常**：回合因 API 等错误终止（仅 Claude Code 支持）。
- **渠道（Channel）**：通知的投递目标，实现统一的 `send` 接口；本版只有 Telegram。
- **隐私模式**：只发送元信息与事件类型，不发送消息摘要或命令预览。
