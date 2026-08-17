# execute-task 任务内改为纯 TDD 闭环设计文档

日期：2026-08-17

## 背景

原闭环里每个任务要派三个 subagent：执行（TDD → 验证）→ review（对照验收标准审）→ fix（带发现修复）→ 复审，
最多 3 轮。它把"任务做完没做完"押在一个**主观判断**上：reviewer 说 Critical / Important 清零才算过。
代价有三处：

1. **成本与轮次**：每个任务至少 2 次派发，审出问题就 4~6 次；一份 10 任务的清单光审查开销就成倍于实现本身。
2. **判据是主观的**：同一份 diff 换个 reviewer 结论可能不同，"过闸门"没法机械复核；
   而 TDD 本身自带客观判据（先红后绿），原设计等于在有判据的机制外面又套了一层没判据的确认。
3. **审查位置错**：任务级 reviewer 只看单任务 diff，看不出跨任务的架构问题；真正需要架构判断的地方是
   阶段 3 whole-branch review，那里本来就有五轴 + 覆盖回扫。

参考 `mattpocock/skills`（`skills/engineering/implement` + `skills/engineering/tdd`）的分工：
implement 只做"用 TDD 在事先约定的 seam 上实现 + 定期 typecheck / 单测 / 末尾全套"，
审查是**实现之后一次独立的 code-review**，不是每一小步都插一轮。

## 决策

**任务内只保留 TDD，取消任务级 review 轮与 fix 轮**；审查与修复集中到阶段 3 整体验收做一次。

1. **闸门一从"审查门"改为"证据门"**——主 agent 只核三样可机械判定的事：
   - 执行报告里每个行为的**红 → 绿证据**齐（红的命令与失败输出 + 为何预期失败、绿的命令与通过输出）；
   - 主 agent **自己复跑一次**任务的「验证方式」+ typecheck，看退出状态与输出噪音；
   - `git rev-parse HEAD` 仍等于 `task-baseline.sh` 记录的基线，改动落在任务涉及文件内。
   三样齐 + 验收标准逐条对上才 commit。只有绿没有红 → 退回同一执行 subagent 补齐；补不出就记录并告知用户，
   不默认它做了 TDD，也不由主 agent 补一段事后测试充当证据。
2. **TDD 内容加厚**（吸收 mattpocock 的 `tdd` skill，因为它现在是任务内唯一的质量机制）：
   - **seam 事先约定**：阶段 1 列 seam 清单；design / tasks 没指明的 seam 先与用户确认再写进简报，
     未确认的 seam 不派发。原来测错地方由 reviewer 兜，现在必须前置。
   - **好测试判据**：验行为不验实现、读起来像规格、期望值来自独立事实来源、能活过重构、一个逻辑断言。
   - **三个反模式**：实现耦合（mock 内部协作者 / 侧信道验证）、同义反复（期望值按代码算法重算）、
     水平切片（先写完所有测试）——写进执行派发模板与反例清单，让执行方自己认得出来。
   - **循环规则**：红先于绿且确认红的原因是行为缺失、一次一片、**重构不进循环**
     （结构问题写进报告「疑虑」→ 记账本 → 交阶段 3 architecture 轴）、mock 只在系统边界。
3. **阶段 3 相应加强**：五轴之外补一条**测试质量**审查（验的是真行为还是实现细节、有没有同义反复），
   派发时把各任务记下的结构疑虑一并交给 reviewer——任务内没人审过测试，这里是唯一关口。
   阶段 3 的 review / fix 轮、轮次上限（默认 3 轮）、commit-then-review 机制均保持不变。
4. **模型档位**：执行 subagent 默认从 cheap 上调为 **standard 兜底**（它同时写测试和实现且没人复核），
   cheap 只留给"简报里已给完整代码的单文件转录类"任务。理由写进 model-selection：
   档位选低的代价不再是"多修一轮"，而是"缺陷带着一堆绿测试进 commit"，要到阶段 3 才被发现。
5. **删 `scripts/review-diff.sh`**：它唯一的消费者是任务级 reviewer，随该轮一起移除。
   `task-baseline.sh` 保留——干净基线仍保证原子提交只含本任务改动，记录的 HEAD 改由闸门一核对漂移。

## 保留没动的部分

阶段 0 提交授权闸门、依赖 / wave 调度与并行四条件、worktree 隔离、checkbox + ledger 与 safe-resume、
上游纠错守层、阶段 3 覆盖核对回扫、阶段 4 交 finish-branch 收尾、危险操作用户拍板——全部不变。

## 改动文件

- `SKILL.md`：四件事第 2 条、招牌机制核心一、闸门一 / 二、阶段 1 seam 清单、阶段 2 步骤、阶段 3、
  核心原则、终止条件、自检清单、示范（T2 改成逐行为红 → 绿 + 主 agent 核证据）、反例、相关参考。
- `references/execution-loop.md`：整体重写为 seam / 好测试 / 三反模式 / 循环规则 / 小步 / 验证节奏 /
  闸门一证据核对 / atomic commit / bug 诊断。
- `references/handoff-templates.md`：删任务级 review 模板；执行模板补 seam 段与红 → 绿工作步骤、
  报告要求红证据；fix 模板改挂阶段 3；自查同步。
- `references/orchestration.md`：第四节改为"每任务只派执行 subagent"，回执四态处理改挂闸门一，
  补"证据不齐怎么办"，ledger 兼记结构疑虑。
- `references/acceptance.md`：闸门一改证据门；闸门二补测试质量轴与疑虑输入；自检同步。
- `references/model-selection.md`：表改为执行 / 阶段 3 review / 阶段 3 fix 三行，cheap 适用面收窄。
- `references/platform-agents.md`：角色分离改挂阶段 3；降级路径改为"TDD → 验证 → 证据核对 → commit"。
- `scripts/review-diff.sh`：删除。`workspace.sh` / `task-baseline.sh`：头部注释同步。
- `README.md`、`metadata.yaml`（`description` + `updated_at`）。

## 发布

skill 行为机制变更，随插件发布：`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、
`.codex-plugin/plugin.json` 同步递增到 0.19.0。
