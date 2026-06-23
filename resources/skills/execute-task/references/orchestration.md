# 调度与编排 — 排序、并行、subagent 派发、进度账本

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

## 四 · subagent 派发

- **每任务一个 fresh subagent**：全新上下文，只带这个任务需要的信息（任务条目 + 相关 design/spec 片段 + 代码位置）。
- **主 agent 做编排**：派发 → 收结果 → 过闸门 → 记账本 → 下一个；不自己埋头糊完所有代码。
- **收什么**：subagent 回报实现了什么、测试是否绿、commit 号；主 agent 据此过「闸门一」。
- **平台**：在 Claude Code 里用 Task / Agent 工具派发 subagent。**subagent 不可用的环境**（无该能力）→
  降级为主 agent **顺序执行**同一套闭环纪律（TDD → 验证 → 审查 → commit），不卡死。

## 五 · 进度账本与 safe-resume

- **checkbox 回写**：任务过闸门一后，把 tasks.md 对应项改 `- [x]`——状态即进度，无缝衔接 split-task。
- **ledger**：记已完成任务 + 对应 commit（便于追溯）。
- **safe-resume**：重跑先读 checkbox + ledger，**已完成的跳过**，只接着做未完成的——防上下文压缩后从头重跑、重复执行。
- 不引入 GSD 全套 STATE / ROADMAP——checkbox + 轻 ledger 足够，别把进度跟踪做成负担。

## 收尾自检

- 执行顺序是按依赖拓扑排的、无环？
- 并行任务确实不冲突文件？wave 间是串行的？
- 每任务派了 fresh subagent（或降级顺序执行）？主 agent 在编排而非糊代码？
- 每完成一个就回写了 checkbox + ledger？中断能 safe-resume？
