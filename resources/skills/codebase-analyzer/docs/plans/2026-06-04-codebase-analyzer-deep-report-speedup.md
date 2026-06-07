# Codebase Analyzer 深度报告提速（按章节并行起草）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 codebase-analyzer 的深度报告档加一条"按报告章节并行起草 + 分阶段流式"提速路径，缩短深度档大项目的撰写墙钟并给出连续进度感。

**Architecture:** 纯文档 / prompt 工程改动，复用第 8 章 g 类已验证的"派子 agent + 主 agent 控全局"模式，把它从扩展件泛化到整章报告。改动主体落在 `parallel-strategy.md` 新增一个并列变体节，再用 `SKILL.md` 四处串联、`template-deep.md` 一句指引把它接进现有流程。只改 3 个现有文件，不新建文件（沿用 spec 的路线 A）。

**Tech Stack:** Markdown skill 文件（无代码、无测试框架）。本计划的"验证"= `grep` / 阅读确认改动落位 + 对照 spec 第 10 节验收标准做一致性核对，不是单元测试。

**关联 spec:** `docs/superpowers/specs/2026-06-04-codebase-analyzer-deep-report-speedup-design.md`

> **提交约定**：本项目 `git commit` 需用户明确确认。计划中的 commit 步骤在执行时先与用户确认再提交。

**工作目录约定:** 下文命令里的 skill 文件均在 `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/`，git 仓库根在 `/Users/chenjinfan/Project/codebase-analyzer/`。

---

## File Structure

| 文件 | 职责 | 本次改动 |
|---|---|---|
| `references/parallel-strategy.md` | 大项目并行调研策略（含各变体） | **改动主体**：新增「变体：按报告章节并行起草（深度档提速）」节 |
| `SKILL.md` | 主流程 | 四处串联：第 4 步、第 5 步深度档自检、大项目策略、相关参考 |
| `references/template-deep.md` | 深度档报告骨架 | 顶部说明区加一句并行起草指引；骨架不动 |

执行顺序：先 Task 1（`parallel-strategy.md`，是其余两文件引用的源头），再 Task 2（`SKILL.md` 串联），再 Task 3（`template-deep.md`），最后 Task 4 整体一致性自检。

---

## Task 1: 在 `parallel-strategy.md` 新增「按报告章节并行起草」变体节

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/parallel-strategy.md`（在第 114 行「## 变体：按扩展条目并行」节之后、第 138 行「## 反例」之前插入新节）

- [ ] **Step 1: 插入新变体节**

用 Edit 工具，把下面这段（旧锚点）：

```
### 退化
- 当前环境无子 agent 工具时，退化为顺序逐条解读，并在报告注明"未启用并行"。

---

## 反例（不要这样做）
```

替换为（旧锚点 + 新节 + 分隔线 + 反例标题）：

````
### 退化
- 当前环境无子 agent 工具时，退化为顺序逐条解读，并在报告注明"未启用并行"。

---

## 变体：按报告章节并行起草（深度档提速）

> 前两种并行解决"采集"的并行（按模块 / 按扩展条目）；本变体解决**深度档"撰写"的并行**——把描述性章节拆给子 agent 并行起草，气脉章节主 agent 亲自写，并叠加分阶段流式输出。目标是**同时**压低墙钟和给出进度感。

### 何时启用

同时满足才启用：
- 输出深度 = **深度档**（标准 / 快速档不适用——报告短，并行不划算）；
- 当前环境有子 agent 工具；
- 项目**够大**（沿用本文件开头「何时启用并行」的阈值：顶层模块 >10 / 源文件 >500 / 一次写完会超过单次输出能力）。

不满足就退化为主 agent 串行写（见末尾「退化」）。

### 章节分工

深度档「一页纸概览 + 10 章」按"是否需要全局视角"分两类：

**🔒 主 agent 亲自写**（控气脉，拆了必丢信息）：
- 一页纸概览（含 ASCII 架构图）—— 需全局视角
- 第 5 章 端到端代表性流程 —— 气脉所在，本文件已定"端到端绝不切分"
- 第 9 章 综合评价 / 亮点 —— 基于其他章节的事实，必须最后写
- 第 10 章 未搞清楚 —— 汇总各子 agent 上报的盲区

**🔓 子 agent 并行起草**（描述性、对应局部证据）：
- 第 1 章定位功能、第 2 章整体架构、第 3 章技术栈、第 4 章代码结构、第 6 章配置运行、第 7 章工程质量、第 8 章专项画像 / 场景表

> **第 8 章的特例**：当第 8 章命中 g 类且扩展条目较多（会触发上一节「按扩展条目并行」）时，第 8 章改由主 agent 直接走那条路径（派画像子 agent + 自己画装配图），**不要再套一层 chapter-drafter**，避免两个并行机制嵌套。无论哪种方式，**g 类装配图始终主 agent 自己画**。

### 编排时间线

```
① 采集证据（大项目沿用「按模块并行采集」；中等项目主 agent 自己采）
        ↓
② 主 agent 立刻输出「一页纸概览初版 + 目录地图」→ 主动停一下
        ↓
③ 并行（提速核心）：
   ├─ 主 agent：亲自追第 5 章端到端流程
   └─ 子 agents：并行起草 🔓 那 7 章
        ↓
④ 章节陆续返回 → 主 agent 逐章聚合、统一术语、消冲突、跨章核对
   每完成一批 → 推送用户
        ↓
⑤ 主 agent 收尾：写第 9 章、第 10 章，校正概览的架构图
        ↓
⑥ 自检 → 问保存
```

**提速**来自 7 章并行 + 主 agent 追端到端与子 agent 起草重叠；**进度感**来自概览先出 + 边就绪边推。drafter 派发沿用"一批不超过 5~6 个、同一条消息内发出才真并行"——7 章可分两批。

### 给子 agent 的产出要求（chapter-drafter 派活模板）

与前两种派活的关键区别：**它返回成稿章节，不是简报**。

```
你是项目调研助手。请起草调研报告的【第 X 章：{{章标题}}】，
直接返回该章的中文 Markdown 成稿（主 agent 会聚合，不要写别的章）。

【项目根目录】{{绝对路径}}
【证据摘要（导航用，不是全部真相）】
  - 一句话定义 / 技术栈速记
  - 目录地图 + 顶层模块清单（带路径）
  - 入口位置、依赖清单要点
【本章骨架】{{从 template-deep.md 摘出的该章子标题结构}}

【产出要求】
  - 按本章骨架的子标题逐项填，产出成稿（不是简报）
  - 证据摘要不足处，回到源码核实并深化——不准只转写摘要
  - 每个论断带 `path:line`；不凭名字 / README 猜
  - 区分「不适用（原因）」与「未搞清楚（原因）」
  - 中文；篇幅按深度档该章应有的详尽度，不硬撑不敷衍
【必填】本章「未搞清楚」清单（汇给主 agent 第 10 章）
```

**一份共用证据摘要发给所有 drafter**（省得各自重新发现项目结构）；具体源码核实各 drafter 自做——硬约束要求每个论断带 `path:line`，不准只转写摘要。

### 主 agent 聚合职责

沿用本文件「聚合时要做的事」5 条，并额外做：
- **跨章一致性核对**：第 2 章架构的模块名 / 职责须与第 4 章代码结构、第 8 章专项一致；第 3 章技术栈不得与第 6 章配置打架。读每章时核对，冲突自己回源码定夺，不留给读者。
- **合并各章「未搞清楚」** → 第 10 章；**端到端流程（第 5 章）主 agent 自己追**，不外包。

### 流式节奏

沿用本文件「分阶段输出节奏」：概览 + 目录地图先出 → **主动停一下**给用户调整关注点 / 排除章节 → 之后每完成一批章节同步一次 → 最后聚合完整版 → 自检 → 问保存。

### 退化

- 无子 agent 工具 / 项目偏小 → 主 agent 串行写，但仍**保留流式**（概览先出 + 边写边推），报告注明"未启用章节并行"。
- 某章 drafter 失败或质量明显不足 → 主 agent 自己补写该章。

---

## 反例（不要这样做）
````

- [ ] **Step 2: 验证新节落位且层级正确**

Run:
```bash
grep -n "^## 变体：按报告章节并行起草" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/parallel-strategy.md
grep -n "^## " /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/parallel-strategy.md
```
Expected: 第一条命中新节标题；第二条显示章节顺序为 …「## 变体：按扩展条目并行」→「## 变体：按报告章节并行起草（深度档提速）」→「## 反例（不要这样做）」，新节夹在两者之间。

- [ ] **Step 3: 验证关键子标题齐全**

Run:
```bash
grep -nE "^### (何时启用|章节分工|编排时间线|给子 agent 的产出要求|主 agent 聚合职责|流式节奏|退化)$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/parallel-strategy.md
```
Expected: 至少出现新节内的 7 个子标题（其中「何时启用」「退化」会与既有节重名，属正常，确认新节范围内都在即可）。

- [ ] **Step 4: 提交（先与用户确认）**

```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add codebase-analyzer/references/parallel-strategy.md
git commit -m "并行策略新增按报告章节并行起草变体（深度档提速）"
```

---

## Task 2: `SKILL.md` 四处串联

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md`（第 115 / 143 / 169 / 200 行四处锚点）

- [ ] **Step 1: 第 4 步末尾追加深度档提速提示**

用 Edit 工具，把：

```
调研每个章节时的具体追问点见 [references/investigation-checklist.md](references/investigation-checklist.md)。第 2 步识别出的项目类型专项分析，写入模板里的"项目类型专项分析"章节（快速概览档可省略此章）。
```

替换为：

```
调研每个章节时的具体追问点见 [references/investigation-checklist.md](references/investigation-checklist.md)。第 2 步识别出的项目类型专项分析，写入模板里的"项目类型专项分析"章节（快速概览档可省略此章）。

> **深度档 + 大项目提速**：深度报告档调研大项目时，可把描述性章节（第 1/2/3/4/6/7/8 章）拆给子 agent 并行起草、气脉章节（一页纸概览与第 5/9/10 章）主 agent 亲自写，并分阶段流式输出，缩短撰写墙钟、给出进度感。详见 [references/parallel-strategy.md](references/parallel-strategy.md) 的「按报告章节并行起草」。
```

- [ ] **Step 2: 第 5 步 🔴 深度档自检新增一条**

用 Edit 工具，把：

```
- [ ] 若命中 **Claude Code 插件 / 扩展**：是否**逐条画像 + 画了整体装配图**？条目多时是否用了并行（或注明未启用）？
```

替换为：

```
- [ ] 若命中 **Claude Code 插件 / 扩展**：是否**逐条画像 + 画了整体装配图**？条目多时是否用了并行（或注明未启用）？
- [ ] 若启用了**按报告章节并行起草**：是否做了逐章聚合 / 统一术语 / **跨章一致性核对**？一页纸概览是否先出、章节是否边就绪边推？无子 agent 工具或项目偏小时是否退化为串行并注明"未启用章节并行"？
```

- [ ] **Step 3: 大项目策略「聚合」步追加一句**

用 Edit 工具，把：

```
3. **聚合**：等子 agent 返回后，由你统一按报告模板拼装，并消除模块间冲突 / 重复 / 不一致。拼装的详尽程度**按选定的输出深度档**决定（深度报告写满全部章节，标准调研抓主干），阶段 1 的概览只是过渡。
```

替换为：

```
3. **聚合**：等子 agent 返回后，由你统一按报告模板拼装，并消除模块间冲突 / 重复 / 不一致。拼装的详尽程度**按选定的输出深度档**决定（深度报告写满全部章节，标准调研抓主干），阶段 1 的概览只是过渡。深度档还可在此基础上**按报告章节并行起草**（描述性章节派子 agent、气脉章节主 agent 自己写），详见 [references/parallel-strategy.md](references/parallel-strategy.md) 的「按报告章节并行起草」。
```

- [ ] **Step 4: 相关参考区同步变体清单**

用 Edit 工具，把：

```
- [references/parallel-strategy.md](references/parallel-strategy.md) —— 大项目分阶段 / 并行调研策略（含"按扩展条目并行"变体）
```

替换为：

```
- [references/parallel-strategy.md](references/parallel-strategy.md) —— 大项目分阶段 / 并行调研策略（含"按扩展条目并行""按报告章节并行起草"两个变体）
```

- [ ] **Step 5: 验证四处都落位**

Run:
```bash
grep -nc "按报告章节并行起草" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md
```
Expected: `4`（第 4 步提示、深度档自检、大项目策略、相关参考各一处）。

- [ ] **Step 6: 提交（先与用户确认）**

```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add codebase-analyzer/SKILL.md
git commit -m "SKILL 串联按报告章节并行起草（第4步/自检/大项目策略/参考）"
```

---

## Task 3: `template-deep.md` 顶部加一句并行起草指引

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md`（第 11 行顶部说明区之后）

- [ ] **Step 1: 在顶部说明区追加指引**

用 Edit 工具，把：

```
> 二者不要混用。对于**条件章节**（如 2.6 外部系统、3.4 部署基础设施、6.5 可观测性、7.5 认证与安全），若与项目无关，一行写明"不适用（原因）"即可，不必硬撑子标题和占位内容。
```

替换为：

```
> 二者不要混用。对于**条件章节**（如 2.6 外部系统、3.4 部署基础设施、6.5 可观测性、7.5 认证与安全），若与项目无关，一行写明"不适用（原因）"即可，不必硬撑子标题和占位内容。
>
> **深度档大项目提速**：调研大项目时，描述性章节（第 1/2/3/4/6/7/8 章）可拆给子 agent 并行起草，一页纸概览与第 5/9/10 章由主 agent 亲自写，并分阶段流式输出——详见 [parallel-strategy.md](parallel-strategy.md) 的「按报告章节并行起草」。**本模板的章节结构、顺序、层级不变。**
```

- [ ] **Step 2: 验证指引已加且骨架未动**

Run:
```bash
grep -n "深度档大项目提速" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
grep -cE "^## " /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
```
Expected: 第一条命中新指引；第二条返回的一级章节数与改动前一致（确认只加了说明、没动章节骨架）。

- [ ] **Step 3: 提交（先与用户确认）**

```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add codebase-analyzer/references/template-deep.md
git commit -m "深度模板顶部加按章节并行起草指引（骨架不动）"
```

---

## Task 4: 整体一致性自检（对照 spec 验收标准）

**Files:**
- Read-only 核对：上述 3 个文件

- [ ] **Step 1: 逐条对照 spec 第 10 节验收标准**

打开 spec `docs/superpowers/specs/2026-06-04-codebase-analyzer-deep-report-speedup-design.md` 第 10 节，逐条确认：
1. `parallel-strategy.md` 新节覆盖门槛 / 章节分工 / 时间线 / 派活模板 / 聚合 / 流式 / 退化 —— 用 Task 1 Step 2~3 的 grep 结果核对。
2. `SKILL.md` 四处串到 —— 用 Task 2 Step 5 的 `grep -nc`（应为 4）核对。
3. `template-deep.md` 有指引、骨架未动 —— 用 Task 3 Step 2 核对。
4. 退化路径明确（无工具 / 太小 → 串行 + 流式 + 注明；单章失败 → 主 agent 补写）—— 阅读新节「退化」确认。
5. 正交：仅深度档启用 —— 阅读新节「何时启用」与 `template-deep` 指引确认未涉及 quick / standard。
6. 硬约束（`path:line` / 不凭名字猜 / 区分不适用·未搞清楚）在派活模板里 —— 阅读派活模板确认。
7. 第 8 章衔接边界（§3.3）写清、两个并行机制不嵌套 —— 阅读章节分工的「第 8 章的特例」确认。

- [ ] **Step 2: 交叉引用可达性核对**

Run:
```bash
grep -rn "按报告章节并行起草" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/
```
Expected: 出现在 `parallel-strategy.md`（定义处，标题）、`SKILL.md`（≥4 处引用）、`template-deep.md`（1 处引用）。确认所有指向「按报告章节并行起草」的链接都能落到 `parallel-strategy.md` 的真实标题（无悬空引用）。

- [ ] **Step 3: 若发现缺漏或不一致，修复并提交（先与用户确认）**

修复后：
```bash
cd /Users/chenjinfan/Project/codebase-analyzer
git add -A
git commit -m "深度报告章节并行：一致性修订"
```
若 Step 1~2 全部通过、无需修复，则跳过本步。

---

## Self-Review（计划作者已执行）

**1. Spec coverage（spec 各节 → 计划任务映射）：**
- spec §3 章节分工 → Task 1 新节「章节分工」+ Task 3 模板指引 ✓
- spec §4 编排时间线 → Task 1 新节「编排时间线」✓
- spec §5 启用门槛与退化 → Task 1 新节「何时启用」「退化」✓
- spec §6 派活模板 → Task 1 新节「给子 agent 的产出要求」✓
- spec §7 聚合纪律（含跨章核对）→ Task 1 新节「主 agent 聚合职责」+ Task 2 自检条 ✓
- spec §8 流式节奏 → Task 1 新节「流式节奏」✓
- spec §9.1 parallel-strategy → Task 1；§9.2 SKILL 四处 → Task 2；§9.3 template-deep → Task 3 ✓
- spec §10 验收 → Task 4 逐条核对 ✓
- spec §11 Non-goals（不新建文件 / 不动 quick·standard / 不动深度档骨架 / 不拆第 5 章）→ 计划只改 3 个现有文件、模板骨架不动、未涉及其他档、章节分工把第 5 章列为 🔒 ✓

**2. Placeholder scan:** 新节正文无 TBD / TODO；派活模板里的 `{{…}}` 是有意的 prompt 占位（与既有两份派活模板风格一致），非计划缺口。✓

**3. Type/措辞 consistency:** 全程统一用「按报告章节并行起草」「chapter-drafter」「🔒/🔓」「气脉章节」；SKILL 自检条、模板指引、新节标题措辞一致。✓

---

## Execution Handoff

计划已保存到 `docs/superpowers/plans/2026-06-04-codebase-analyzer-deep-report-speedup.md`。两种执行方式：

1. **Subagent-Driven（推荐）** —— 每个任务派一个全新 subagent，任务间我来 review，迭代快。
2. **Inline Execution** —— 在本会话内用 executing-plans 批量执行、设检查点 review。

> 注：本计划只改 3 个文档文件、彼此有引用依赖，且 git commit 需你确认——**Inline Execution 在这里其实更顺手**（无需跨 subagent 传递文件状态）。但你定。

选哪种？
