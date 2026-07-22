# 验收与收尾 — 双验收门、五轴 review、覆盖回扫、守层、收尾

> 用途：`execute-task` 招牌机制「双验收闸门」+ 阶段 3/4 的操作细则。
>
> **两道门**：每任务验收门（闸门一，阶段 2 内）+ 整体验收门（闸门二，阶段 3）。

## 一 · 每任务验收门（闸门一）

- 对齐 split-task 给的「验收标准 + 验证方式」，逐条核——**全绿才算完成**。
- 审查由主 agent 派发的**独立 review subagent** 执行，结论按 Critical / Important / Minor 分级；
  有 Critical / Important 则派**独立 fix subagent** 修复 → 复审——不自审自修。
- **Critical / Important 清零才过闸门**，Minor 记录不阻塞；修复超轮次上限（默认 3 轮）仍不过 → 停下交用户判断。
- **不过不 commit、不标 `[x]`**：验收不绿（含复审未过）的任务不许进账本。通过后先标 `[x]`，与已审代码 / 测试一起提交；提交成功后才写 ignored ledger。
- 这是任务级"做完没做完"的客观判据，不靠"看起来写好了"。

## 二 · 整体五轴 review（闸门二）

**输入准备**：先检查本次开发 diff 中的临时日志、调试打印、断点和临时开关；有残留就精准清理、
跑覆盖测试，并在阶段 0 授权范围内提交。确认真实工作区干净后，再运行本 skill 目录下的
`scripts/acceptance-diff.sh <起点commit>`（起点 = 阶段 1
记入账本的起点 commit）——脚本先拒绝任何非忽略 dirty 状态、确认 BASE 是 HEAD 的祖先，再生成整体审查包
（commit 清单 + 变更统计 + BASE..HEAD 完整 binary diff，-U10）
并打印路径，派发时传包路径（照抄 handoff-templates.md 第四节模板），不让 review subagent 自己爬库推导改动。

全部任务完成后，主 agent **派独立 review subagent** 对整条分支做五轴审查（吸收 agent-skills code-review-and-quality）；
**这次派发固定用 most-capable（最强档）模型，不沿用 session 默认**——它是全链路唯一的架构级判断点，
判据见 [model-selection.md](model-selection.md)。审出的 Critical / Important **派独立 fix subagent** 修复 → 复审（同样按轮次计，超限交用户），Minor 记录不阻塞：

- **correctness（正确）**：行为对不对，边界 / 错误路径处理了吗，验收标准真满足吗。
- **readability（可读）**：命名 / 结构清晰吗，后人能看懂吗。
- **architecture（架构）**：模块边界 / 职责合理吗，有没有该抽的重复、该隔的耦合。
- **security（安全）**：输入校验、权限、敏感数据、注入面有没有问题。
- **performance（性能）**：有没有明显热点 / N+1 / 不必要开销（按项目实际规模判断，别过早优化）。

**阶段 3 的 fix 循环（commit-then-review）**：审出的 Critical / Important 派独立 fix subagent 修复后，
主 agent **先 commit 再复审**——重跑 `scripts/acceptance-diff.sh <起点>`（轮次递增，HEAD 已前进，
新包已含 fix），复审读一个新包。与任务级"不过不 commit"**有意不同**：任务级的 commit 是闸门记号；
阶段 3 面对的本来就是已 commit 的分支，闸门记号是"整体验收通过"状态本身，fix commit 只是普通代码演进。
这些 fix commit 也必须落在阶段 0 的明确批次授权内；超出授权范围就重新确认。

## 三 · 覆盖核对回扫

对回上游，确认没落空（这是这条链"可验证"基因在执行末端的收口）：

- 对回 split-task 的**覆盖核对表**：design 每个组件 / Decision、spec 每条 Requirement / MUST NOT →
  都**已实现**、且**被测试或检查覆盖**了吗？
- 对回 spec 的**成功标准**：每条都能跑通验证了吗？
- 有落空（某设计点没实现 / 没测试）→ 回阶段 2 补任务，别让它溜过整体验收。

## 四 · 上游纠错守层

执行中发现 design / spec / tasks 有误，分级处理：

- **小问题**（笔误、明显小遗漏、不动结构）→ 就地修正 + 回写 artifact + 告知用户，继续。
- **重大问题**（技术决策错、需求缺、任务依赖不存在的设计）→ 停下退回 make-design / split-task，不在执行里硬改。
- 检验：「这修正会改变已 review 的行为契约 / 技术决策 / 任务边界吗？」会 → 重大，退回上游。

## 五 · 收尾（调用 finish-branch）

- **整体验收通过后，调用 `finish-branch` 做收尾**：它会先清理本次开发的调试残留并重跑最终测试，再检测
  repo/worktree 状态，给出合并到主干 / 本地保留 / 创建 PR / 丢弃选项。
- **危险操作 gate**：commit 必须已有阶段 0 明确授权；合并 / PR / push / 丢弃 / 移除 worktree **不自动做**，
  由 finish-branch 对具体动作逐项取得用户确认（遵循当前 `CLAUDE.md` / `AGENTS.md` 与平台审批策略）。
- execute-task 到"整体验收通过 + 收尾决策交付"为止，不擅自合并、不自动往下。

## 收尾自检

- 每任务都过了验收门（独立 review subagent 审查、独立 fix subagent 修复）才 commit / 标 `[x]`？
- 整体过了五轴 review（独立 review subagent，且**固定用了 most-capable 档位**）？审出的问题派独立 fix subagent 修了？
- 整体 review 拿到的是 `acceptance-diff.sh` 生成的审查包（而非让它自己爬库）？fix 后复审用的是 commit 过再重新生成的新包？
- 生成整体包前确认了工作区无非忽略改动、BASE 是 HEAD 祖先？阶段 3 fix commit 仍在用户授权内？
- 整体验收包生成前清掉了本次开发的调试残留，并在清理改动后重新跑了覆盖测试？
- 覆盖核对回扫——design / spec 每条都实现且被测试覆盖、不落空？
- 全套测试 / 构建 / typecheck 绿？
- 发现上游错误按"小修就地 / 重大退回"处理了？
- 收尾交用户拍板，没擅自合并 / PR / push？
