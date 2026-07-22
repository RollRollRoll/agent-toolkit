# Claude Code / Codex Subagent 映射

派发执行、审查、修复或整体验收前，先确认当前平台并只使用对应一节。两个平台共用任务简报、报告、diff、状态回执和验收闸门，不共用工具参数。

## Claude Code

- 使用 Task / Agent 工具创建 fresh subagent；执行、review、fix 分别建立独立上下文。
- 用 Agent 工具的 `model` 参数映射 cheap / standard / most-capable，具体模型按当前账号可用列表选择。
- 使用 Claude Code 的 permission mode、tool allowlist 与 worktree/subagent isolation；不要用 Codex 的 sandbox 配置解释 Claude 权限。
- 并行任务仍按 `setup-worktree` 锁定 expected base，每个 subagent 只进入自己的 worktree。

## Codex

- Codex 可由 Skill 指令触发 subagent workflow。执行与 fix 优先用内置 `worker`；只读探索可用 `explorer`；review 可用 fresh 默认 agent，或项目 `.codex/agents/` 中明确标为只读的 reviewer。
- 执行、review、fix 必须是不同 agent thread。默认只需要根 agent 直接派发，不要求子 agent 再嵌套派发；若平台限制深度或并发，回退串行，不修改闭环角色分离。
- subagent 继承父任务当前 sandbox 与 approval 选择。开始派发前先确认父任务权限足以完成已授权范围；非交互运行无法弹出新审批时，越权动作会失败，按 `BLOCKED` 处理，不绕过 sandbox。
- cheap / standard / most-capable 继续表示能力档位，不在 Skill 中固定模型名。使用当前 Codex 可用的 model 与 `model_reasoning_effort` 映射；机械任务取较快档，跨文件实现与 review 至少标准档，阶段 3 整体验收取最强可用档。
- Codex 同一任务树中的 agent 可能共享文件系统视图。默认串行；并行写任务必须各自使用独立 worktree，并在派发 prompt 的 `[目录]` 写入不同绝对路径。review agent 保持只读，不与执行 agent 同时修改同一 checkout。
- Codex App 托管 Worktree 默认 detached HEAD；若任务需要原子 commit，先按 `setup-worktree` 明确 HEAD 状态与分支策略。Codex CLI / IDE 不假设存在 App 的 Worktree/Handoff UI。

## 共同失败处理

- 平台没有 subagent、模型参数或所需隔离能力时，明确记录降级原因，由主 agent 顺序执行同一套 TDD → 验证 → 独立审查视角 → commit 纪律。
- 不因平台差异删除任务基线、diff 审查、测试证据、用户提交授权或整体验收门。
