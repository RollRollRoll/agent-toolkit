# Execute Task

## 用途

把一份**已确认的任务清单**（理想情况下来自 split-task），逐个落地成**实现 + 测试 + 提交**：
按依赖 / wave 调度，每个任务由 fresh subagent 走"TDD → 验证 → 审查 → 原子提交"的干净闭环，
进度用 checkbox + 账本记录可恢复，最后做整体五轴 review + 覆盖核对回扫确认不落空，
收尾的合并 / PR 交用户拍板。

它是这条链**唯一真正写代码**的 skill，填补"任务拆好了"和"功能交付"之间的最后一棒：
自包含（以 superpowers 执行逻辑为骨架、融合五源，运行时不依赖外部插件），守层（不拆任务 / 不定决策 / 不定行为）。

## 触发场景

- "tasks 定了，开始执行 / 把这些任务做掉 / 按任务清单编码"
- "实现 split-task 拆出来的任务"
- "推进开发，逐个任务落地"
- 手上有 split-task 的任务清单，要继续往下落地实现。
- 不适用：任务还没拆（先 split-task）；技术方案没定（先 make-design）；行为没钉死（先 write-spec）；
  想法还模糊（先 refine-idea）；单纯调试某个 bug；纯代码评审。

## 使用方式

将本目录下的 `SKILL.md` 和 `references/` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/execute-task/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/orchestration.md`：调度与编排——依赖 / wave 排序、并行与 worktree 隔离、subagent 派发、进度账本与 safe-resume。
- `references/execution-loop.md`：每任务闭环——TDD seam / tracer bullet、小步推进、验证节奏、审查与 fix loop、atomic commit、bug 诊断。
- `references/acceptance.md`：验收与收尾——每任务验收门、整体五轴 review、覆盖核对回扫、上游纠错守层、收尾。
- `docs/`：开发过程中的设计文档。
