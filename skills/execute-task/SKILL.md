---
name: execute-task
description: 当用户已有确认过的开发任务清单（理想来自 split-task），要把它逐个落地成实现 + 测试 + 提交，并经验收确认真的做完时使用——如"执行任务、把 tasks 做掉、按任务清单开始编码、实现这些任务、推进开发"。不要用于：任务还没拆（先 split-task）、技术方案没定（先 make-design）、行为没钉死（先 write-spec）、想法还模糊（先 refine-idea）、只做单个改动的红绿闭环（那是 tdd）、只做一次代码审查（那是 review-changes）、单纯调试某个 bug、代码评审。
---

# Execute Task — 执行编排 Skill（workflow 层）

## 你的任务

把一份**已确认的任务清单**（理想情况下来自 split-task），**编排**成实现 + 测试 + 提交，
并经验收确认"真的做完了"。你不亲手定义怎么写测试、怎么审代码——那些交给 composable 层；
你钉死的是**编排层的四件事**：

1. **按依赖 / wave 调度** —— 用 split-task 的依赖与并行视图排执行顺序，可并行的并行、高风险的先做，
   并为每个任务备齐**约定的 seam**。
2. **每任务一个可核对的闭环** —— 干净基线 → 调用 **tdd** 走红 → 绿 → 过闸门一（核证据）→
   checkbox 与代码一起原子提交。判据是**落盘的红 → 绿证据 + 验证全绿 + 范围没漂**，不绿不算完成。
3. **进度可恢复** —— checkbox 回写 + 轻量账本，中断 / 上下文压缩后能续上，不重复执行。
4. **整体验收对回上游** —— 调用 **review-changes** 做 whole-branch 审查 + 自己做覆盖核对回扫，
   确认每个设计点都落地、不落空；这是全链路唯一的审查与修复轮。

**这是本链唯一真正写代码的 skill**：前面 refine-idea / write-spec / make-design / split-task 都止于文档，
到 execute-task 才落地实现。但**守层不变**：不拆任务（那是 split-task）、不定技术决策（make-design）、
不定行为（write-spec）；发现上游有重大错误，退回上游修，不在执行里硬改。

> 一句话：把"拆好、可验收的任务清单"，**按依赖顺序逐个编排成通过验收的代码**——
> 每个任务调 tdd 走一个红 → 绿闭环并凭证据过门，进度记在可恢复账本里，
> 最后调 review-changes 做一次整体审查并逐条对回 design / spec。

## 分层与调用

本 skill 是 **workflow 层**的最后一棒。workflow 层是
`refine-idea → write-spec → make-design → split-task → execute-task` 这条链，各守一道闸门、
把产物交给下一棒。执行期需要的**具体能力**一律调用 **composable 层**：

| 调用点 | composable skill | 传入 | 取回 |
|---|---|---|---|
| 阶段 1 需要隔离 / 并行 | **setup-worktree** | expected base、用途 | worktree 路径 + 已验证的 HEAD |
| 阶段 2 每个任务 | **tdd** | 任务简报路径、**约定的 seam**、验证方式、记录路径（`.execute-task/`，名称 `task-N`） | 证据齐否、改动文件、疑虑、记录路径 |
| 阶段 3 整体验收 | **review-changes** | BASE 起点 commit、design/spec/tasks 路径、各任务疑虑 | 分级 findings（带 `file:line`）+ 六关判定 |
| 阶段 4 收尾 | **finish-branch** | 最终验证命令、本次开发范围、调用来源（本 skill） | 收尾决策与已执行的动作 |

三条跨层约定：

- **调用即交出该层的判据定义权**：不在本 skill 里重述 tdd 的循环规则、也不重述 review-changes 的审查判据——
  需要细节时读那个 skill，别在这里维护第二份。
- **调用 tdd 不是派 subagent**：阶段 2 由主 agent 自己加载 tdd 的执行纪律走完闭环，任务内**不派任何 subagent**。
  全流程唯一的 subagent 派发点是阶段 3（review 与 fix），fresh 上下文正是那道门的价值。
- **被调 skill 不可用时，闸门判据不变**：主 agent 按闸门一 / 闸门二的判据自己完整走一遍
  （红 → 绿证据齐、六关逐项判定），并说明降级原因——**降级的是谁来做，不是做不做**。

## 核心理念

执行是这条链的**最后一棒，也是唯一产出代码的一棒**。前四道闸门把"做什么 / 怎么实现 / 拆成哪些任务"
都钉死了，但"代码写完了"不等于"做完了"。execute-task 把"做完"变成**有客观判据的事**：
每任务凭红 → 绿证据过门才提交、整体过验收门才收尾、进度有账本可恢复。
判据是**机制自带的**（先红后绿、命令实跑、范围不漂），不是再加一层"另一个 agent 看过了"的主观确认。

## 何时用 / 何时不用

**适用**：

- 任务清单已确认（或手上有 split-task 的 tasks），准备落地编码。
- 要把一组拆好的开发任务推进到"实现 + 测试 + 提交 + 整体验收"。
- 需要可恢复、可追溯的执行过程（中断后能续、每步有 commit、最后能整体验收）。

**不适用**（别硬套）：

- 任务还没拆 / 没确认 → 先 split-task。执行必须站在确认过的任务清单上。
- 技术方案没定 → 先 make-design；行为没钉死 → 先 write-spec；想法还模糊 → 先 refine-idea。
- 只是**一个改动**要走红 → 绿 → 直接用 **tdd**，不必起整套编排。
- 只是要**审一遍改动** → 直接用 **review-changes**。
- 单纯定位某个已知 bug、纯代码评审 → 用对应方法，不必起整套执行编排。

**⚠️ 加载约束**：execute-task **会真写代码、跑测试、提交**——没有前四个 skill 那种"止于文档"约束。但有硬线：

- **提交也必须先授权**：阶段 0 在任何代码修改前，说明当前分支、tasks 范围和预计提交批次，获得用户明确授权；
  拒绝或语义含糊就停止，不降级成"先改代码、以后再说"。超出授权范围的提交必须重新确认。
  若要用并行任务分支，还要单独说明并取得对具体集成 merge 的授权。
- **其他破坏性 / 对外操作必须用户确认**：合并到主干、提 PR、push、删文件 / 目录——遵循当前仓库
  `CLAUDE.md` / `AGENTS.md` 与平台审批策略，**不自动做**。
- **重大上游错误退回，不硬改**：执行中发现 design / spec / tasks 有重大错误，停下退回对应上游 skill，
  不在执行里绕过。
- 可在自治 / 批处理场景执行任务，但**合并 / 对外操作仍要 gate**——遇到该合并时，正确做法是停下交用户拍板。

## 招牌机制：调度编排 + 可恢复账本 + 双验收闸门 ⭐

编排类的招牌不是"探针覆盖"，而是执行纪律。两个核心 + 两道闸门：

### 核心一：每任务一个干净闭环（调用 tdd，任务内不派 subagent）

**干净基线** → **备简报与 seam** → **调用 tdd 走红 → 绿** → **过闸门一（核证据）** → **atomic commit**

- **seam 事先约定**：seam 由 make-design / split-task 指定；没指明的任务，开工前把 seam 写下来
  **与用户确认**，再写进任务简报交给 tdd——**不让 tdd 自己挑地方测**。测错地方比测得少更糟，
  任务内没有 reviewer 会发现。
- **一次只做一个任务**：手上同时只推进一个任务的闭环。混着做会让"范围没漂"这条判据失效，也拆不出原子提交。
- **记录落文件，不只留在上下文**：任务简报与 tdd 的执行记录都写进自忽略的 `.execute-task/`——
  上下文一旦被压缩，留在对话里的证据就没了，落盘的还在；safe-resume 也靠它。
- **重构不夹带**：tdd 交回的「疑虑」记进账本，留给阶段 3 的 architecture 关，不在任务内顺手改。
- **atomic commit**：过闸门一后先回写 checkbox，再把代码、测试和 checkbox 一起提交；
  一个任务一个原子提交，提交信息可追溯到任务。提交必须落在阶段 0 的明确授权内。

> **质量靠 TDD 本身承担**：红 → 绿是自带判据的机制，任务内不再套一层主观审查；
> 架构级审查集中到阶段 3 做一次。

### 核心二：可恢复账本

每任务完成后记账，让执行可中断、可恢复：

- **checkbox 回写**：把 split-task 的 tasks.md 对应任务从 `- [ ]` 改成 `- [x]`，
  与该任务代码 / 测试进入同一个 commit（状态即进度）。
- **轻量 ledger**：在自忽略的 `.execute-task/` 内记起点 commit、已完成任务 + 对应 commit +
  tdd 交回的结构疑虑（交阶段 3），提交成功后才写。
- **safe-resume**：重跑时读账本**跳过已完成任务**，绝不重复执行（防上下文压缩后从头再来）。

### 闸门一：每任务证据门（跑命令与比对，不是代码审查）

任务「验收标准」逐条对上，外加核三样：

1. **红 → 绿证据齐**：tdd 交回的执行记录里每个行为都有实现前的失败输出（含"为何预期失败"）+
   实现后的通过输出，且都是**当场记下的**。
2. **验证方式收尾实跑绿**：提交前**完整跑一次**任务的验证命令（加 typecheck / 相关测试文件），
   告警噪音也要看见——不拿红绿循环中途某一次的输出顶替。
3. **范围没漂**：HEAD 仍是 `task-baseline.sh` 记录的基线，改动落在任务涉及文件内。

**不齐不 commit、不算完成**，也不许标 `[x]`。记录只有绿没有红 → 这个任务没走成 TDD：
把缺的行为**交回 tdd 重做一遍红 → 绿**，做不到就记录在案并告知用户，**别事后补一段测试冒充红证据**。

### 闸门二：整体验收门（全链路唯一的审查与修复轮）

全部任务完成后做 whole-branch 验收：

- **调用 review-changes**：派 fresh subagent（固定最强档）加载它，对 BASE..HEAD 做六关审查
  （五轴 + 测试质量），把各任务疑虑一并交给它。
- **覆盖核对回扫（本 skill 自己做）**：对回 split-task 的覆盖核对表、spec 的成功标准——
  design 每个组件 / spec 每条 MUST / MUST NOT 都**已实现且被测试覆盖**，不落空。
- **全绿**：全套测试 / 构建 / typecheck 通过。
- 审出的 Critical / Important **派独立 fix subagent** 修复 → 复审（**按轮次计，默认 3 轮**，
  超限停下交用户），Minor 记录不阻塞。

**流程**：确认提交授权 → 调度排序（依赖 / wave + seam 清单）→ 逐任务闭环（干净基线 + 调用 tdd +
闸门一 + 原子提交）→ ignored ledger → 整体验收（闸门二）→ 收尾。

## 工作流程（阶段 0 + 四个工作阶段）

### 阶段 0 · 定位与上下文

1. **接上游**：读 tasks（`docs/tasks/*` 或用户指明位置）作为主输入，读 design / spec 取验收口径。
   **无 tasks → 视为前置缺失**：执行必须站在确认过的任务清单上；没有就**建议先 split-task**，
   不要自己临场拆任务。
2. **扫代码库**：技术栈、**测试怎么跑、构建怎么跑、typecheck 怎么跑**——这决定每任务的验证怎么做，
   也是交给 tdd 的「验证方式」。
3. **建 / 读进度账本**：首次执行建账本并记**起点 commit**（`git rev-parse HEAD`——阶段 3 的 BASE）；
   续跑读账本，确定从哪个任务接着做。
4. **确认分支策略**：在哪个分支执行（默认当前工作分支；若在主干，按仓库习惯决定是否先开分支）。
5. **提交授权闸门（代码修改前）**：向用户明确说明当前分支、要执行的 tasks 范围，以及本批次将产生的
   任务提交和必要验收修复提交；等待"确认 / 继续 / 是"等明确授权。未授权、拒绝或范围不清 →
   **停止 execute-task，不开工、不修改代码**。后续提交若超出该范围，重新确认。默认串行执行；
   若计划用并行任务分支，还必须同时说明 expected base、集成顺序与将执行的 merge，并取得明确授权。

### 阶段 1 · 调度规划

1. **排执行顺序**：按 split-task 的依赖与并行视图做拓扑排序。
2. **列 seam 清单**：逐任务从 design / tasks 取出该任务的**可测接缝**；有任务没指明 seam → 现在就与用户确认，
   确认后写进该任务简报。**没有确认过 seam 的任务不开工**——测试写在哪决定这个闭环能验住什么。
3. **定并行与隔离**：默认串行执行。同 wave 只有在每个任务使用独立 worktree、共享同一个 expected base、
   能证明改动与 tasks checkbox 的集成不会冲突，且阶段 0 已授权具体 merge 时才并行。
   建立隔离时调用 **setup-worktree**。
4. **高风险前置**：split-task 标了高风险 / 高不确定性的任务先做，早暴露问题。
5. **打印执行计划**：列出顺序、每个任务测在哪个 seam、哪些并行、checkpoint 在哪——让执行过程可见。

### 阶段 2 · 逐任务执行闭环

1. 运行 `scripts/task-baseline.sh <任务编号>`：真实工作区必须干净，并记录当前 HEAD；
   失败就停下处理，不能带着上个任务或用户的改动开工。
2. 备好任务简报（`scripts/task-brief.sh` 抽取 + 追加 design/spec 片段与**约定的 seam**）。
3. **调用 tdd**，按其调用契约传入：简报路径、seam、验证方式、记录参数（名称 `task-N`、
   输出目录 `.execute-task/`）。任务内**不派任何 subagent**——主 agent 自己走完这个闭环。
4. 收 tdd 交回的证据齐否 / 改动文件 / 疑虑 / 记录路径，过「闸门一」（三样证据 + 验收标准逐条对上）；
   不齐 → 交回 tdd 把缺的行为重做红 → 绿，或交用户判断，不往下走。
5. 过门后先回写 checkbox，确认提交仍在阶段 0 授权范围内，再把**代码 + 测试 + checkbox**一起
   atomic commit；提交成功后写 ignored ledger（含本任务的疑虑），并用
   `git status --porcelain=v1 --untracked-files=all` 校验真实工作区干净。未干净就停下排查，不开始下一任务。
6. 同 wave 默认仍串行；只有满足阶段 1 的四项条件才并行。并行时按预先声明的确定顺序集成并逐次验证；
   **wave 间串行**。
7. 每 2~3 个任务到 checkpoint 跑一次相关测试 / 构建，确认到这里是稳的。

### 阶段 3 · 整体验收

1. 先扫本次开发 diff 中的临时日志、调试打印、断点与临时开关；发现残留就精准清理、跑覆盖测试，
   并在阶段 0 授权范围内提交。工作区恢复干净后再进入验收。
2. 过「闸门二」：**派独立 subagent 加载 review-changes**（固定最强档），传 BASE 起点 commit、
   tasks / design / spec 路径、各任务疑虑；它自己生成审查包并回六关 findings。
   同时跑全套测试 / 构建 / typecheck 绿，并**自己做覆盖核对回扫**。
3. 不绿 / 有落空 / 有 Critical 或 Important → **派独立 fix subagent** 修复（或回阶段 2 补任务），
   涉及行为的修复仍先补失败测试再修到绿；修完 commit 再复审（按轮次计，超限交用户）。

### 阶段 4 · 收尾

1. **调用 `finish-branch` 做收尾**：先清理本次开发的调试残留并重跑最终测试，再检测 repo/worktree 状态，
   给出合并到主干 / 本地保留 / 创建 PR / 丢弃选项。提交、合并、push、删除和移除 worktree 分别由用户授权，
   不把一种选择扩张成其他动作的许可。
2. execute-task 到"整体验收通过 + 收尾决策交付"为止，不擅自合并、不自动往下。

## 进度跟踪与恢复

- **状态存在 tasks.md 的 checkbox**：`- [x]` = 已完成、已提交、已过闸门一；checkbox 必须在对应任务 commit 内。
- **ledger** 位于自忽略的 `.execute-task/`，记起点 commit、每个完成任务对应的 commit 与 tdd 交回的结构疑虑，
  便于追溯、safe-resume 和阶段 3 整体验收。
- **中断恢复**：重新执行时，先读账本与 checkbox，**已完成的跳过**；只接着做未完成的，绝不重复执行。
- 不引入 GSD 那套 STATE / ROADMAP 全套状态文件——checkbox + 轻 ledger 足够，别把进度跟踪做成负担。

## 上游纠错与守层

执行中发现 design / spec / tasks 有误时，分级处理：

- **小问题**（笔误、明显的小遗漏、不影响结构的偏差）→ **就地修正 + 回写 artifact + 告知用户**，继续执行。
- **重大问题**（技术决策错、需求缺失、任务依赖一段不存在的设计）→ **停下退回 make-design / split-task** 修订，
  不在执行里硬改绕过——否则代码会偏离已 review 的契约。

> 检验：「这个修正会不会改变已 review 的行为契约 / 技术决策 / 任务边界？」会 → 它是重大问题，退回上游，别就地改。

## 产物与收尾

- **产物是代码**（实现 + 测试 + 一串原子提交 + 回写的 tasks.md），不是文档。
- **收尾交 finish-branch**：执行完调用 finish-branch 决定合并 / 本地保留 / PR / 丢弃，破坏性操作由用户拍板。
- brownfield：执行只动 tasks 涉及的范围；迁移 / 回滚任务按 tasks 里标的来做。

## 核心原则（不要违反）

1. **每任务走可核对的闭环** —— 干净基线 → 调用 tdd 红 → 绿 → 三样证据核对 → checkbox + 代码原子提交 →
   ignored ledger → clean 校验；证据不齐不算完成、不 commit。
2. **测在约定的 seam 上** —— seam 来自 design / tasks，缺就先与用户确认后写进简报再交给 tdd。
3. **先站在 tasks + design/spec 上再动手** —— 执行依据是确认过的任务清单与验收口径，不临场发挥。
4. **能力交给 composable 层** —— 红绿闭环调 tdd、整体审查调 review-changes、隔离调 setup-worktree、
   收尾调 finish-branch；不在本 skill 里维护第二份判据。
5. **任务内主 agent 自己做，不派 subagent** —— 调用 tdd 是加载纪律；subagent 只在阶段 3 出现。
6. **进度记可恢复账本** —— checkbox 回写 + ledger，safe-resume 不重复执行。
7. **审查集中在整体验收一次** —— review-changes 六关 + 本 skill 的覆盖核对回扫，design / spec 每条都落地
   且被测试覆盖，不落空；任务内不开审查轮。
8. **守层** —— 不拆任务 / 不定决策 / 不定行为；重大上游错误退回，不硬改。
9. **提交与危险操作用户拍板** —— commit 必须先在阶段 0 获得明确批次授权；任务分支集成 merge 也需在阶段 0
   明确授权；合并 / PR / push / 删文件不自动做。
10. **自包含** —— 不依赖**外部**插件，只调用本工具集内的 composable skill；被调 skill 或 subagent
    不可用时，由主 agent 按同一套判据自己走完（阶段 3 以 fresh 视角走六关），**不删掉那道门**。

## 终止条件（可检验）

- **达标即停**：全部任务过闸门一、整体过闸门二（六关 + 覆盖回扫 + 全绿）、收尾决策交付给用户——
  执行就完成了，别为"再优化一下"无限改。
- **兜底①**：执行中发现任务依赖的 design 决策缺失 / 错误（重大）→ **停下退回 make-design / split-task**，
  别用代码替设计补窟窿。
- **兜底②**：某任务反复实现不过 / 卡死（tdd 交回 BLOCKED）、**红 → 绿证据补不出来**，
  或 **阶段 3 的 fix loop 超轮次上限仍有 Critical / Important** → **停下把判断告诉用户**——
  继续修、接受现状还是退回上游，由用户拍板，别在原地空转或硬猜。

## 自检清单（执行与收尾时过一遍）

- [ ] 在任何代码修改前，已向用户说明分支 / tasks / 提交批次并获得**明确提交授权**？每个实际 commit 都在授权范围内？
- [ ] 每任务开工前 `task-baseline.sh` 都确认了真实工作区干净并记录 HEAD？
- [ ] 每个任务的 **seam 都是约定过的**（来自 design / tasks，或已与用户确认并写进简报）？没有让 tdd 自己挑地方测？
- [ ] 每任务都**过了闸门一的三样证据**（红 → 绿齐、收尾完整跑一次验证命令绿、HEAD 未漂移且范围没越界）才标 `[x]`、才 commit？
- [ ] 记录只有绿没有红时**把那个行为交回 tdd 重做了红 → 绿**，没把事后补的测试当 TDD 证据？
- [ ] 每任务 commit 都包含**代码 + 测试 + checkbox**，随后才写 ignored ledger，并确认工作区干净？
- [ ] 任务内**一个 subagent 都没派**（调用 tdd 是加载纪律，不是派发）？
- [ ] tdd 的执行记录落在 `.execute-task/task-N-record.md`，不是只留在对话上下文里？
- [ ] 阶段 3 的 review / fix 派发**显式指定了模型档位**，整体验收用了最强档？
- [ ] 调度按 tasks 的**依赖 / wave**，无环、顺序可执行？默认串行；若并行，是否每任务独立 worktree、
      expected base 相同、集成无冲突且 merge 已获授权？
- [ ] 整体验收**调用了 review-changes**（独立 subagent、最强档），并把各任务疑虑交给了它？
      审出的 Critical / Important 派 fix 修了、按轮次计？
- [ ] **覆盖核对回扫**——design 组件 / spec MUST / MUST NOT 都已实现且被测试覆盖、不落空？
- [ ] 全套**测试 / 构建 / typecheck 绿**？
- [ ] 生成审查包前工作区无非忽略改动、BASE 是 HEAD 的祖先？
- [ ] 中断恢复**读了账本**、没重复执行已完成任务？
- [ ] 发现上游错误：小修就地 + 回写 + 告知，**重大退回上游**？
- [ ] 破坏性 / 对外操作（合并 / PR / push）都**停下问了用户**，没自动做？
- [ ] 收尾**调用了 finish-branch**，给了用户合并 / PR / 留分支的决策，没擅自合并？

## 一次完整示范（照着这个节奏走）

> 接 split-task 那份"实验清单"任务清单（T1 建表 → T2 `list_experiments()` → T3 路由 + 模板 →
> T4 MUST NOT 收口），看它怎么被执行掉。

**阶段 0 · 定位与上下文**

> 读 tasks（4 个任务，线性依赖 T1→T2→T3→T4）+ design / spec（验收口径）。扫项目：测试 `pytest`、
> 无构建步骤、无 typecheck（小 Python 项目）。首次执行，建进度账本并记起点 commit `a1b2c3d`。
> 分支：在当前 feature 分支执行。
> 向用户说明"本批次会产生 T1~T4 四个任务提交，以及整体验收发现问题时的必要修复提交"，获得明确授权后才继续。

**阶段 1 · 调度规划**

> 依赖链线性、split-task 已标"无并行"，无需 worktree（不调 setup-worktree）。执行计划：T1 → T2 → T3 → T4，
> checkpoint 设在 T2 后（数据层绿）、T3 后（开页面）。无高风险任务。
> **seam 清单**：T1 建表脚本 / migration 的幂等接口、T2 `list_experiments()` 纯函数、T3 路由响应，
> T4 三条 MUST NOT 各自的检查点——design 已指明 T1~T3，T4 的 seam design 没写，
> 与用户确认为"在 `list_experiments()` 与路由两层各加拒绝用例"后写进 T4 简报。

**阶段 2 · 逐任务执行闭环（以 T2 为例）**

> 1. `task-baseline.sh T2` 确认 T1 提交后工作区干净，记录 HEAD；`task-brief.sh` 抽 T2 简报，
>    追加 design 片段与 seam（`list_experiments()` 纯函数）。
> 2. **调用 tdd**：传简报路径、seam、验证方式 `pytest tests/test_models.py`、记录参数
>    （`task-2` + `.execute-task/`）。tdd 逐个行为走红 → 绿——`test_empty` → 红（`NameError`，行为缺失）→
>    最小实现 → 绿；`test_invalid_status` → 红 → 校验 → 绿；`test_stable_sort` → 红 → 稳定排序 → 绿；
>    `test_owner_none` → 红 → 绿。收尾完整跑一次 `pytest tests/test_models.py` → 4 passed。
>    交回：证据齐、改动 `models.py` + `tests/test_models.py`、疑虑一条（"取数可拆两个 helper，按规则没动"）、
>    记录路径 `.execute-task/task-2-record.md`。
> 3. 过**闸门一**核三样：记录里四个行为红 → 绿证据齐、都是当场写的 ✓；收尾验证完整跑绿、无告警 ✓；
>    `git rev-parse HEAD` 仍是基线、改动只在那两个文件 ✓；验收标准四条逐条对上 ✓。
> 4. 过门 → tasks.md 的 T2 改 `- [x]`；确认仍在阶段 0 授权内，把实现、测试和 checkbox 一起
>    `git commit -m "feat: list_experiments 查询+校验+稳定排序"`（atomic）。
> 5. **回写账本**：提交成功后 ledger 记 commit + 那条疑虑（留阶段 3）；确认工作区干净，再开始 T3。
>
> 〔T1 / T3 / T4 同构。T3 后到 checkpoint：开页面看列表 + 空态 + owner 空。〕

**阶段 3 · 整体验收**

> 先扫 diff 无调试残留，工作区干净。过**闸门二**：
> - 全套 `pytest` 绿；无构建 / typecheck 步骤。
> - **调用 review-changes**（派独立 subagent，最强档）：传 BASE `a1b2c3d`、tasks/design/spec 路径、
>   两条结构疑虑。它生成审查包后回六关判定：correctness（验收全过）/ readability（纯函数清晰）/
>   architecture（"取数拆 helper"判为 Minor，不阻塞）/ security（只读、无注入面）/ performance（数据量小）/
>   测试质量（四个用例都走公共函数、期望值是字面量，无同义反复）——无 Critical / Important。
> - **覆盖核对回扫（自己做）**：对回 split-task 覆盖核对表——experiments 表(T1) / `list_experiments`(T2) /
>   路由+模板(T3) / 三条 MUST NOT(T4) 全部实现且有测试或检查覆盖，**不落空**。

**阶段 4 · 收尾**

> 调用 **finish-branch**。它给出收尾选项：
> > 「实验清单 4 个任务全部完成、整体验收通过（pytest 全绿 + 六关无阻塞项 + 覆盖核对无落空）。
> > 收尾你想怎么走？**A 合并到 main**　**B 提 PR**　**C 留在分支**。合并 / PR 我不会自动做，等你定。」

## 反例（不要这样做）

❌ 在本 skill 里重写一遍红绿循环规则或五轴审查判据 —— 那是 tdd / review-changes 的事，维护两份必然漂移。
❌ 跳过 tdd 直接自己糊实现再补测试 —— 红没发生过，闸门一的证据造不出来。
❌ 不给 tdd 传 seam，让它自己挑地方测 —— seam 缺就先与用户确认。
❌ 一个任务没过闸门一（三样证据缺一样）就 commit / 标 `[x]` —— 证据门形同虚设。
❌ tdd 交回"只有绿没有红"，事后补一段测试冒充红证据。
❌ 在任务内派执行 / 审查 / 修复 subagent —— 任务内只有主 agent 加载 tdd 自己走，subagent 只在阶段 3 出现。
❌ 阶段 3 派发 review / fix 不写模型，任其继承主 agent 当前档位 —— 该显式定档，整体验收固定最强档。
❌ 阶段 3 的 fix loop 不设轮次上限无限修，或超限后不问用户硬冲；反过来把 Minor 问题也当阻塞项修个没完。
❌ 中断后不读账本，从头重跑、重复执行已完成任务。
❌ 跳过整体验收，"测试绿就算完" —— 任务内已经没有审查轮，跳过闸门二等于全程没被审过。
❌ 只调 review-changes 就算验收完 —— 覆盖核对回扫是本 skill 自己的活，它不做。
❌ 发现 design 设计错了，在执行里硬改绕过，不退回 make-design。
❌ 自动合并到 main / 自动提 PR / 自动 push —— 没让用户拍板（危险操作）。
❌ tasks 还没确认就开始执行 —— 该先 split-task。
❌ 没有阶段 0 的明确提交授权就改代码或 commit；或把含糊的"看看吧"当授权。
❌ 上一任务留下 dirty 工作区仍开下一任务，或不核 HEAD 就提交。
❌ 先 commit 代码、之后再单独改 tasks checkbox / ledger —— checkbox 会留脏或与任务提交失去原子性。
❌ 越界回去拆任务 / 改技术决策 / 改行为契约 —— 那是上游的事。
❌ 运行时去调用 / 依赖外部插件 —— 本工具集自包含；阶段 3 无 subagent 可用时主 agent 以 fresh 视角
   自己走一遍 review-changes 的六关，不是删掉那道门。

## 相关参考

调用的 composable skill（**tdd / review-changes / setup-worktree / finish-branch**）见上文「分层与调用」表——
它们的判据住在各自的 SKILL.md，需要细节直接读那一份。以下是本 skill 自己的参考：

- [references/orchestration.md](references/orchestration.md) —— 调度与编排：依赖 / wave 排序、
  并行与 worktree 隔离、任务工作文件、进度账本与 safe-resume。
- [references/acceptance.md](references/acceptance.md) —— 双验收闸门：闸门一证据核对、
  闸门二编排与 fix 循环、覆盖核对回扫、上游纠错守层、收尾。
- [references/handoff-templates.md](references/handoff-templates.md) —— 任务简报的准备，
  以及阶段 3 review / fix 派发 prompt（照抄填空）与派发前自查。
- [references/model-selection.md](references/model-selection.md) —— 阶段 3 派发的档位判据
  （standard / most-capable），以及为什么任务内不再有定档动作。
- [references/platform-agents.md](references/platform-agents.md) —— Claude Code 与 Codex 在阶段 3 的
  subagent 派发、权限继承、模型参数和并行工作目录；派发前按当前平台读取。
