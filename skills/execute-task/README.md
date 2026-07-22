# Execute Task

## 用途

把一份**已确认的任务清单**（理想情况下来自 split-task），逐个落地成**实现 + 测试 + 提交**：
按依赖 / wave 调度（默认串行，仅在隔离、同基线、无冲突和 merge 授权齐备时并行），每个任务走"执行 subagent（TDD → 验证）→ 独立 review subagent 审查 → 独立 fix subagent 修复 → 原子提交"的干净闭环，
进度用 checkbox + 账本记录可恢复，最后做整体五轴 review + 覆盖核对回扫确认不落空，
收尾的合并 / PR 交用户拍板。
任何代码修改前必须先获得用户对当前分支、任务范围和提交批次的明确授权；每任务从干净 HEAD 开始，
审查包覆盖全部未提交变化，代码、测试与 tasks checkbox 进入同一个原子提交。

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

将本目录下的 `SKILL.md`、`references/` 和 `scripts/` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/execute-task/`；Codex：`.agents/skills/execute-task/`）即可直接使用；
若 `scripts/` 下脚本丢失可执行权限，按所在环境的权限变更规则取得确认后，再补一次 `chmod +x scripts/*.sh`。

Claude Code 使用 Task / Agent 工具派发执行、审查和修复 subagent；Codex 使用 agent thread，并可按角色选
内置 `worker` / `explorer` 或项目自定义 agent。两者共用同一套任务闭环、验收和提交纪律。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/orchestration.md`：调度与编排——依赖 / wave 排序、并行与 worktree 隔离、subagent 派发、进度账本与 safe-resume。
- `references/execution-loop.md`：每任务闭环——TDD seam / tracer bullet、小步推进、验证节奏、独立 review / fix subagent 闭环、atomic commit、bug 诊断。
- `references/acceptance.md`：验收与收尾——每任务验收门、整体五轴 review、覆盖核对回扫、上游纠错守层、收尾。
- `references/model-selection.md`：模型选择——派发执行 / review / fix subagent 与整体验收时，按角色与复杂度定档。
- `references/platform-agents.md`：Claude Code / Codex 的 subagent、权限、模型与工作目录映射。
- `scripts/workspace.sh`：交接目录 `.execute-task/` 的单一事实来源（建目录 + 自忽略 `.gitignore`，打印路径），其余脚本经它取目录。
- `scripts/task-brief.sh`：从 tasks 文档机械抽取单个任务全文生成简报基底，防手抄失真；design/spec 片段由主 agent 追加。
- `scripts/task-baseline.sh`：每任务开工前确认真实工作区干净并记录 HEAD，供任务审查校验提交漂移。
- `scripts/review-diff.sh`：生成派 review 前的完整任务 diff（暂存、未暂存、删除、未跟踪、binary、-U10），不修改真实 index。
- `scripts/acceptance-diff.sh`：拒绝 dirty 工作区后生成阶段 3 整体验收审查包（BASE..HEAD 的 commit 清单 + 变更统计 + 完整 diff）。
- `docs/`：开发过程中的设计文档。
