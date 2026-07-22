# Codebase Analyzer 输出目的地选择（终端/文件/两者）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 codebase-analyzer 的"报告输出"从"无条件先刷满终端 + 事后问保存"改为"产出后、输出前先问目的地（终端 / 文件 / 两者）"，支持"不在终端刷整份报告"。

**Architecture:** 纯文档 / prompt 工程改动。改动主体是 `SKILL.md`「第 6 步」整段重写（事后问保存 → 事中问目的地三选），外加第 5 步自检与反例两处同步；`parallel-strategy.md` 把两处"问保存"措辞更新为"问输出目的地"，并在「分阶段输出节奏」补一段大项目流式协调规则（过程推进度+概要、逐章成稿不贴终端、完整报告最终按目的地落定）。只改 2 个现有文件，不新建文件，不动三个报告模板的章节骨架（沿用 spec 路线 A）。

**Tech Stack:** Markdown skill 文件（无代码、无测试框架）。本计划的"验证"= `grep` / 阅读确认改动落位 + 对照 spec 第 6 节验收标准做一致性核对，不是单元测试。

**关联 spec:** `docs/superpowers/specs/2026-06-04-codebase-analyzer-output-destination-design.md`

> **提交约定**：本项目 `git commit` 需用户明确确认。计划中的 commit 步骤在执行时先与用户确认再提交。

**工作目录约定:** 下文命令里的 skill 文件均在 `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/`，git 仓库根在 `/Users/chenjinfan/Project/codebase-analyzer/`。

---

## File Structure

| 文件 | 职责 | 本次改动 |
|---|---|---|
| `SKILL.md` | 主流程 | **改动主体**：第 6 步整段重写 + 第 5 步自检通用项加 1 条 + 反例第 191 行更新 |
| `references/parallel-strategy.md` | 大项目并行调研策略 | 两处"问保存"→"问输出目的地" + 「分阶段输出节奏」补 1 段流式协调 |

执行顺序：先 Task 1（`SKILL.md`，"询问输出目的地"这个名字的定义源头），再 Task 2（`parallel-strategy.md` 引用该名字），最后 Task 3 对照 spec 验收做整体自检。

---

## Task 1: `SKILL.md` 第 6 步重写 + 自检 + 反例

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md`（第 148-160 行第 6 步、第 124-126 行自检通用项、第 191 行反例）

- [ ] **Step 1: 第 6 步整段重写（事后问保存 → 事中问目的地）**

用 Edit 工具，把下面这整段（旧第 6 步，第 148-160 行）：

````
### 第 6 步：询问是否保存报告

报告在对话中产出、且第 5 步自检通过后，**主动询问用户是否把这份报告保存为文件**。默认**不自动保存**——等用户明确表示要存再写盘。

- **询问方式**：用一句话问"是否将这份调研报告保存为文件？"。当前环境提供交互式选择工具（如 Claude Code 的 AskUserQuestion）时用它给出"保存 / 不保存"两个选项；不可用就用纯文本询问。
- **用户不需要保存**：到此结束，不写任何文件。
- **用户需要保存**：把刚产出的那一档报告**原文**（中文、Markdown）写入文件：
  - **默认位置**：被调研项目的根目录。
  - **默认文件名**：`<项目名>-调研报告-<YYYYMMDD>.md`——`<项目名>` 取被调研目录名，`<YYYYMMDD>` 取当天日期，例如 `codebase-analyzer-调研报告-20260603.md`。
  - 用户若指定了自己的路径 / 文件名，以用户的为准。
  - 写盘前若发现**同名文件已存在**，先提示用户确认覆盖还是改名，不要静默覆盖。
  - 写入内容就是对话里那份报告，不要为落盘重新精简或扩写。
- **大项目分阶段产出时**：等全部模块聚合、形成完整报告后再询问保存，存的是最终完整版，而非阶段 1 的过渡概览。
````

替换为（新第 6 步，对应 spec §3 + §4）：

````
### 第 6 步：询问输出目的地

报告在对话中产出、且第 5 步自检通过后，**先不要把全文贴出来**，而是问用户希望报告输出到哪里。默认**不自动写盘**——按用户选择决定。

- **询问方式**：当前环境提供交互式选择工具（如 Claude Code 的 AskUserQuestion）时用它给出下面三个选项；不可用就用纯文本询问，让用户回一个。
  - **终端**：把报告全文输出在对话里，不写文件。
  - **文件**：写入文件，对话里只回 `✅ 已写入 <路径>` + 报告的**一页纸概览**，不刷全文。
  - **两者**：报告全文输出在对话里，**同时**写入文件。
- **一页纸概览的来源**（"文件"档终端要留的那段）：标准 / 深度档直接摘报告里的 `## 一页纸概览` 章节；快速概览档没有该章节，摘它的"一句话定义 + 核心价值"两三行。
- **选"文件"或"两者"时的写盘细节**：把刚产出的那一档报告**原文**（中文、Markdown）写入文件：
  - **默认位置**：被调研项目的根目录。
  - **默认文件名**：`<项目名>-调研报告-<YYYYMMDD>.md`——`<项目名>` 取被调研目录名，`<YYYYMMDD>` 取当天日期，例如 `codebase-analyzer-调研报告-20260604.md`。
  - 用户若指定了自己的路径 / 文件名，以用户的为准。
  - 写盘前若发现**同名文件已存在**，先提示用户确认覆盖还是改名，不要静默覆盖。
  - 写入内容就是对话里那份报告，不要为落盘重新精简或扩写。
- **选完不再二次追问**：选"终端"就只输出在对话里、不存盘；想存又想终端看全文的，一开始就选"两者"。
- **大项目分阶段产出时**：等全部模块 / 章节聚合、形成完整报告后再问目的地，落定的是最终完整版而非阶段 1 的过渡概览；流式过程中只向终端推进度 + 概要、逐章成稿不贴终端（见 [references/parallel-strategy.md](references/parallel-strategy.md) 的「分阶段输出节奏」）。
````

- [ ] **Step 2: 第 5 步自检「通用项」新增一条**

用 Edit 工具，把：

````
- [ ] 关键论断是不是都附上了文件路径 / 行号？源码里没有证据的结论，是否都标了"不确定"？没凭名字 / README 猜？
- [ ] 全文是不是中文？
````

替换为：

````
- [ ] 关键论断是不是都附上了文件路径 / 行号？源码里没有证据的结论，是否都标了"不确定"？没凭名字 / README 猜？
- [ ] 全文是不是中文？
- [ ] 输出前问过目的地了吗？（终端 / 文件 / 两者）选"文件 / 两者"时处理了同名覆盖吗？
````

> 说明：这两行只在第 5 步「通用项（三档都要）」出现一次（第 125-126 行），匹配唯一。

- [ ] **Step 3: 反例第 191 行更新为新语义**

用 Edit 工具，把：

````
❌ 没问过用户就擅自把报告写进项目目录，或反过来——产出后绝口不提保存。本 skill 要求"先问，再按需存"。
````

替换为：

````
❌ 没问过目的地就把整篇报告刷满终端，或擅自把报告写进项目目录。本 skill 要求**产出后、输出前先问目的地**（终端 / 文件 / 两者），再按用户选择输出。
````

- [ ] **Step 4: 验证三处都落位、旧措辞已清**

Run:
```bash
cd /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer
grep -nc "第 6 步：询问输出目的地" SKILL.md
grep -nc "询问是否保存报告" SKILL.md
grep -n "输出前问过目的地" SKILL.md
grep -n "没问过目的地就把整篇报告刷满终端" SKILL.md
```
Expected:
- 第 1 条 = `1`（新标题已就位）
- 第 2 条 = `0`（旧标题已清除）
- 第 3 条命中第 5 步自检新增条
- 第 4 条命中更新后的反例

- [ ] **Step 5: 提交（先与用户确认）**

```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add codebase-analyzer/SKILL.md
git commit -m "SKILL 第6步改为事中问输出目的地（终端/文件/两者）+ 自检/反例同步"
```

---

## Task 2: `parallel-strategy.md` 措辞更新 + 流式协调补段

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/parallel-strategy.md`（第 37 行「分阶段输出节奏」、第 182 行编排时间线 ⑥、第 221 行流式节奏）

- [ ] **Step 1: 编排时间线 ⑥ 的"问保存"→"问输出目的地"**

用 Edit 工具，把：

````
⑥ 自检 → 问保存
````

替换为：

````
⑥ 自检 → 问输出目的地
````

- [ ] **Step 2: 流式节奏句末的"问保存"→"问输出目的地"**

用 Edit 工具，把：

````
沿用本文件「分阶段输出节奏」：概览 + 目录地图先出 → **主动停一下**给用户调整关注点 / 排除章节 → 之后每完成一批章节同步一次 → 最后聚合完整版 → 自检 → 问保存。
````

替换为：

````
沿用本文件「分阶段输出节奏」：概览 + 目录地图先出 → **主动停一下**给用户调整关注点 / 排除章节 → 之后每完成一批章节同步一次 → 最后聚合完整版 → 自检 → 问输出目的地。
````

- [ ] **Step 3: 「分阶段输出节奏」末尾补流式协调段（落 spec §4）**

用 Edit 工具，把：

````
**关键**：阶段 1 输出后**主动停一下**，告诉用户你的下一步计划，给用户机会调整顺序、指定关注点、或排除某些模块。
````

替换为：

````
**关键**：阶段 1 输出后**主动停一下**，告诉用户你的下一步计划，给用户机会调整顺序、指定关注点、或排除某些模块。

**最终输出目的地**：阶段 2~4 向用户同步的是**进度 + 概要**（全局概览、目录地图、"模块 / 章节 X 已就绪"），逐份成稿**不必逐一贴到终端**。等聚合出完整报告后，再按 SKILL「第 6 步：询问输出目的地」让用户选终端 / 文件 / 两者——选"文件"则完整全文写盘、终端只留路径 + 一页纸概览。这样既保留分阶段的进度感，又不在选"文件"时把全文刷满终端。
````

- [ ] **Step 4: 验证措辞已全部更新、无残留**

Run:
```bash
cd /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer
grep -nc "问保存" references/parallel-strategy.md
grep -nc "问输出目的地" references/parallel-strategy.md
grep -n "最终输出目的地" references/parallel-strategy.md
```
Expected:
- 第 1 条 = `0`（旧措辞已清除）
- 第 2 条 = `2`（编排时间线 + 流式节奏各一处）
- 第 3 条命中新补的流式协调段

- [ ] **Step 5: 提交（先与用户确认）**

```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add codebase-analyzer/references/parallel-strategy.md
git commit -m "并行策略：问保存→问输出目的地，并补大项目流式协调段"
```

---

## Task 3: 整体一致性自检（对照 spec 验收标准）

**Files:**
- Read-only 核对：上述 2 个文件 + spec

- [ ] **Step 1: 逐条对照 spec 第 6 节验收标准**

打开 spec `docs/superpowers/specs/2026-06-04-codebase-analyzer-output-destination-design.md` 第 6 节，逐条确认：
1. 第 6 步已重写为"询问输出目的地"，三选语义 / 一页纸概览来源 / 落盘规则齐备 —— 阅读 Task 1 Step 1 改后的第 6 步确认。
2. 三档统一都问；选完不二次追问存盘 —— 第 6 步「选完不再二次追问」条已写明，未按档分叉。
3. "文件"档终端 = 路径 + 一页纸概览；标准 / 深度摘现成 `## 一页纸概览`、快速概览摘"一句话定义 + 核心价值" —— 第 6 步「一页纸概览的来源」条确认。
4. 落盘规则（默认路径 / 命名 / 同名提示 / 原文写入）完整保留 —— 第 6 步「写盘细节」条确认。
5. 大项目流式：过程推进度 + 概要、逐章成稿不贴终端、完整版最终落定 —— 已写进 `parallel-strategy.md`（Task 2 Step 3）+ 第 6 步「大项目分阶段产出时」条。
6. 所有"问保存"措辞已更新、无残留 —— 用 Step 2 全仓 grep 核对。
7. 第 5 步自检通用项、反例区均已同步 —— Task 1 Step 2 / Step 3。

- [ ] **Step 2: 全仓 grep 确认旧"问保存"语义无残留**

Run:
```bash
grep -rnE "问保存|询问是否保存|是否将这份调研报告保存为文件|询问保存" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/
```
Expected: **无输出**（旧的"问保存"措辞在 SKILL 与 references 全部清除）。

> 注：新第 6 步里仍会出现"写盘""不存盘"等词，这是落盘动作的正常描述，**不是**要清除的旧措辞；本步只针对"问保存 / 询问是否保存"这类被取代的交互措辞。

- [ ] **Step 3: 交叉引用可达性核对**

Run:
```bash
grep -rn "询问输出目的地\|第 6 步" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/
```
Expected: `parallel-strategy.md` 新流式协调段里"SKILL「第 6 步：询问输出目的地」"的引用，能落到 `SKILL.md` 第 6 步真实标题（无悬空引用）；`SKILL.md` 第 6 步里指向 `parallel-strategy.md`「分阶段输出节奏」的链接真实存在。

- [ ] **Step 4: 若发现缺漏或不一致，修复并提交（先与用户确认）**

修复后：
```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add -A
git commit -m "输出目的地选择：一致性修订"
```
若 Step 1~3 全部通过、无需修复，则跳过本步。

---

## Self-Review（计划作者已执行）

**1. Spec coverage（spec 各节 → 计划任务映射）：**
- spec §2 核心决策（事中问 / 三档都问 / 三选 / 只问一次）→ Task 1 Step 1 新第 6 步全覆盖 ✓
- spec §3 新第 6 步定稿文案（三选语义 / 一页纸概览来源 / 落盘细节）→ Task 1 Step 1 ✓
- spec §4 大项目流式协调 → Task 2 Step 3「分阶段输出节奏」补段 + Task 1 Step 1 第 6 步「大项目分阶段产出时」条 ✓
- spec §5.1 SKILL 三处（第 6 步 / 第 5 步自检 / 反例）→ Task 1 Step 1/2/3 ✓
- spec §5.2 parallel-strategy 两处"问保存"+ 流式补句 → Task 2 Step 1/2/3 ✓
- spec §6 验收标准 7 条 → Task 3 Step 1 逐条核对 ✓
- spec §7 Non-goals（不加格式选项 / 不加按档默认 / 不动模板骨架 / 不新建文件 / 不改落盘默认规则）→ 计划只改 2 个现有文件、落盘规则原样保留、未触碰任何模板与格式选项 ✓

**2. Placeholder scan:** 各 old/new 文本块均为完整成稿，无 TBD / TODO；`<项目名>` `<YYYYMMDD>` `<路径>` 是面向终端用户的有意占位（与原文风格一致），非计划缺口。✓

**3. 措辞 consistency:** 全程统一用「询问输出目的地」「终端 / 文件 / 两者」「一页纸概览」「写盘细节」；新标题、自检条、反例、parallel-strategy 引用四处对「第 6 步：询问输出目的地」的称呼一致；grep 验证里的字符串与 old/new 文本逐字对应。✓

---

## Execution Handoff

计划已保存到 `docs/superpowers/plans/2026-06-05-codebase-analyzer-output-destination.md`。两种执行方式：

1. **Subagent-Driven（推荐项）** —— 每个任务派一个全新 subagent，任务间我来 review，迭代快。
2. **Inline Execution** —— 在本会话内用 executing-plans 批量执行、设检查点 review。

> 注：本计划只改 2 个文档文件、彼此有交叉引用，且 git commit 需你确认——**Inline Execution 在这里其实更顺手**（无需跨 subagent 传递文件状态，改完连贯）。但你定。

选哪种？
