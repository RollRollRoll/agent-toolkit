# Execute Task

## 用途

**workflow 层**的最后一棒：把一份**已确认的任务清单**（理想情况下来自 split-task），**编排**成
实现 + 测试 + 提交，并经验收确认"真的做完了"。

它自己只做编排——按依赖 / wave 调度（默认串行，仅在隔离、同基线、无冲突和 merge 授权齐备时并行）、
为每个任务备齐**约定的 seam**、凭证据过闸门、把 checkbox 与代码一起原子提交、记可恢复账本、
做覆盖核对回扫、把收尾决策交给用户。**具体能力一律调用 composable 层**：

| 调用点 | composable skill |
|---|---|
| 阶段 1 需要隔离 / 并行 | **setup-worktree** |
| 阶段 2 每个任务的红 → 绿闭环 | **tdd** |
| 阶段 3 整体审查（五轴 + 测试质量） | **review-changes** |
| 阶段 4 收尾 | **finish-branch** |

调用即交出该层的判据定义权：本 skill 不重述 tdd 的循环规则，也不重述 review-changes 的审查判据。

**任务内不派任何 subagent**（调用 tdd 是加载执行纪律，不是派发），也没有审查轮与修复轮：
闸门一核的是可机械判定的证据——红 → 绿输出当场落盘且齐、收尾完整跑一次验证命令绿、HEAD 未漂移；
架构级审查与修复集中到阶段 3 做一次，那也是全流程唯一的 subagent 派发点。
任何代码修改前必须先获得用户对当前分支、任务范围和提交批次的明确授权；每任务从干净 HEAD 开始，
代码、测试与 tasks checkbox 进入同一个原子提交。

它是这条链**唯一真正写代码**的 skill，填补"任务拆好了"和"功能交付"之间的最后一棒：
自包含（运行时只调用本工具集内的 skill，不依赖外部插件），守层（不拆任务 / 不定决策 / 不定行为）。

## 触发场景

- "tasks 定了，开始执行 / 把这些任务做掉 / 按任务清单编码 / 用 TDD 把任务做掉"
- "实现 split-task 拆出来的任务"
- "推进开发，逐个任务落地"
- 不适用：任务还没拆（先 split-task）；技术方案没定（先 make-design）；行为没钉死（先 write-spec）；
  想法还模糊（先 refine-idea）；只做**单个改动**的红绿闭环（直接用 **tdd**）；
  只做**一次代码审查**（直接用 **review-changes**）；单纯调试某个 bug；纯代码评审。

## 使用方式

将本目录下的 `SKILL.md`、`references/` 和 `scripts/` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/execute-task/`；Codex：`.agents/skills/execute-task/`）即可直接使用；
若 `scripts/` 下脚本丢失可执行权限，按所在环境的权限变更规则取得确认后，再补一次 `chmod +x scripts/*.sh`。
它调用的 **tdd / review-changes / setup-worktree / finish-branch** 需要同时可用。

阶段 2 由主 agent 自己执行，不派 subagent。只有阶段 3 整体验收派 review / fix：
Claude Code 用 Task / Agent 工具，Codex 用 agent thread；review subagent 一律加载 `review-changes` 执行。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/orchestration.md`：调度与编排——依赖 / wave 排序、并行与 worktree 隔离、每任务的工作文件、进度账本与 safe-resume。
- `references/acceptance.md`：双验收闸门——闸门一证据核对、闸门二派发编排与 fix 循环、覆盖核对回扫、上游纠错守层、收尾。
- `references/handoff-templates.md`：任务简报的准备，以及阶段 3 整体验收 review / fix 的派发 prompt。
- `references/model-selection.md`：模型选择——阶段 3 review / fix 的档位判据（阶段 2 无派发、无定档）。
- `references/platform-agents.md`：Claude Code / Codex 在阶段 3 的 subagent、权限、模型与工作目录映射。
- `scripts/workspace.sh`：工作目录 `.execute-task/` 的单一事实来源（建目录 + 自忽略 `.gitignore`，打印路径）。
- `scripts/task-brief.sh`：从 tasks 文档机械抽取单个任务全文生成简报基底，防手抄失真；design/spec 片段与约定的 seam 随后追加。
- `scripts/task-baseline.sh`：每任务开工前确认真实工作区干净并记录 HEAD，供闸门一核对 HEAD 未漂移。

审查包由 `review-changes` 的 `scripts/review-package.sh` 生成，执行记录由 `tdd` 的
`scripts/tdd-record.sh` 建立——两者都接受 `.execute-task/` 作为输出目录，工作文件仍落在一处。
