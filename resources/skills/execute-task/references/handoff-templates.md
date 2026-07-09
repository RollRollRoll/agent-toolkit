# handoff 模板 — 执行 / 审查 / 修复 subagent 的派发 prompt

> 用途：`execute-task` 阶段 2 派发 subagent 时照抄填空（占位符 `[...]`）。
> 机制与状态协议见 [orchestration.md](orchestration.md) 第四节，此处只给可直接套用的模板。
> subagent 不可用的降级场景不用模板——主 agent 顺序执行同一套闭环纪律。
> **模型档位不是 prompt 正文的一部分**：派发前先按 [model-selection.md](model-selection.md) 定档（cheap / standard / most-capable），
> 用平台的模型参数（如 Agent 工具的 `model`）指定，不要写进下面的模板文本里、也不要留空。

## 〇 · 派发前主 agent 先备好交接文件

1. 临时工作目录 `.execute-task/`（仓库根下，含自忽略 `.gitignore`，不提交）由各脚本经
   `scripts/workspace.sh` 自动创建，不必手建。
2. **任务简报** `[BRIEF_FILE]`：运行本 skill 目录下的 `scripts/task-brief.sh <tasks文件> <任务编号>`——
   它机械抽取该任务全文（验收标准、验证方式、涉及文件，精确值逐字保真）写入
   `.execute-task/task-N-brief.md` 并打印路径，任务号不存在会报错；**不要手抄任务正文**。
   然后主 agent 把相关 design/spec 片段**追加**到同一文件（这半截需要判断力，脚本管不了）。
3. **执行报告**路径约定为 `[REPORT_FILE]` = `.execute-task/task-N-report.md`（执行 subagent 写、fix 追加）。
4. **diff 文件**在派 review 前生成：运行本 skill 目录下的 `scripts/review-diff.sh <任务编号>`——
   它会建好 `.execute-task/`（含自忽略 `.gitignore`）、按轮次自动递增命名（R1/R2/R3…）、跑 `git diff -U10`
   （扩展上下文，review 不必另读改动文件）写入文件，
   并把写入路径打印到 stdout；主 agent 拿这个打印路径填 `[DIFF_FILE]`。
   复审时**重新运行同一命令**生成新一轮文件，不要复用旧 diff；脚本对空 diff 会打印警告，提示确认执行 subagent 是否真的有改动。

## 一 · 执行 subagent 派发模板

```text
你来实现任务 N：[任务名]

## 任务要求

先读你的任务简报：[BRIEF_FILE]
它是需求的唯一来源——其中的精确值（数字、签名、测试用例）逐字照用。

## 上下文

[一行：该任务在整个项目中的位置]
[前序任务已定的接口 / 决策——简报无法知道的，没有则删]

## 开工前

对需求、验收标准、实现途径、依赖有任何疑问——**现在就问**，别猜、别默默假设。

## 你的工作

1. 在 seam 上 TDD（tracer bullet：一个行为测试 → 最小实现 → 下一个行为）；bug 任务先写复现测试。
2. 小步推进，每步保持可构建、可测。
3. 按任务的「验证方式」验证：[验证命令，如 `pytest tests/test_x.py`]，加 typecheck（若项目有）。
4. **不要 commit、不要自审**——到验证为止，commit 由主 agent 过闸门后执行。

工作目录：[目录]
途中遇到意外或不清楚的地方，随时停下来问。

## 卡住了怎么办

说"这超出我的能力"永远是允许的——坏活比没活更糟，升级不会被追责。
需要架构决策、看不懂现有代码又找不到答案、不确定方向对不对 →
回执 BLOCKED 或 NEEDS_CONTEXT，写清卡在哪、试过什么、需要什么帮助。

## 回执格式

把详细报告写进 [REPORT_FILE]：
- 实现了什么（被阻塞时：尝试了什么）
- 测试命令与输出——TDD 证据：红（实现前的失败输出、为何预期失败）、绿（实现后的通过输出）
- 改动了哪些文件
- 问题与疑虑

然后**只回执**（十行内，细节都在报告文件里）：
- 状态：DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- 一行测试摘要（如 "14/14 通过，输出干净"）
- 疑虑（若有）
- 报告文件路径

BLOCKED / NEEDS_CONTEXT 时把具体缺什么直接写在回执里，主 agent 要据此行动。
做完但对正确性没把握 → 用 DONE_WITH_CONCERNS，绝不悄悄交付没把握的活。
```

## 二 · review subagent 派发模板

```text
你来审查任务 N 的实现：先核是否符合需求，再看做得好不好。
这是任务级闸门，不是合并评审——整体 whole-branch review 在全部任务完成后另做。

## 需求是什么

读任务简报：[BRIEF_FILE]

绑定本任务的 design/spec 硬约束（逐字抄，不转述）：
[GLOBAL_CONSTRAINTS：精确值、格式、组件间关系；没有则删]

## 执行方声称做了什么

读执行报告：[REPORT_FILE]
**报告是未经证实的自述**——可能不完整、不准确或过于乐观，逐条对着 diff 核对。
报告里的设计辩解（"按 YAGNI 省了""刻意保持简单"）也是自述，不因辩解降级 finding。

## 待审 diff

diff 文件：[DIFF_FILE]（工作区未提交改动，含带上下文的完整 diff）
读一次即可——diff 的上下文行就是改动后的文件，别再单独读改动文件、别爬代码库。
只有为核实一个**能点名的具体风险**才看 diff 外的代码（如改了函数契约就查调用点），
并在回执里写明查了什么。你只读不改：不动工作区、不动 git 状态。

## 测试

执行方已跑过测试并在报告里给了证据，**别重跑**去确认。
只有读代码产生了具体疑问、且现有运行回答不了时，才跑一个聚焦的测试。
报告的测试输出里有告警 / 噪音，本身就是 finding。

## 审什么

1. **验收对照**：对照简报逐条核——
   缺了什么（漏做 / 声称做了没做）、多了什么（没要求的功能、过度设计）、做歪了什么（做了但理解错）。
   单凭 diff 核不了的（在未改动代码里 / 跨任务）→ 标 ⚠️ 交主 agent 核，别自己扩大搜索。
2. **质量**：坏味道、回归风险、错误处理、测试验的是真行为还是 mock、边界是否覆盖。

## 回执格式

回执直接从判定开始，不要过程叙述。每条 finding 带 file:line，按严重度分级：
- Critical：行为错 / 违反验收标准
- Important：不修不能信任——坏味道、回归风险、spec 之外的多余改动
- Minor：雕琢项（记录不阻塞）

先说做得好的（要具体），再列问题。最后给两个判定，各一句理由：
- 验收对照：✅ / ❌（+ ⚠️ 待核列表）
- 质量：通过 / 需修
```

## 三 · fix subagent 派发模板

```text
你来修复任务 N 审查发现的问题。

## 待修问题（review 的 Critical / Important 发现）

[逐条列：file:line、什么问题、为什么要紧、修法（若 review 给了）]

## 任务要求

读任务简报：[BRIEF_FILE]——修复不许越出任务边界，不许顺手改无关代码。

## 你的工作

1. 逐条修复上述发现。
2. **复跑覆盖你改动的测试**：[点名覆盖测试文件 / 命令]（一行小修不必全套）。
3. **不要 commit**。

## 回执格式

把修复报告**追加**到 [REPORT_FILE]（保留原报告）：
- 每条发现怎么修的
- 复验的测试命令与输出

然后只回执：修了什么（每条一行）+ 一行测试摘要 + 报告路径。
修不了、或发现问题出在需求 / 设计层面 → 回执 BLOCKED 并说明，别硬改绕过。
```

## 四 · 整体验收 review 派发模板（阶段 3）

先跑 `scripts/acceptance-diff.sh <起点commit>`（起点 = 阶段 1 记入账本的起点 commit）生成整体审查包，
拿打印路径填 `[PACKAGE_FILE]`。五轴定义与覆盖回扫住在 acceptance.md，此处不重复。

```text
你来做整体验收 review：全部任务已完成，对整条开发线做五轴审查。
这次派发用最强档模型（见 model-selection.md），是全链路唯一的架构级判断点。

## 审查范围

整体审查包：[PACKAGE_FILE]（commit 清单 + 变更统计 + BASE..HEAD 完整 diff，-U10 上下文）
读一次即可——上下文行就是改动后的文件。只有为核实一个能点名的具体风险才看包外代码，
并在回执里写明查了什么。你只读不改：不动工作区、不动 git 状态。

## 审什么

按 acceptance.md「整体五轴 review」：correctness / readability / architecture / security / performance。
参考输入：tasks 文件 [TASKS_FILE]、design/spec [DESIGN_SPEC_PATHS]。

## 回执格式

同任务级 review：每条 finding 带 file:line、按 Critical / Important / Minor 分级、
先说做得好的再列问题，最后按五轴各给一句判定。
```

> 阶段 3 审出的 Critical / Important：fix 派发**复用第三节任务级 fix 模板**，「任务简报」位换成
> design/spec 路径、边界从"单任务"换成"本次开发范围"；fix 后主 agent **先 commit 再复审**——
> 重跑 `scripts/acceptance-diff.sh <起点>` 生成新一轮包（机制与理由见 acceptance.md）。

## 五 · 派发前主 agent 自查

- 简报 / 报告 / diff 走的是**路径**？prompt 里没粘正文、没粘前序任务的累积摘要？
- review 派发里没有预判（"这个别报""顶多算 Minor"）？硬约束是逐字抄的？
- fix 派发**点名了覆盖测试**？收到 fix 回执后核了三样证据（覆盖测试 + 命令 + 输出）才生成新 diff 派复审？
- 用平台的模型参数**显式指定了本次派发的档位**（cheap/standard/most-capable），没有留空？
- 简报是 `task-brief.sh` 生成的基底 + 追加片段？没有手抄任务正文？
- 阶段 3 派发传了 `acceptance-diff.sh` 生成的整体包路径？fix 后是 commit 过再重新生成的新包？
