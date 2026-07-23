# SSH MCP

## 用途

让 agent 安全地参与远程服务器运维的 MCP 服务器。
核心原则：不让 agent 直接拿 shell、不暴露私钥、所有动作可审计、
高危操作可审批可回滚。

实现位于 [RollRollRoll/ssh-mcp](https://github.com/RollRollRoll/ssh-mcp)。
本目录不复制上游源码，仅保留资源说明、设计资料与元数据。SSH MCP 已合并进
仓库根目录的 `agent-toolkit` 插件，两个平台均通过 npm 上的固定版本启动服务。

使用前请在启动 Codex 或 Claude Code 的环境中设置 `SSH_MCP_CONFIG`，
其值必须是本机 YAML 配置文件的绝对路径。

## 设计要点

- 洋葱型分层 + 单点 PolicyEngine 安全闸门（8 段规则栈）。
- 审批四步闭环（plan → request → approve → apply）+ token/nonce 一次性凭证。
- 统一 Tool Contract（9 必备字段）与 ToolResult Envelope。
- stdio + Streamable HTTP 双 transport 共用同一安全治理。
- 17 个业务模块，映射为 16 个能力规格：主机资产 / 命令执行 /
  系统巡检 / 服务管理 / 日志 / 文件 / 网络 / 批量 / 长任务 /
  审批 / 审计等。
- 技术栈：Python 3.11+ / asyncssh / aiosqlite / 官方 mcp SDK / pydantic。

## 目录说明

- `docs/proposal.md`：变更提案（why / what / capabilities）。
- `docs/brainstorm.md`：前期头脑风暴。
- `docs/design.md`：架构设计。
- `docs/plan.md`：实现计划。
- `docs/tasks.md`：任务拆解。
- `docs/specs/`：16 个能力模块的规格。

## 发布文件

- `../../.codex-plugin/plugin.json`：Codex 根插件清单。
- `../../.claude-plugin/plugin.json`：Claude Code 根插件清单。
- `../../.mcp.json`：两个平台共用的 stdio MCP 启动配置。
