# handoff 模板 — 执行 subagent 与阶段 3 整体验收的派发 prompt

> 用途：`execute-task` 派发 subagent 时照抄填空（占位符 `[...]`）。
> 机制与状态协议见 [orchestration.md](orchestration.md) 第四节，此处只给可直接套用的模板。
> **阶段 2 每个任务只派一类 subagent（执行）**；review / fix 模板只用于阶段 3 整体验收。
> subagent 不可用的降级场景不用模板——主 agent 顺序执行同一套闭环纪律。
> **模型档位不是 prompt 正文的一部分**：派发前先按 [model-selection.md](model-selection.md) 定档（cheap / standard / most-capable），
> 用平台的模型参数（如 Agent 工具的 `model`）指定，不要写进下面的模板文本里、也不要留空。
> 派发机制、权限继承和并行工作目录按 [platform-agents.md](platform-agents.md) 执行；Codex 并行写任务必须把各自 worktree 绝对路径写入 `[目录]`，不能让多个 agent 共用同一 checkout。

## 〇 · 派发前主 agent 先备好交接文件

1. 临时工作目录 `.execute-task/`（仓库根下，含自忽略 `.gitignore`，不提交）由各脚本经
   `scripts/workspace.sh` 自动创建，不必手建。
2. **任务简报** `[BRIEF_FILE]`：运行本 skill 目录下的 `scripts/task-brief.sh <tasks文件> <任务编号>`——
   它机械抽取该任务全文（验收标准、验证方式、涉及文件，精确值逐字保真）写入
   `.execute-task/task-N-brief.md` 并打印路径，任务号不存在会报错；**不要手抄任务正文**。
   然后主 agent 把相关 design/spec 片段**追加**到同一文件（这半截需要判断力，脚本管不了）。
3. **约定的 seam**：从 design / tasks 取本任务的可测接缝；没指明就先与用户确认，再把它追加进简报——
   执行 subagent 只在这个 seam 上写测试（理由见 [execution-loop.md](execution-loop.md) 第一节）。
4. **执行报告**路径约定为 `[REPORT_FILE]` = `.execute-task/task-N-report.md`（执行 subagent 写，闸门一读它核证据）。
5. **任务基线**（主 agent 自留，不进派发 prompt）：在派执行 subagent 前运行本 skill 目录下的
   `scripts/task-baseline.sh <任务编号>`。它要求真实工作区没有暂存、未暂存或未跟踪改动，并记录当前 HEAD；
   失败就先处理现有改动，**不要覆盖基线或带脏开工**。提交前拿它核对 HEAD 未漂移。

## 一 · 执行 subagent 派发模板（阶段 2 唯一派发）

```text
你来实现任务 N：[任务名]

## 任务要求

先读你的任务简报：[BRIEF_FILE]
它是需求的唯一来源——其中的精确值（数字、签名、测试用例）逐字照用。

## 上下文

[一行：该任务在整个项目中的位置]
[前序任务已定的接口 / 决策——简报无法知道的，没有则删]

## 测在哪（已约定的 seam）

[SEAM]：本任务的测试只写在这个公共边界上，不伸进内部实现。
认为它不对、或需要新增 seam → 停下来问，不要自己换地方测。

## 开工前

对需求、验收标准、实现途径、依赖有任何疑问——**现在就问**，别猜、别默默假设。

## 你的工作：红 → 绿，一次一片

1. 写**一个**失败测试：验行为、走公共接口、期望值用独立字面量或 spec 里的精确值
   （不要用被测代码的同一套算法把期望值重算一遍）。
2. 跑它 → **确认红的原因是行为缺失**，不是语法 / import / 环境错；是后者就先修掉再重跑。
3. 写**刚好让它过**的最小实现 → 跑 → 绿。不提前实现下一个测试要的东西、不加投机功能。
4. 回到 1 做下一个行为，直到验收标准逐条被覆盖。bug 任务的第一个测试就是复现测试。
5. mock 只在系统边界（外部 API、时间 / 随机）；不 mock 自己的模块和内部协作者。
6. 让测试转绿的那一步**不夹带重构**；看到结构问题写进报告「疑虑」，不顺手改。
7. 按任务的「验证方式」验证：[验证命令，如 `pytest tests/test_x.py`]，加 typecheck（若项目有）。
8. 每一步保持系统可构建、可测；**不要 commit**——commit 由主 agent 过闸门后执行。

工作目录：[目录]
途中遇到意外或不清楚的地方，随时停下来问。

## 卡住了怎么办

说"这超出我的能力"永远是允许的——坏活比没活更糟，升级不会被追责。
需要架构决策、看不懂现有代码又找不到答案、不确定方向对不对 →
回执 BLOCKED 或 NEEDS_CONTEXT，写清卡在哪、试过什么、需要什么帮助。

## 回执格式

把详细报告写进 [REPORT_FILE]：
- 实现了什么（被阻塞时：尝试了什么）
- **每个行为的红 → 绿证据**：红的测试命令与失败输出 + 为何预期失败；绿的命令与通过输出。
  这是任务验收门的判据——只有绿、没有红，算证据不齐。
- 改动了哪些文件
- 问题与疑虑（含看到但按规则没动的结构问题）

然后**只回执**（十行内，细节都在报告文件里）：
- 状态：DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- 一行测试摘要（如 "14/14 通过，输出干净"）
- 疑虑（若有）
- 报告文件路径

BLOCKED / NEEDS_CONTEXT 时把具体缺什么直接写在回执里，主 agent 要据此行动。
做完但对正确性没把握 → 用 DONE_WITH_CONCERNS，绝不悄悄交付没把握的活。
```

## 二 · 整体验收 review 派发模板（阶段 3）

先跑本 skill 目录下的 `scripts/acceptance-diff.sh <起点commit>`（起点 = 阶段 1 记入账本的起点 commit）生成整体审查包，
拿打印路径填 `[PACKAGE_FILE]`。五轴定义与覆盖回扫住在 acceptance.md，此处不重复。
脚本若报告工作区 dirty 或 BASE 不是 HEAD 祖先，先处理并重新运行，不能让 reviewer 审一个漏掉未提交改动的包。

```text
你来做整体验收 review：全部任务已完成，对整条开发线做五轴审查。
这是全链路唯一的架构级判断点——任务级没有独立审查轮，问题要在这里被看见。

## 审查范围

整体审查包：[PACKAGE_FILE]（commit 清单 + 变更统计 + BASE..HEAD 完整 diff，-U10 上下文）
读一次即可——上下文行就是改动后的文件。只有为核实一个能点名的具体风险才看包外代码，
并在回执里写明查了什么。你只读不改：不动工作区、不动 git 状态。

## 审什么

按 acceptance.md「整体五轴 review」：correctness / readability / architecture / security / performance。
另外核测试本身：验的是真行为还是实现细节 / mock，期望值有没有按代码算法重算（同义反复）。
参考输入：tasks 文件 [TASKS_FILE]、design/spec [DESIGN_SPEC_PATHS]、
执行期记下的结构疑虑 [CONCERNS：来自各任务执行报告；没有则删]。

## 回执格式

每条 finding 带 file:line，按严重度分级：
- Critical：行为错 / 违反验收标准
- Important：不修不能信任——坏味道、回归风险、spec 之外的多余改动
- Minor：雕琢项（记录不阻塞）
先说做得好的（要具体），再列问题，最后按五轴各给一句判定。
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

把修复报告**追加**到 [REPORT_FILE]：
- 每条发现怎么修的
- 复验的测试命令与输出（涉及行为的附红 → 绿证据）

然后只回执：修了什么（每条一行）+ 一行测试摘要 + 报告路径。
修不了、或发现问题出在需求 / 设计层面 → 回执 BLOCKED 并说明，别硬改绕过。
```

> 主 agent 收到 fix 回执后**先 commit 再复审**——重跑本 skill 目录下的
> `scripts/acceptance-diff.sh <起点>` 生成新一轮包（机制与理由见 acceptance.md），
> 复审读新包。fix commit 同样必须落在阶段 0 的授权批次内。

## 四 · 派发前主 agent 自查

- 简报 / 报告走的是**路径**？prompt 里没粘正文、没粘前序任务的累积摘要？
- 简报是 `task-brief.sh` 生成的基底 + 追加片段（design/spec + 约定的 seam）？没有手抄任务正文？
- 派执行前 `task-baseline.sh` 确认了真实工作区干净并记录了 HEAD？
- 执行模板里填了 `[SEAM]`？该 seam 来自 design / tasks，或已与用户确认？
- 用平台的模型参数**显式指定了本次派发的档位**（cheap/standard/most-capable），没有留空？
- 收到 DONE 回执后按闸门一核了三样（红 → 绿证据齐、自己复跑验证命令绿、HEAD 未漂移）才 commit？
- 阶段 3 派发传了 `acceptance-diff.sh` 生成的整体包路径？fix 后是 commit 过再重新生成的新包？
