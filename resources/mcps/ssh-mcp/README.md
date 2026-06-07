# SSH MCP

## 用途

让 agent 安全地参与远程服务器运维的 MCP 服务器设计方案。
核心原则：不让 agent 直接拿 shell、不暴露私钥、所有动作可审计、
高危操作可审批可回滚。

当前处于设计阶段（0→1），暂无实现代码和可用配置。

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

## 后续

实现完成后补充 `config.example.json`，并将 `metadata.yaml` 的
`status` 从 `draft` 更新为 `active`。
