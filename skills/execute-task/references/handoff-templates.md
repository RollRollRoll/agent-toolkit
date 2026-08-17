# 任务工作文件与阶段 3 派发模板

> 用途：`execute-task` 阶段 2 的每任务工作文件规范，以及阶段 3 派发 subagent 时照抄填空的 prompt
> （占位符 `[...]`）。机制见 [orchestration.md](orchestration.md) 第四节。
>
> **阶段 2 不派任何 subagent**——主 agent 自己走 TDD 闭环，第一节给的是它自己要维护的两份文件；
> 派发模板（第二、三节）只用于阶段 3 整体验收。
> **模型档位不是 prompt 正文的一部分**：阶段 3 派发前先按 [model-selection.md](model-selection.md) 定档，
> 用平台的模型参数（如 Agent 工具的 `model`）指定，不要写进模板文本里、也不要留空。
> 派发机制、权限继承和工作目录按 [platform-agents.md](platform-agents.md) 执行。

## 一 · 每任务的三份工作文件（阶段 2，主 agent 自己维护）

临时工作目录 `.execute-task/`（仓库根下，含自忽略 `.gitignore`，不提交）由各脚本经
`scripts/workspace.sh` 自动创建，不必手建。

1. **任务基线**：开工前运行本 skill 目录下的 `scripts/task-baseline.sh <任务编号>`。
   它要求真实工作区没有暂存、未暂存或未跟踪改动，并记录当前 HEAD；
   失败就先处理现有改动，**不要覆盖基线或带脏开工**。提交前拿它核对 HEAD 未漂移。
2. **任务简报** `.execute-task/task-N-brief.md`：运行 `scripts/task-brief.sh <tasks文件> <任务编号>`——
   它机械抽取该任务全文（验收标准、验证方式、涉及文件，精确值逐字保真）并打印路径，
   任务号不存在会报错；**不要手抄任务正文**。然后把相关 design/spec 片段和**约定的 seam**
   （从 design / tasks 取；没指明就先与用户确认，理由见 [execution-loop.md](execution-loop.md) 第一节）
   **追加**到同一文件——这半截需要判断力，脚本管不了。
   它是需求的**唯一来源**：上下文被压缩后回来重读它，不靠记忆复述验收标准和精确值。
3. **执行记录** `.execute-task/task-N-record.md`：**边做边写**，每转一次红或绿就追加一次。
   闸门一读它核证据，阶段 3 的整体 review 拿它当输入。按下面的结构写：

````markdown
# 任务 N 执行记录：[任务名]

## 行为 1：[一句话说清验的是什么行为]

- 红：`[测试命令]`
  ```
  [失败输出，保留关键几行]
  ```
  为何预期失败：[行为缺失在哪——必须是行为缺失，不是语法 / import / 环境错]
- 绿：`[同一条测试命令]`
  ```
  [通过输出]
  ```

## 行为 2：…

## 收尾验证

`[任务的验证方式命令 + typecheck]`
```
[完整输出，含告警]
```

## 改动文件

- [路径]：[改了什么]

## 疑虑

- [看到但按规则没动的结构问题 —— 留给阶段 3 的 architecture 轴]
````

**跑完一整轮再凭印象补写的是回忆，不是证据**；只有绿没有红的行为，按闸门一的规则重做一遍红 → 绿。

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
执行期记下的结构疑虑 [CONCERNS：来自各任务执行记录 `.execute-task/task-*-record.md`；没有则删]。

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

把修复报告写进 [FIX_REPORT_FILE]（约定为 `.execute-task/acceptance-fix-<轮次>.md`）：
- 每条发现怎么修的
- 复验的测试命令与输出（涉及行为的附红 → 绿证据）

然后只回执：修了什么（每条一行）+ 一行测试摘要 + 报告路径。
修不了、或发现问题出在需求 / 设计层面 → 回执 BLOCKED 并说明，别硬改绕过。
```

> 主 agent 收到 fix 回执后**先 commit 再复审**——重跑本 skill 目录下的
> `scripts/acceptance-diff.sh <起点>` 生成新一轮包（机制与理由见 acceptance.md），
> 复审读新包。fix commit 同样必须落在阶段 0 的授权批次内。

## 四 · 自查

**阶段 2（每任务，自己做）**

- 开工前 `task-baseline.sh` 确认了真实工作区干净并记录了 HEAD？
- 简报是 `task-brief.sh` 生成的基底 + 追加片段（design/spec + 约定的 seam）？没有手抄任务正文？
  seam 来自 design / tasks，或已与用户确认？
- 执行记录是**边做边当场写**的，每个行为都有红（含"为何预期失败"）+ 绿？不是事后追写、
  也不是只留在对话上下文里？
- 任务内**一个 subagent 都没派**？
- 按闸门一核了三样（红 → 绿证据齐、收尾完整跑一次验证命令绿、HEAD 未漂移）才 commit？

**阶段 3（派发前）**

- 用平台的模型参数**显式指定了本次派发的档位**（整体验收固定 most-capable），没有留空？
- 派发传了 `acceptance-diff.sh` 生成的整体包路径，没让 reviewer 自己爬库？
- 把各任务执行记录里的结构疑虑一并交给了 reviewer？
- fix 后复审用的是 commit 过再重新生成的新包？
