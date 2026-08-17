# 任务工作文件与阶段 3 派发模板

> 用途：`execute-task` 阶段 2 的每任务工作文件规范，以及阶段 3 派发 subagent 时照抄填空的 prompt
> （占位符 `[...]`）。机制见 [orchestration.md](orchestration.md) 第四节。
>
> **阶段 2 不派任何 subagent**——主 agent 自己加载 `tdd` 走闭环，第一节给的是它开工前要备好的文件；
> 派发模板（第二、三节）只用于阶段 3 整体验收。
> **模型档位不是 prompt 正文的一部分**：阶段 3 派发前先按 [model-selection.md](model-selection.md) 定档，
> 用平台的模型参数（如 Agent 工具的 `model`）指定，不要写进模板文本里、也不要留空。
> 派发机制、权限继承和工作目录按 [platform-agents.md](platform-agents.md) 执行。

## 一 · 每任务的工作文件（阶段 2）

临时工作目录 `.execute-task/`（仓库根下，含自忽略 `.gitignore`，不提交）由各脚本经
`scripts/workspace.sh` 自动创建，不必手建。

1. **任务基线**：开工前运行本 skill 目录下的 `scripts/task-baseline.sh <任务编号>`。
   它要求真实工作区没有暂存、未暂存或未跟踪改动，并记录当前 HEAD；
   失败就先处理现有改动，**不要覆盖基线或带脏开工**。提交前拿它核对 HEAD 未漂移。
2. **任务简报** `.execute-task/task-N-brief.md`：运行 `scripts/task-brief.sh <tasks文件> <任务编号>`——
   它机械抽取该任务全文（验收标准、验证方式、涉及文件，精确值逐字保真）并打印路径，
   任务号不存在会报错；**不要手抄任务正文**。然后把相关 design/spec 片段和**约定的 seam**
   （从 design / tasks 取；没指明就先与用户确认）**追加**到同一文件——这半截需要判断力，脚本管不了。
   它是需求的**唯一来源**，也是交给 `tdd` 的主要输入。
3. **执行记录** `.execute-task/task-N-record.md`：由 `tdd` 维护，不在这里定义格式。
   调用 tdd 时传名称 `task-N` 与输出目录 `.execute-task/`，它会用自己的
   `scripts/tdd-record.sh` 建好文件并边做边追加。闸门一读它核证据，阶段 3 的整体 review 拿它当输入。

**调用 tdd 时传给它**（照它的调用契约）：简报路径、**约定的 seam**、任务的验证方式（加 typecheck）、
记录名称与输出目录。**取回**：证据齐否、改动文件、疑虑、记录路径（或 BLOCKED）。

## 二 · 整体验收 review 派发模板（阶段 3）

派发前确认工作区无非忽略改动（否则 reviewer 的 `review-package.sh` 会拒绝生成包）。
六关判据与回执格式住在 `review-changes`，此处不重复。

```text
你来做整体验收 review：全部任务已完成，对整条开发线做独立审查。
这是全链路唯一的架构级判断点——任务级没有独立审查轮，问题要在这里被看见。

## 怎么做

加载并按 `review-changes` skill 执行。BASE 起点 commit：[BASE_COMMIT]
（用它自己的 scripts/review-package.sh 生成审查包，输出目录传 .execute-task/）。

## 参考输入

- tasks 文件：[TASKS_FILE]
- design / spec：[DESIGN_SPEC_PATHS]
- 执行期疑虑（architecture 关优先看这些点）：[CONCERNS：来自 ledger 与各任务
  `.execute-task/task-*-record.md`；没有则删]

## 边界

你只读不改：不动工作区、不动 git 状态、不修问题。
回执按 review-changes 的回执格式：做得好的（要具体）+ 分级 findings（带 file:line）+ 六关各一句判定。
```

## 三 · fix subagent 派发模板（阶段 3 整体验收发现）

```text
你来修复整体验收 review 发现的问题。

## 待修问题（Critical / Important 发现）

[逐条列：file:line、什么问题、为什么要紧、修法（若 review 给了）]

## 边界

需求依据：[DESIGN_SPEC_PATHS] + tasks 文件 [TASKS_FILE]。
修复范围限于**本次开发范围**内的上述发现，不许顺手改无关代码、不许改行为契约。

## 你的工作

1. 逐条修复上述发现；涉及行为的修复**先补 / 改一个失败测试再修到绿**。
2. **复跑覆盖你改动的测试**：[点名覆盖测试文件 / 命令]（一行小修不必全套）。
3. **不要 commit**。

## 回执格式

把修复报告写进 [FIX_REPORT_FILE]（约定为 `.execute-task/acceptance-fix-<轮次>.md`）：
- 每条发现怎么修的
- 复验的测试命令与输出（涉及行为的附红 → 绿证据）

然后只回执：修了什么（每条一行）+ 一行测试摘要 + 报告路径。
修不了、或发现问题出在需求 / 设计层面 → 回执 BLOCKED 并说明，别硬改绕过。
```

> 主 agent 收到 fix 回执后**先 commit 再复审**——复审的 reviewer 重新生成一份新包
> （机制与理由见 [acceptance.md](acceptance.md)），读新包而不是旧包。
> fix commit 同样必须落在阶段 0 的授权批次内。

## 四 · 自查

**阶段 2（每任务，自己做）**

- 开工前 `task-baseline.sh` 确认了真实工作区干净并记录了 HEAD？
- 简报是 `task-brief.sh` 生成的基底 + 追加片段（design/spec + 约定的 seam）？没有手抄任务正文？
  seam 来自 design / tasks，或已与用户确认？
- 调用 tdd 时把简报路径、seam、验证方式、记录名称与输出目录都传齐了？
- 任务内**一个 subagent 都没派**？
- 按闸门一核了三样（红 → 绿证据齐、收尾完整跑一次验证命令绿、HEAD 未漂移）才 commit？

**阶段 3（派发前）**

- 用平台的模型参数**显式指定了本次派发的档位**（整体验收固定 most-capable），没有留空？
- 派发 prompt 里写清了**加载 review-changes 执行**，并给了 BASE 与输出目录？
- 把 ledger / 执行记录里的结构疑虑一并交给了 reviewer？
- 工作区在派发前是干净的？fix 后复审用的是 commit 过再重新生成的新包？
