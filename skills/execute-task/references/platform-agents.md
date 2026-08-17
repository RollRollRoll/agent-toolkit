# Claude Code / Codex Subagent 映射

本 skill **只在阶段 3 整体验收派 subagent**（review 与 fix）；阶段 2 每个任务由主 agent 自己执行，
不涉及派发。派发前先确认当前平台并只使用对应一节。两个平台共用任务简报、执行记录和验收闸门，不共用工具参数。

## Claude Code

- 使用 Task / Agent 工具创建 fresh subagent；阶段 3 的 review 与 fix 各自独立上下文。
- 用 Agent 工具的 `model` 参数映射 standard / most-capable，具体模型按当前账号可用列表选择。
- 使用 Claude Code 的 permission mode 与 tool allowlist；不要用 Codex 的 sandbox 配置解释 Claude 权限。
- review subagent 保持只读——不动工作区、不动 git 状态。

## Codex

- Codex 可由 Skill 指令触发 subagent workflow。阶段 3 review 可用 fresh 默认 agent，或项目 `.codex/agents/`
  中明确标为只读的 reviewer；fix 优先用内置 `worker`。
- 阶段 3 的 review 与 fix 必须是不同 agent thread。默认只需要根 agent 直接派发，不要求子 agent 再嵌套派发；
  若平台限制深度或并发，回退串行，不修改角色分离。
- subagent 继承父任务当前 sandbox 与 approval 选择。开始派发前先确认父任务权限足以完成已授权范围；
  非交互运行无法弹出新审批时，越权动作会失败，按阻塞处理，不绕过 sandbox。
- standard / most-capable 继续表示能力档位，不在 Skill 中固定模型名。使用当前 Codex 可用的 model 与
  `model_reasoning_effort` 映射；阶段 3 整体验收取最强可用档。
- review agent 保持只读，不与 fix agent 同时修改同一 checkout。
- Codex App 托管 Worktree 默认 detached HEAD；若需要原子 commit，先按 `setup-worktree` 明确 HEAD 状态与分支策略。
  Codex CLI / IDE 不假设存在 App 的 Worktree/Handoff UI。

## 并行任务的工作目录

阶段 1 判定可并行时，隔离仍按 `setup-worktree` 锁定 expected base，每个任务一个 worktree——
这与 subagent 无关，是主 agent 自己在不同 worktree 间切换执行。

## 共同失败处理

- 平台没有 subagent 或模型参数能力时，明确记录降级原因，由主 agent 以 fresh 视角完整走一遍阶段 3 的五轴审查
  （读 `acceptance-diff.sh` 生成的整体包，按 acceptance.md 的五轴 + 测试质量逐项判定），**不删掉那道门**。
- 不因平台差异删除任务基线、红 → 绿证据、用户提交授权或整体验收门。
