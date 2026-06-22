# execute-task 设计文档

日期：2026-06-22

## 背景与目标

综合五个上游项目在"任务拆分后如何推进执行"上的设计精华，为 agent-toolkit 新增
split-task 之后的**执行层** skill：把一份已确认的**任务清单**（理想来自 split-task），
逐个落地成**实现 + 测试 + 提交**，并经每任务验收门与整体验收门确认"真的做完了"。

**这是本链第一个真正写代码的 skill**——与前四个"规划/设计类"skill（产出文档、止于 review、不写代码）
**是不同物种**，结构不与它们同构；但保留家族基因：**验收闸门**是这条链"可验证"纪律在执行层的延续。

五个母体（综合，不照抄任何一个；**以 superpowers 为骨架基础**）：

- **superpowers（subagent-driven-development / executing-plans / TDD / finishing）**：每任务 fresh subagent 实现，
  每任务 review loop（审查→fix→复审），whole-branch review，ledger 防上下文压缩后重复执行，
  finishing 收尾决策；主 agent 做 orchestration 而非自己糊代码。
- **GSD Core（execute-phase）**：wave 并行、worktree 隔离、atomic commit、SUMMARY/STATE 可恢复、safe-resume gate。
- **agent-skills（incremental-implementation / TDD / code-review-and-quality）**：小步实现（不一次写完、不超约 100 行才测）、
  每步保持可构建可测、未完功能用 feature flag、bug 先写复现测试、五轴 review（correctness/readability/architecture/security/performance）。
- **OpenSpec（opsx:apply / verify）**：checkbox 即执行状态、执行中可回改 artifacts、verify 三维（完整/正确/一致）。
- **mattpocock（implement / tdd / diagnosing-bugs）**：TDD tracer bullet（一个行为测试→最小实现→通过→下一个）、
  在 seam 上做 TDD、频繁验证（typecheck/单测文件/全套）、bug 诊断流程、最后 review + commit。

## 定位

站在 split-task（任务清单）下游、链路的最末端：

- 上游 split-task 给"可独立验收、带依赖与验证方式"的任务清单 —— 主要输入。
- 上游 design/spec 提供验收口径（验收标准 / MUST / 成功标准）的最终来源。
- 本 skill 把任务清单**执行掉**：调度 → 逐任务闭环实现 → 进度记账 → 整体验收 → 收尾。

> **链路最终形态**：
> `refine-idea → write-spec → make-design → split-task → execute-task`
> 五道工序：挖意图 → 定行为 → 定技术决策 → 拆任务 → **执行落地**。

**不同物种的结构差异**（相对前四个 skill）：

| 维度 | 前四个（规划类） | execute-task（执行类） |
|---|---|---|
| 产物 | 文档（概念单/spec/design/tasks） | 实现 + 测试 + 提交 |
| 终态 | 落盘 + 用户 review 门禁 | 全部实现 + 测试绿 + 整体验收 + 收尾决策 |
| 招牌 | 探针 + 覆盖核对 | 任务闭环 + 可恢复账本 + 双验收闸门 |
| 加载约束 | 止于文档、不写代码 | 会真写代码；破坏性/对外操作需用户确认 |
| 中断恢复 | 一次性落盘 | 进度账本 + safe-resume |

## 关键设计决策（本次确认）

1. **自包含复刻（用户拍板）**：以 superpowers 的执行逻辑为骨架，融合其他四源，**全部自己写、运行时不依赖外部插件**。
   - 理由：与前四个 skill 同一哲学（借鉴五源但自包含），整个 agent-toolkit 能作为自洽的中文工具集独立分发，
     不假设使用者装了 superpowers。
2. **中重 subagent 编排 + 可选并行（用户拍板）**：每任务 fresh subagent 走闭环，进度账本可恢复，最终整体 review；
   GSD 的 wave 并行 / worktree 隔离作为**可选能力**（按 split-task 的并行标注启用），不强制；不搞 GSD 全套状态文件。
   - 理由："以 superpowers 为基础"= subagent 编排 + review loop + 整体验收是骨架；wave/worktree 重特性可选，避免对个人/中小任务集 over-engineer。
3. **收尾边界（推断，用户认可）**：执行到"全部实现 + 测试绿 + 整体验收过"，收尾给出 **合并 / PR / 留分支** 选项**让用户拍板**；
   合并 / PR / push 等破坏性或对外操作**不自动做**。
4. **上游纠错守层（推断，用户认可）**：执行中发现 design/spec/tasks 有误——**小问题**（笔误 / 明显小遗漏）就地修正 + 回写 + 告知；
   **重大问题**（设计错 / 需求缺）停下退回 make-design / split-task 修订，不在执行里硬改。吸收 OpenSpec"可回改 artifacts"但加守层闸门。
5. **进度跟踪（推断，用户认可）**：checkbox 回写 split-task 的 tasks.md（无缝衔接）+ 轻量 ledger 记已完成任务与 commit；
   重跑读账本跳过已完成，不搞 GSD 全套 STATE/ROADMAP。
6. **危险操作 gate（推断，用户认可）**：execute-task 会真写代码（无"止于文档"约束），但合并 / PR / push / 删文件等**必须用户确认**，呼应 CLAUDE.md 危险操作机制。

## 招牌机制：任务闭环 + 可恢复账本 + 双验收闸门

执行类的招牌不是"探针覆盖"，而是执行纪律。两个核心 + 两道闸门：

- **核心一 · 每任务闭环**（superpowers + mattpocock + agent-skills）：每个任务由 fresh subagent 执行，走
  **在 seam 上 TDD（tracer bullet：一个行为测试 → 最小实现 → 通过 → 下一个）→ 验证（验收标准 + typecheck/测试）→
  审查 → fix loop → atomic commit**。一个任务一个干净闭环，小步推进、每步保持可构建可测。
- **核心二 · 可恢复账本**（OpenSpec + superpowers + GSD）：每任务完成 checkbox 回写 tasks.md + 轻量 ledger 记 commit；
  中断 / 上下文压缩后 **safe-resume**：读账本跳过已完成，绝不重复执行。
- **闸门一 · 每任务验收门**：对齐 split-task 的「验收标准 + 验证方式」，**不过不 commit**——验收不绿不算完成。
- **闸门二 · 整体验收门**（agent-skills 五轴 + OpenSpec verify）：全部任务完成后做 whole-branch review，按
  correctness / readability / architecture / security / performance 五轴审查 + **覆盖核对回扫**（对回 split-task 覆盖核对表、spec 成功标准）+ 全套测试/构建绿。

**流程**：调度排序（依赖/wave）→ 逐任务闭环（实现 + 闸门一）→ 账本记录 → 整体验收（闸门二）→ 收尾。

## 工作流程（阶段 0 + 四阶段）

- **阶段 0 · 定位与上下文**：读 tasks（主）+ design/spec（验收口径）；扫代码库（**测试 / 构建 / typecheck 怎么跑**）；
  建 / 读进度账本；确认分支策略。**无 tasks → 退回 split-task**。
- **阶段 1 · 调度规划**：按 split-task 的依赖与并行视图排执行顺序，定哪些任务并行、是否用 worktree 隔离，打印执行计划。
- **阶段 2 · 逐任务执行闭环**：每任务 fresh subagent 跑「核心一」；过「闸门一」后 atomic commit + 回写账本；
  同 wave 可并行（不冲突文件 / 可 worktree 隔离），wave 间串行。
- **阶段 3 · 整体验收**：过「闸门二」（五轴 review + 覆盖核对回扫 + 全套测试/构建绿）。不绿 → 回阶段 2 修。
- **阶段 4 · 收尾**：给出合并 / PR / 留分支选项交用户拍板（不自动合并/PR/push）；清理临时分支 / 调试代码 / worktree。

## 五源如何被综合（不照抄）

- **superpowers** → subagent 编排骨架 + 每任务 review loop + ledger + whole-branch review + finishing 收尾 → 招牌机制核心一/二、阶段 2/3/4。
- **GSD Core** → wave 并行 + worktree 隔离 + atomic commit + safe-resume → 阶段 1 调度（可选）、核心二可恢复账本。
- **agent-skills** → 小步实现纪律 + 保持可构建可测 + 五轴 review + bug 先复现测试 → 核心一闭环、闸门二五轴。
- **OpenSpec** → checkbox 即状态 + 可回改 artifacts（加守层）+ verify 三维 → 核心二账本、决策 4 守层纠错、闸门二验收。
- **mattpocock** → TDD tracer bullet + seam + 频繁验证（typecheck/单测/全套）+ bug 诊断 → 核心一 TDD 节奏。

## 原创内核

把五源的执行主张收束成一条可操作的纪律：**"每个任务走一个可验收的干净闭环（TDD → 验证 → 审查 → 原子提交），
进度记在可恢复账本里，最后整体验收逐条对回 design/spec"**——让"做完了"有客观判据（每任务验收门 + 整体验收门 + 全绿 +
覆盖不落空），而不是"代码写完了"就算完。这是这条链"可验证"基因从规划层延伸到执行层。

## 边界（本 skill 不做什么）

- 不拆任务（那是 split-task）；tasks 没确认就退回上游。
- 不定技术决策（make-design）、不定行为（write-spec）、不挖意图（refine-idea）。
- 不软依赖外部插件（自包含；以 superpowers 为思想骨架，但不在运行时调用它）。
- 不自动做破坏性 / 对外操作（合并 / PR / push / 删文件需用户拍板）。
- 重大上游错误不在执行里硬改 —— 退回 make-design / split-task。

## 文件结构

```text
resources/skills/execute-task/
  SKILL.md
  README.md
  metadata.yaml
  references/
    orchestration.md   调度与编排：依赖/wave 并行、worktree 隔离、subagent 派发、进度账本与 safe-resume
    execution-loop.md  每任务闭环：TDD seam / tracer bullet、验证节奏、审查、fix loop、atomic commit、bug 诊断
    acceptance.md      每任务验收门 + 整体五轴 review + 覆盖核对回扫 + 收尾（合并/PR/留分支）
  docs/specs/
    2026-06-22-execute-task-design.md   本文档
```

贯穿案例延续「实验清单」：执行 split-task 那份 4 任务清单（T1 建表 → T2 `list_experiments()` → T3 路由+模板 →
T4 MUST NOT 收口），演示线性调度、T2 的 TDD 闭环（写 `test_models` 失败 → 最小实现 → 绿 → 审查 → commit）、
整体验收（pytest 全绿 + 覆盖回扫 + 路由 smoke + 开页面）、收尾提示。

> **subagent 措辞**：SKILL.md 用平台中立表述（"派发一个 subagent"），并注明在 Claude Code 里用 Task/Agent 工具；
> subagent 不可用的环境降级为主 agent 顺序执行同一套闭环纪律。

## 衔接修订（split-task 下游措辞校正）

execute-task 落地后，本链"执行"这一棒由 execute-task 承担。需校正 split-task 里把下游执行
指向"执行 / writing-plans"的措辞，正名为 execute-task（与本项目历次衔接修订同理）。

**校正原则**：split-task 中指向下游执行 skill 的措辞 → 改指 **execute-task**；去掉对外部 `writing-plans` 的指名
（自包含哲学下本链文档不再指名外部插件）。纯描述"split-task 自己不写代码"的自检句（不指向下游 skill）保留。

**涉及位置（8 处）**：
- `split-task/SKILL.md`：L19（你的任务·刻意止步）、L48（何时不用）、L172（阶段 4 提示）、L199（核心原则 8）、
  L311（示范收尾）、L322（反例）——"下游执行 / writing-plans"改指 execute-task。
- `split-task/README.md`：L12（用途）、L21（触发场景·不适用）——同方向校正。
- 保留：`split-task/SKILL.md` L223 自检句"没下沉到逐行实现、没写代码"（描述自身边界，不指向下游，语义正确）。
- 历史 design 快照不回溯。

## 发布

按 `docs/conventions.md` 新增资源流程：

- 新建 `resources/skills/execute-task/` 下 SKILL.md / README.md / metadata.yaml / references / docs。
- `metadata.yaml`：id=execute-task，type=skill，status=draft，created_at/updated_at=2026-06-22。
- `.claude-plugin/plugin.json` 的 `skills` 数组加入 `./resources/skills/execute-task`。
- **双清单版本同步**：`plugin.json` 与 `marketplace.json` 版本 `0.5.0` → `0.6.0`。
- 用 `claude plugin validate . --strict` 校验。
