# Execute Task

## 用途

把一份**已确认的任务清单**（理想情况下来自 split-task），逐个落地成**实现 + 测试 + 提交**：
按依赖 / wave 调度（默认串行，仅在隔离、同基线、无冲突和 merge 授权齐备时并行），每个任务走
"执行 subagent 在约定 seam 上红 → 绿 TDD → 验证 → 主 agent 核证据 → 原子提交"的干净闭环，
进度用 checkbox + 账本记录可恢复，最后做一次整体五轴 + 测试质量 review + 覆盖核对回扫确认不落空，
收尾的合并 / PR 交用户拍板。
**任务内只有 TDD，没有审查轮与修复轮**：闸门一核的是可机械判定的证据——红 → 绿输出齐、主 agent 自己复跑验证命令绿、
HEAD 未漂移；架构级审查与修复集中到阶段 3 整体验收做一次。
任何代码修改前必须先获得用户对当前分支、任务范围和提交批次的明确授权；每任务从干净 HEAD 开始，
代码、测试与 tasks checkbox 进入同一个原子提交。

它是这条链**唯一真正写代码**的 skill，填补"任务拆好了"和"功能交付"之间的最后一棒：
自包含（以 superpowers 执行逻辑为骨架、融合五源，运行时不依赖外部插件），守层（不拆任务 / 不定决策 / 不定行为）。

## 触发场景

- "tasks 定了，开始执行 / 把这些任务做掉 / 按任务清单编码 / 用 TDD 把任务做掉"
- "实现 split-task 拆出来的任务"
- "推进开发，逐个任务落地"
- 手上有 split-task 的任务清单，要继续往下落地实现。
- 不适用：任务还没拆（先 split-task）；技术方案没定（先 make-design）；行为没钉死（先 write-spec）；
  想法还模糊（先 refine-idea）；单纯调试某个 bug；纯代码评审。

## 使用方式

将本目录下的 `SKILL.md`、`references/` 和 `scripts/` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/execute-task/`；Codex：`.agents/skills/execute-task/`）即可直接使用；
若 `scripts/` 下脚本丢失可执行权限，按所在环境的权限变更规则取得确认后，再补一次 `chmod +x scripts/*.sh`。

Claude Code 使用 Task / Agent 工具派发执行 subagent（阶段 3 另派 review / fix）；Codex 使用 agent thread，并可按角色选
内置 `worker` / `explorer` 或项目自定义 agent。两者共用同一套 TDD 闭环、证据核对和提交纪律。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/orchestration.md`：调度与编排——依赖 / wave 排序、并行与 worktree 隔离、执行 subagent 派发与状态回执、进度账本与 safe-resume。
- `references/execution-loop.md`：每任务 TDD 闭环——seam 约定、好测试判据、三个反模式（实现耦合 / 同义反复 / 水平切片）、循环规则、验证节奏、闸门一证据核对、atomic commit、bug 诊断。
- `references/handoff-templates.md`：派发 prompt 模板——执行 subagent，以及阶段 3 整体验收 review / fix。
- `references/acceptance.md`：验收与收尾——每任务证据门、整体五轴 + 测试质量 review、覆盖核对回扫、上游纠错守层、收尾。
- `references/model-selection.md`：模型选择——执行 subagent 与阶段 3 review / fix 的档位判据。
- `references/platform-agents.md`：Claude Code / Codex 的 subagent、权限、模型与工作目录映射。
- `scripts/workspace.sh`：交接目录 `.execute-task/` 的单一事实来源（建目录 + 自忽略 `.gitignore`，打印路径），其余脚本经它取目录。
- `scripts/task-brief.sh`：从 tasks 文档机械抽取单个任务全文生成简报基底，防手抄失真；design/spec 片段与约定的 seam 由主 agent 追加。
- `scripts/task-baseline.sh`：每任务开工前确认真实工作区干净并记录 HEAD，供闸门一核对 HEAD 未漂移。
- `scripts/acceptance-diff.sh`：拒绝 dirty 工作区后生成阶段 3 整体验收审查包（BASE..HEAD 的 commit 清单 + 变更统计 + 完整 diff）。
