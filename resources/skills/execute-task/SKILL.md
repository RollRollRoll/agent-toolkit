---
name: execute-task
description: 当用户已有确认过的开发任务清单（理想来自 split-task），要把它逐个落地成实现 + 测试 + 提交，并经验收确认真的做完时使用——如"执行任务、把 tasks 做掉、按任务清单开始编码、实现这些任务、推进开发"。不要用于：任务还没拆（先 split-task）、技术方案没定（先 make-design）、行为没钉死（先 write-spec）、想法还模糊（先 refine-idea）、单纯调试某个 bug、代码评审。
---

# Execute Task — 执行 Skill

## 你的任务

把一份**已确认的任务清单**（理想情况下来自 split-task），逐个落地成**实现 + 测试 + 提交**，
并经验收确认"真的做完了"。你要把"拆好的任务"变成"实现完、验证过、提交了、整体验收通过"的代码，
钉死四件事：

1. **按依赖 / wave 调度** —— 用 split-task 的依赖与并行视图排执行顺序，可并行的并行、高风险的先做。
2. **每任务走干净闭环** —— 干净基线 → 执行 subagent（TDD → 验证）→ 独立 review subagent 审查 → 独立 fix subagent 修复 → checkbox 与代码一起原子提交，不绿不算完成。
3. **进度可恢复** —— checkbox 回写 + 轻量账本，中断 / 上下文压缩后能续上，不重复执行。
4. **整体验收对回上游** —— whole-branch 五轴 review + 覆盖核对回扫，确认每个设计点都落地、不落空。

**这是本链唯一真正写代码的 skill**：前面 refine-idea / write-spec / make-design / split-task 都止于文档，
到 execute-task 才落地实现。但**守层不变**：不拆任务（那是 split-task）、不定技术决策（make-design）、
不定行为（write-spec）；发现上游有重大错误，退回上游修，不在执行里硬改。

> 一句话：把"拆好、可验收的任务清单"，**按依赖顺序逐个执行成通过验收的代码**——每个任务一个干净闭环，
> 进度记在可恢复账本里，最后整体验收逐条对回 design / spec。

## 核心理念

执行是这条链的**最后一棒，也是唯一产出代码的一棒**。前四道闸门把"做什么 / 做成什么样 / 怎么实现 / 拆成哪些任务"
都钉死了，但"代码写完了"不等于"做完了"——没过验收的实现、没测试的功能、漏掉的设计点、中断后重复执行的混乱，
都会让"完成"变成幻觉。execute-task 把"做完"变成**有客观判据的事**：每任务过验收门才提交、整体过验收门才收尾、
进度有账本可恢复——延续这条链"可验证"的基因到执行层。

execute-task 不挖意图、不定行为、不定技术决策、不拆任务——那都是上游的事。它只做一件事：
**把已确认的任务清单，执行成通过验收、可追溯、可恢复的代码。**

## 何时用 / 何时不用

**适用**：

- 任务清单已确认（或手上有 split-task 的 tasks），准备落地编码。
- 要把一组拆好的开发任务推进到"实现 + 测试 + 提交 + 整体验收"。
- 需要可恢复、可追溯的执行过程（中断后能续、每步有 commit、最后能整体验收）。

**不适用**（别硬套）：

- 任务还没拆 / 没确认 → 先 split-task。执行必须站在确认过的任务清单上。
- 技术方案没定 → 先 make-design；行为没钉死 → 先 write-spec；想法还模糊 → 先 refine-idea。
- 单纯定位某个已知 bug（不是执行任务清单）→ 用调试方法，不必起整套执行编排。
- 纯代码评审 → 用评审流程。

**⚠️ 加载约束**：execute-task **会真写代码、跑测试、提交**——没有前四个 skill 那种"止于文档"约束。但有硬线：

- **提交也必须先授权**：阶段 0 在任何代码修改前，说明当前分支、tasks 范围和预计提交批次，获得用户明确授权；拒绝或语义含糊就停止，不降级成“先改代码、以后再说”。超出授权范围的提交必须重新确认。若要用并行任务分支，还要单独说明并取得对具体集成 merge 的授权。
- **其他破坏性 / 对外操作必须用户确认**：合并到主干、提 PR、push、删文件 / 目录——呼应 CLAUDE.md 危险操作机制，**不自动做**。
- **重大上游错误退回，不硬改**：执行中发现 design / spec / tasks 有重大错误，停下退回对应上游 skill，不在执行里绕过。
- 可在自治 / 批处理场景执行任务，但**合并 / 对外操作仍要 gate**——遇到该合并时，正确做法是停下交用户拍板，而不是自动合并往下冲。

## 招牌机制：任务闭环 + 可恢复账本 + 双验收闸门 ⭐

执行类的招牌不是"探针覆盖"，而是执行纪律。两个核心 + 两道闸门：

### 核心一：每任务闭环（执行 / 审查 / 修复各派独立 subagent）

每个任务走一个干净闭环；闭环内的**执行、审查、修复各由一个独立的 fresh subagent 承担**：

**执行 subagent：在 seam 上 TDD（tracer bullet）→ 验证** → **review subagent：独立审查** → **fix subagent：修复 → 复审** → **atomic commit**

- **TDD**（执行 subagent）：一个行为测试 → 最小实现 → 通过 → 下一个行为。bug 类任务**先写复现测试**。在已约定的 seam（纯函数 / 接口）上测，不测难测的外壳。
- **小步推进**：不一次写完整功能、不堆到几百行才测；每一步保持系统可构建、可测。
- **验证**：跑该任务的「验收标准 + 验证方式」（split-task 已给）+ typecheck / 相关测试文件。**执行 subagent 到此为止：不 commit、不自审**。
- **审查**（独立 review subagent）：主 agent 另派 fresh reviewer 对照验收标准逐条审，结论按
  **Critical / Important / Minor** 分级——**写代码的不审自己的代码**。
- **fix**（独立 fix subagent）：有 Critical / Important → 另派 fresh fixer 带着 review 发现修复 → 再派 reviewer 复审；
  Minor 记录不阻塞。**修复按轮次计（默认 3 轮）**：超限仍有 Critical / Important → 停下交用户判断继续修还是另作处理。
- **handoff 走文件 + 状态回执**：任务简报 / 执行报告 / diff 三份交接文件传路径（不粘正文进 prompt）；
  执行回执带状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED），主 agent 按状态处理；
  review 拿三件套、以 diff 为准核对报告——机制见 [references/orchestration.md](references/orchestration.md)，
  三类派发 prompt 照抄 [references/handoff-templates.md](references/handoff-templates.md)。
- **atomic commit**：复审绿、过闸门一后，先回写 checkbox，再把代码、测试和 checkbox 一起提交；一个任务一个原子提交，提交信息可追溯到任务。提交必须落在阶段 0 的明确授权内。
- **按角色 + 复杂度定档模型**：派发执行 / review / fix subagent 时**必须显式指定模型档位**（cheap / standard / most-capable），
  阶段 3 整体验收固定用最强档——不写等于任其继承主 agent 当前档位（通常最贵），白白抬高成本；
  判据见 [references/model-selection.md](references/model-selection.md)。

> 主 agent 做 **orchestration（编排）**，不自己埋头糊代码、也不亲手审查 / 修复——派发执行 / review / fix subagent、收结果、过闸门、commit、记账本。
> （subagent 不可用的环境，降级为主 agent 顺序执行同一套闭环纪律。）

### 核心二：可恢复账本

每任务完成后记账，让执行可中断、可恢复：

- **checkbox 回写**：把 split-task 的 tasks.md 对应任务从 `- [ ]` 改成 `- [x]`，与该任务代码 / 测试进入同一个 commit（状态即进度）。
- **轻量 ledger**：在自忽略的 `.execute-task/` 内记已完成任务 + 对应 commit，提交成功后才写。
- **safe-resume**：重跑时读账本**跳过已完成任务**，绝不重复执行（防上下文压缩后从头再来）。

### 闸门一：每任务验收门

对齐 split-task 的「验收标准 + 验证方式」——**不过不 commit、不算完成**。验收不绿的任务不许标 `[x]`。

### 闸门二：整体验收门

全部任务完成后做 whole-branch review：

- **五轴 review**：correctness（正确）/ readability（可读）/ architecture（架构）/ security（安全）/ performance（性能）。
- **覆盖核对回扫**：对回 split-task 的覆盖核对表、spec 的成功标准——design 每个组件 / spec 每条 MUST / MUST NOT
  都**已实现且被测试覆盖**，不落空。
- **全绿**：全套测试 / 构建 / typecheck 通过。

**流程**：确认提交授权 → 调度排序（依赖 / wave）→ 逐任务闭环（干净基线 + 实现 + 闸门一 + 原子提交）→ ignored ledger → 整体验收（闸门二）→ 收尾。

## 工作流程（阶段 0 + 四个工作阶段）

### 阶段 0 · 定位与上下文

1. **接上游**：读 tasks（`docs/tasks/*` 或用户指明位置）作为主输入，读 design / spec 取验收口径。
   **无 tasks → 视为前置缺失**：执行必须站在确认过的任务清单上；没有就**建议先 split-task**，不要自己临场拆任务。
2. **扫代码库**：技术栈、**测试怎么跑、构建怎么跑、typecheck 怎么跑**——这决定每任务的验证怎么做。
3. **建 / 读进度账本**：首次执行建账本；续跑读账本，确定从哪个任务接着做。
4. **确认分支策略**：在哪个分支执行（默认当前工作分支；若在主干，按仓库习惯决定是否先开分支）。
5. **提交授权闸门（代码修改前）**：向用户明确说明当前分支、要执行的 tasks 范围，以及本批次将产生的任务提交和必要验收修复提交；等待“确认 / 继续 / 是”等明确授权。未授权、拒绝或范围不清 → **停止 execute-task，不派执行 subagent、不修改代码**。后续提交若超出该范围，重新确认。默认串行执行；若计划用并行任务分支，还必须同时说明 expected base、集成顺序与将执行的 merge，并取得明确授权。

### 阶段 1 · 调度规划

1. **排执行顺序**：按 split-task 的依赖与并行视图做拓扑排序。
2. **定并行与隔离**：默认串行执行。同 wave 只有在每个任务使用独立 worktree、共享同一个 expected base、能证明改动与 tasks checkbox 的集成不会冲突，且阶段 0 已授权具体 merge 时才并行；任一条件不满足就改回串行。建立隔离时调用 **setup-worktree**。
3. **高风险前置**：split-task 标了高风险 / 高不确定性的任务先做，早暴露问题。
4. **打印执行计划**：列出顺序、哪些并行、checkpoint 在哪——让执行过程可见。

### 阶段 2 · 逐任务执行闭环

1. 对每个任务，先运行 `scripts/task-baseline.sh <任务编号>`：真实工作区必须干净，并记录当前 HEAD；失败就停下处理，不能带着上个任务或用户的改动开工。然后按「核心一」闭环**分别派发独立 subagent**：先派执行 subagent（TDD → 验证，不 commit），
   再派 review subagent 独立审查；有 Critical / Important 再派 fix subagent 修复并复审
   （修复轮次超限仍不过 → 停下交用户判断）。
2. 派 review 前运行 `scripts/review-diff.sh <任务编号>`；它校验 HEAD 仍是任务基线，并把暂存、未暂存、删除、未跟踪及 binary 变化全部纳入审查包，且不修改真实 index。
3. 过「闸门一」后先回写 checkbox，确认提交仍在阶段 0 授权范围内，再把**已审代码 + 测试 + checkbox**一起 atomic commit；提交成功后写 ignored ledger，并用 `git status --porcelain=v1 --untracked-files=all` 校验真实工作区干净。未干净就停下排查，不开始下一任务。
4. 同 wave 默认仍串行；只有满足阶段 1 的独立 worktree、同基线、无冲突和 merge 授权四项条件才并行。并行时按预先声明的确定顺序集成并逐次验证；**wave 间串行**。
5. 每 2~3 个任务到 checkpoint 跑一次相关测试 / 构建，确认到这里是稳的。

### 阶段 3 · 整体验收

1. 先扫本次开发 diff 中的临时日志、调试打印、断点与临时开关；发现残留就精准清理、跑覆盖测试，并在阶段 0 授权范围内提交。工作区恢复干净后再生成整体验收包。
2. 过「闸门二」：**派独立 review subagent** 做五轴 review + 覆盖核对回扫，跑全套测试 / 构建 / typecheck 绿。
3. 不绿 / 有落空 → **派独立 fix subagent** 修复（或回阶段 2 补任务），修完再验收。

### 阶段 4 · 收尾

1. **调用 `finish-branch` 做收尾**：先清理本次开发的调试残留并重跑最终测试，再检测 repo/worktree 状态，
   给出合并到主干 / 本地保留 / 创建 PR / 丢弃选项。提交、合并、push、删除和移除 worktree 分别由用户授权，
   不把一种选择扩张成其他动作的许可。
2. execute-task 到"整体验收通过 + 收尾决策交付"为止，不擅自合并、不自动往下。

## 进度跟踪与恢复

- **状态存在 tasks.md 的 checkbox**：`- [x]` = 已完成、已提交、已过验收门；checkbox 必须在对应任务 commit 内。
- **ledger** 位于自忽略的 `.execute-task/`，提交成功后记每个完成任务对应的 commit，便于追溯与 safe-resume。
- **中断恢复**：重新执行时，先读账本与 checkbox，**已完成的跳过**；只接着做未完成的，绝不重复执行。
- 不引入 GSD 那套 STATE / ROADMAP 全套状态文件——checkbox + 轻 ledger 足够，别把进度跟踪做成负担。

## 上游纠错与守层

执行中发现 design / spec / tasks 有误时，分级处理（吸收 OpenSpec"可回改 artifacts"，但加守层闸门）：

- **小问题**（笔误、明显的小遗漏、不影响结构的偏差）→ **就地修正 + 回写 artifact + 告知用户**，继续执行。
- **重大问题**（技术决策错、需求缺失、任务依赖一段不存在的设计）→ **停下退回 make-design / split-task** 修订，
  不在执行里硬改绕过——否则代码会偏离已 review 的契约。

> 检验：「这个修正会不会改变已 review 的行为契约 / 技术决策 / 任务边界？」会 → 它是重大问题，退回上游，别就地改。

## 产物与收尾

- **产物是代码**（实现 + 测试 + 一串原子提交 + 回写的 tasks.md），不是文档。
- **收尾交 finish-branch**：执行完调用 finish-branch 决定合并 / 本地保留 / PR / 丢弃，破坏性操作由用户拍板。
- brownfield：执行只动 tasks 涉及的范围；迁移 / 回滚任务按 tasks 里标的来做。

## 核心原则（不要违反）

1. **每任务走可验收的干净闭环** —— 干净基线 → TDD → 验证 → 完整 diff 审查 → checkbox + 代码原子提交 → ignored ledger → clean 校验；不绿不算完成、不过验收门不 commit。
2. **先站在 tasks + design/spec 上再动手** —— 执行依据是确认过的任务清单与验收口径，不临场发挥。
3. **小步推进、每步可构建可测** —— 不一次写完整功能、不堆到几百行才测。
4. **主 agent 做编排，不埋头糊代码** —— 执行 / 审查 / 修复各派独立 subagent，主 agent 只派发、过闸门、commit、记账本，不亲手审查 / 修复；subagent 不可用才降级顺序执行。
5. **进度记可恢复账本** —— checkbox 回写 + ledger，safe-resume 不重复执行。
6. **整体验收对回上游** —— 五轴 review + 覆盖核对回扫，design / spec 每条都落地且被测试覆盖，不落空。
7. **守层** —— 不拆任务 / 不定决策 / 不定行为；重大上游错误退回，不硬改。
8. **提交与危险操作用户拍板** —— commit 必须先在阶段 0 获得明确批次授权；任务分支集成 merge 也需在阶段 0 明确授权；合并 / PR / push / 删文件不自动做。
9. **自包含** —— 不依赖**外部**插件；隔离 / 收尾复用工具集内的 setup-worktree / finish-branch；subagent 不可用降级为同一套纪律的顺序执行。

## 终止条件（可检验）

- **达标即停**：全部任务过闸门一、整体过闸门二（五轴 + 覆盖回扫 + 全绿）、收尾决策交付给用户——执行就完成了，别为"再优化一下"无限改。
- **兜底①**：执行中发现任务依赖的 design 决策缺失 / 错误（重大）→ **停下退回 make-design / split-task**，别用代码替设计补窟窿。
- **兜底②**：某任务反复实现不过 / 卡死（环境问题、需求歧义、外部依赖不可用），或 **fix loop 超轮次上限仍有
  Critical / Important** → **停下把判断告诉用户**——继续修、接受现状还是退回上游，由用户拍板，别在原地空转或硬猜。

## 自检清单（执行与收尾时过一遍）

- [ ] 在任何代码修改前，已向用户说明分支 / tasks / 提交批次并获得**明确提交授权**？每个实际 commit 都在授权范围内？
- [ ] 每任务开工前 `task-baseline.sh` 都确认了真实工作区干净并记录 HEAD？
- [ ] `review-diff.sh` 校验了 HEAD 未漂移，并把暂存 / 未暂存 / 删除 / 未跟踪 / binary 变化都交给 reviewer？
- [ ] 每任务都**过了验收门**（验收标准 + 验证方式绿）才标 `[x]`、才 commit？
- [ ] 每任务 commit 都包含**已审代码 + 测试 + checkbox**，随后才写 ignored ledger，并确认工作区干净？
- [ ] 审查和修复都**派了独立 subagent**（reviewer 不是写代码的那个、fixer 带 review 发现 fresh 上阵），主 agent 没亲手审 / 修？
- [ ] 每次派发都**显式指定了模型档位**（cheap/standard/most-capable），没有留空任其继承主 agent？阶段 3 整体验收用了最强档？
- [ ] handoff **走了文件三件套**（简报 / 报告 / diff 传路径）？执行回执带状态且按状态处理？fix 有测试证据才复审、复审用新 diff？
- [ ] review 结论按 **Critical / Important / Minor** 分级？fix loop **按轮次计**（默认 3 轮），超限停下交用户而不是无限循环？
- [ ] 在 **seam 上做了 TDD**（bug 先写复现测试）？小步推进、每步可构建可测？
- [ ] 调度按 tasks 的**依赖 / wave**，无环、顺序可执行？默认串行；若并行，是否每任务独立 worktree、expected base 相同、集成无冲突且 merge 已获授权？
- [ ] 整体验收过了**五轴 review**？**覆盖核对回扫**——design 组件 / spec MUST / MUST NOT 都已实现且被测试覆盖、不落空？
- [ ] 全套**测试 / 构建 / typecheck 绿**？
- [ ] 整体验收前 `acceptance-diff.sh` 拒绝了任何非忽略 dirty 状态，并确认 BASE 是 HEAD 的祖先？
- [ ] 中断恢复**读了账本**、没重复执行已完成任务？
- [ ] 发现上游错误：小修就地 + 回写 + 告知，**重大退回上游**？
- [ ] 破坏性 / 对外操作（合并 / PR / push）都**停下问了用户**，没自动做？
- [ ] 收尾给了用户**合并 / PR / 留分支**的决策，没擅自合并？

## 一次完整示范（照着这个节奏走）

> 接 split-task 那份"实验清单"任务清单（T1 建表 → T2 `list_experiments()` → T3 路由 + 模板 → T4 MUST NOT 收口），看它怎么被执行掉。

**阶段 0 · 定位与上下文**

> 读 tasks（4 个任务，线性依赖 T1→T2→T3→T4）+ design / spec（验收口径）。扫项目：测试 `pytest`、
> 无构建步骤、无 typecheck（小 Python 项目）。首次执行，建进度账本。分支：在当前 feature 分支执行。
> 向用户说明“本批次会产生 T1~T4 四个任务提交，以及整体验收发现问题时的必要修复提交”，获得明确授权后才继续。

**阶段 1 · 调度规划**

> 依赖链线性、split-task 已标"无并行"，无需 worktree。执行计划：T1 → T2 → T3 → T4，
> checkpoint 设在 T2 后（数据层绿）、T3 后（开页面）。无高风险任务。

**阶段 2 · 逐任务执行闭环（以 T2 为例）**

> 1. 运行 `task-baseline.sh T2`，确认 T1 提交后的真实工作区干净，记录当前 HEAD；再**派执行 subagent**接 T2「`list_experiments()` 查询 + 校验 + 稳定排序」：
>    - **TDD**：先写 `tests/test_models.py` —— `test_invalid_status`（非法 status 标记异常）、
>      `test_empty`（空集合返回 `[]`）、`test_stable_sort`（created_at 同按 id）、`test_owner_none`（owner 空不抛错）→
>      跑 `pytest tests/test_models.py` → **红**（函数还没写）。
>    - **最小实现** `list_experiments()`：取数 + 状态校验 + 稳定排序 → 跑 → **绿**。
>    - 回报"实现 + 测试绿"，**不 commit、不自审**。
> 2. 运行 `review-diff.sh T2`，确认 HEAD 未漂移并生成包含 tracked / untracked / binary 变化的完整 diff；**另派 review subagent**（fresh，只带 T2 验收标准 + diff）：对照验收标准逐条核——四条都满足；
>    纯函数无副作用、可单测 ✓。若审出 Critical / Important（如排序不稳定），**再派 fix subagent** 带着 review 发现修复 →
>    复审（超 3 轮仍有 Critical / Important 就停下问用户）；Minor 记录不阻塞。
> 3. 复审绿、过**闸门一** → tasks.md 的 T2 改 `- [x]`；确认仍在阶段 0 授权内，把实现、测试和 checkbox 一起
>    `git commit -m "feat: list_experiments 查询+校验+稳定排序"`（atomic）。
> 4. **回写账本**：提交成功后，ignored ledger 记 commit；确认真实工作区干净，再开始 T3。
>
> 〔T1 / T3 / T4 同构。T3 后到 checkpoint：开页面看列表 + 空态 + owner 空。〕

**阶段 3 · 整体验收**

> 过**闸门二**：
> - 全套 `pytest` 绿；无构建 / typecheck 步骤。
> - **五轴**（派独立 review subagent）：正确（验收全过）/ 可读（纯函数清晰）/ 架构（取数-校验-排序抽成纯函数，路由只渲染）/
>   安全（只读、无注入面）/ 性能（数据量小，无需优化）——通过。
> - **覆盖核对回扫**：对回 split-task 覆盖核对表——experiments 表(T1) / `list_experiments`(T2) /
>   路由+模板(T3) / 三条 MUST NOT(T4) 全部实现且有测试或检查覆盖，**不落空**。

**阶段 4 · 收尾**

> 提交都在 feature 分支。给出收尾选项：
> > 「实验清单 4 个任务全部完成、整体验收通过（pytest 全绿 + 覆盖核对无落空）。
> > 收尾你想怎么走？**A 合并到 main**　**B 提 PR**　**C 留在分支**。合并 / PR 我不会自动做，等你定。」
>
> 〔清理：无临时分支 / worktree / 调试代码需清理。等用户拍板收尾方式。〕

## 反例（不要这样做）

❌ 不写测试直接糊实现；或先把所有测试写完再写所有实现（水平切片，测试与真实行为脱节）。
❌ 一个任务没过验收门就 commit / 标 `[x]` —— 验收门形同虚设。
❌ 一次性写完整功能、堆到几百行才跑一次测试 —— 不是小步推进。
❌ 主 agent 自己埋头糊完所有代码，不做编排 —— 违背 subagent 编排骨架。
❌ 执行 subagent 写完自己审自己修，或主 agent 亲手审查 / 修复 —— 审查和 fix 必须各派独立 subagent。
❌ 派发 subagent 不写模型，任其继承主 agent 当前档位（通常最贵）—— 该按角色 / 复杂度显式定档。
❌ fix loop 不设轮次上限无限修，或超限后不问用户硬冲；反过来把 Minor 问题也当阻塞项修个没完。
❌ 中断后不读账本，从头重跑、重复执行已完成任务。
❌ 跳过整体验收，"测试绿就算完" —— 漏了五轴 review 和覆盖核对回扫。
❌ 发现 design 设计错了，在执行里硬改绕过，不退回 make-design。
❌ 自动合并到 main / 自动提 PR / 自动 push —— 没让用户拍板（危险操作）。
❌ tasks 还没确认就开始执行 —— 该先 split-task。
❌ 没有阶段 0 的明确提交授权就改代码或 commit；或把含糊的“看看吧”当授权。
❌ 上一任务留下 dirty 工作区仍开下一任务，或只用普通 `git diff` 导致暂存 / 未跟踪文件没进审查包。
❌ 先 commit 代码、之后再单独改 tasks checkbox / ledger —— checkbox 会留脏或与任务提交失去原子性。
❌ 越界回去拆任务 / 改技术决策 / 改行为契约 —— 那是上游的事。
❌ 某任务卡死却反复重试、空转，不告知用户。
❌ 运行时去调用 / 依赖外部插件 —— 本 skill 自包含，subagent 不可用就降级顺序执行。

## 相关参考

- [references/orchestration.md](references/orchestration.md) —— 调度与编排：
  依赖 / wave 排序、并行与 worktree 隔离、subagent 派发与文件 handoff（简报 / 报告 / diff、状态回执协议）、进度账本与 safe-resume。
- [references/execution-loop.md](references/execution-loop.md) —— 每任务闭环：
  TDD seam / tracer bullet、小步推进、验证节奏（typecheck / 单测 / 全套）、独立 review / fix subagent 闭环、atomic commit、bug 诊断。
- [references/handoff-templates.md](references/handoff-templates.md) —— handoff 模板：
  执行 / 审查 / 修复三类 subagent 的派发 prompt（照抄填空），含交接文件准备与派发前自查。
- [references/acceptance.md](references/acceptance.md) —— 验收与收尾：
  每任务验收门、整体五轴 review、覆盖核对回扫、上游纠错守层、收尾（合并 / PR / 留分支）。
- [references/model-selection.md](references/model-selection.md) —— 模型选择：
  派发执行 / review / fix subagent 与整体验收时，按角色与复杂度定档（cheap / standard / most-capable）的判据。
