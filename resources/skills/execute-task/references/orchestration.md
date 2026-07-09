# 调度与编排 — 排序、并行、subagent 派发与 handoff、进度账本

> 用途：`execute-task` 招牌机制「核心二 + 调度」的操作细则。阶段 1 调度、阶段 2 派发执行时用。
>
> **目标**：把任务清单按依赖排成可执行序列，能并行的并行、能恢复的恢复，主 agent 做编排而非糊代码。

## 一 · 读 tasks 排执行顺序

- 读 split-task 的「依赖与并行视图」，按 depends_on 做**拓扑排序**。
- **依赖无环**：出现环说明上游 tasks 有问题 → 退回 split-task，别硬排。
- 高风险 / 高不确定性任务**前置**（split-task 已标），早暴露问题。
- 输出一个**执行计划**并打印：顺序、哪些并行、checkpoint 在哪——让过程可见。

## 二 · wave 并行

- **同一 wave** = 彼此无依赖、且**不改同一批文件**的任务，可并行执行。
- **wave 间串行**：前一波全部完成、合并 / 稳定后，再开下一波——避免半成品互相踩。
- 判据：并行任务的 `涉及文件`（split-task 已列）不能交叠，否则改回串行或合并。
- 并行是**可选优化**：任务少 / 强依赖链时直接线性执行，别为并行而并行。

## 三 · worktree 隔离（可选，调用 setup-worktree）

- 需要隔离工作区时（并行任务各自隔离、或整次开发隔离），**调用 `setup-worktree`**——它负责检测是否已在
  worktree、优先平台原生工具、fallback `git worktree`。
- **何时需要**：多个任务并行且可能改同一区域代码时——每个并行任务一个 worktree，完成后各自 atomic commit，再按 wave 合并回来。
- **可选**：单任务串行、或并行任务文件不交叠时**不需要**——别为隔离而隔离。
- worktree 的清理 / 合并交收尾的 **finish-branch**。

## 四 · subagent 派发与 handoff

- **每任务三类独立 subagent**：执行 / 审查 / 修复各派一个 fresh subagent，全新上下文，只带各自需要的信息；
  **主 agent 做编排**：派执行 → 派 review →（不过则派 fix → 复审）→ 过闸门 → commit → 记账本 → 下一个；
  不自己埋头糊代码、也不亲手审查 / 修复。三类派发 prompt 照抄 [handoff-templates.md](handoff-templates.md)。
- **文件 handoff，不粘正文**：大块产物写成文件、派发只传路径——粘进派发 prompt 的内容会常驻主 agent
  上下文，每轮都被重读。每任务三份交接文件（放仓库根下临时目录如 `.execute-task/`，内放一个只含 `*` 的
  `.gitignore` 自忽略，不提交；放工作树内是因为 subagent 通常写不了 `.git/` 下）：
  - **任务简报** `task-N-brief.md`：运行本 skill 目录下的 `scripts/task-brief.sh <tasks文件> <任务编号>`
    机械抽取该任务全文（**不要手抄**，精确值逐字保真），再由主 agent 追加相关 design/spec 片段。
    它是需求的**唯一来源**——精确值（数字、签名、测试用例）只出现在这里，不重复粘进 prompt；
  - **执行报告** `task-N-report.md`：执行 subagent 写详细报告——实现了什么、测试命令与输出（TDD 红→绿证据）、
    改动文件、遇到的问题；后续 fix 的修复报告**追加到同一文件**，复审读的就是它；
  - **diff 文件**：主 agent 运行本 skill 目录下的 `scripts/review-diff.sh <任务编号>` 生成交给 review
    （执行 subagent 不 commit，工作区 diff 即该任务改动；脚本以 -U10 扩展上下文、自动按轮次命名并打印写入路径，不必人工记编号；
    fix 后复审时**重新运行**生成新一轮 diff，别复用旧文件）。
- **派发 prompt 只描述这一个任务**：一行任务定位（在整个项目里的位置）+ 简报路径（"先读它，它是你的需求"）+
  前序任务已定的接口 / 决策（简报无法知道的）+ 报告文件路径与回执契约。**不要**把前面任务的累积摘要粘进后面任务的派发。
- **执行回执 = 状态 + 短摘要**（细节都在报告文件里，回执控制在十行内）：
  状态 + commit 无（不 commit）+ 一行测试摘要 + 疑虑 + 报告路径。四种状态、各有处理：
  - `DONE` → 生成 diff 文件、派 review；
  - `DONE_WITH_CONCERNS` → 先读疑虑：涉及正确性 / 范围的先处理再审；纯观察项（如"这文件越来越大"）记下继续；
  - `NEEDS_CONTEXT` → 补上缺的上下文**重派**；
  - `BLOCKED` → 升级阶梯：补上下文重派 → 换更强模型（平台可选时）→ 拆小任务 → 退回上游 / 交用户——
    **不许什么都不变原样重试**，也不许无视升级硬冲。
- **review 输入三件套**：同一份任务简报 + 执行报告 + diff 文件路径，外加绑定该任务的 design/spec 硬约束
  （精确值、格式、组件间关系，逐字抄，不转述）。派发时写明纪律：**执行报告是未经证实的自述，逐条对着 diff 核**；
  review 只读不改；不重跑执行已跑过的测试（报告即测试证据，输出有告警噪音本身算 finding）；
  主 agent 不替 review 预判——派发里出现"这个别报""顶多算 Minor"就是在预判，删掉。
- **fix handoff**：fix subagent 带 review 的 Critical / Important 发现 + 同一份任务简报（Minor 记账本不派）；
  修完**复跑覆盖其改动的测试**（派发里点名覆盖测试，一行小修不必全套）、把修复报告（含测试命令与输出）
  追加进执行报告、回执短摘要。主 agent **确认报告里有测试证据**（覆盖测试 + 命令 + 输出三样齐）后，
  生成新 diff 派复审——复审读更新后的报告 + 新 diff。
- **平台**：在 Claude Code 里用 Task / Agent 工具派发 subagent。**subagent 不可用的环境**（无该能力）→
  降级为主 agent **顺序执行**同一套闭环纪律（TDD → 验证 → 审查 → commit），不卡死。
- **模型按角色 / 复杂度定档**：派发前用平台的模型参数（如 Agent 工具的 `model`）显式指定 cheap / standard / most-capable，
  不写等于任其继承主 agent 当前档位（通常最贵）；判据见 [model-selection.md](model-selection.md)。

## 五 · 进度账本与 safe-resume

- **checkbox 回写**：任务过闸门一后，把 tasks.md 对应项改 `- [x]`——状态即进度，无缝衔接 split-task。
- **ledger**：开工时先记**起点 commit**（`git rev-parse HEAD`——阶段 3 生成整体审查包的 BASE）；
  执行中记已完成任务 + 对应 commit（便于追溯）。
- **safe-resume**：重跑先读 checkbox + ledger，**已完成的跳过**，只接着做未完成的——防上下文压缩后从头重跑、重复执行。
- 不引入 GSD 全套 STATE / ROADMAP——checkbox + 轻 ledger 足够，别把进度跟踪做成负担。

## 收尾自检

- 执行顺序是按依赖拓扑排的、无环？
- 并行任务确实不冲突文件？wave 间是串行的？
- 每任务的执行 / 审查 / 修复各派了独立 fresh subagent（或降级顺序执行）？主 agent 在编排而非糊代码 / 自审自修？
- handoff 走的是文件（简报 / 报告 / diff 传路径）而非粘贴正文？简报是 `task-brief.sh` 抽取的（没手抄）？
  执行回执带了状态（DONE / BLOCKED…）且按状态处理了？
- fix 报告里有测试证据（覆盖测试 + 命令 + 输出）才派的复审？复审用了**新生成**的 diff？
- 每次派发都**显式指定了模型档位**，没有留空任其继承主 agent？
- 每完成一个就回写了 checkbox + ledger？中断能 safe-resume？
