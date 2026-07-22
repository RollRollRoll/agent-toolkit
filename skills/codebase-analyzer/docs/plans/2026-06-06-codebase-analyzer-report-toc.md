# 报告内目录（TOC）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 codebase-analyzer 的**标准档 / 深度档**调研报告，在「一页纸概览」前加一段**预置好、可点击跳转的章节目录（## 目录）**，快速概览档不加。

**Architecture:** 纯文档 / prompt 工程改动。核心手法：目录只列一级 `##` 章节，而一级章节标题在模板里是**固定文本**，所以目录段（含已按 GitHub GFM 规则算好的锚点）**预置进 `template-standard.md` 与 `template-deep.md`**——Claude 产报告时**照抄即可、不动态生成锚点**，从根上消除"锚点写错"风险。`SKILL.md` 第 5 步自检「标准调研档」加一条 TOC 核对（深度档作为标准档超集自动继承）。只改 3 个现有文件 + 同步到 `~/.claude/skills` 安装副本；不新建文件、不改任何章节骨架 / 标题。

**Tech Stack:** Markdown skill 文件（无代码、无测试框架）。本计划的"验证"= `grep` / 阅读确认改动落位 + 对照 spec §5 验收标准核对，**不是**单元测试。

**关联 spec:** `docs/superpowers/specs/2026-06-06-codebase-analyzer-report-toc-design.md`

> **提交约定**：本项目 `git commit` 需用户明确确认。计划中的 commit 步骤在执行时先与用户确认再提交。

**工作目录约定:** skill 文件在 `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/`，git 仓库根在 `/Users/chenjinfan/Project/codebase-analyzer/`；安装副本在 `~/.claude/skills/codebase-analyzer/`。下文命令均用绝对路径，避免 `cd`。

---

## File Structure

| 文件 | 职责 | 本次改动 |
|---|---|---|
| `references/template-standard.md` | 标准档报告骨架 | 在 `## 一页纸概览` 前插入 10 条目录段 |
| `references/template-deep.md` | 深度档报告骨架 | 在 `## 一页纸概览` 前插入 12 条目录段（含附录 A） |
| `SKILL.md` | 主流程 | 第 5 步自检「🟡 标准调研档」加 1 条 TOC 核对 |
| `references/template-quick.md` | 快速档骨架 | **不改**（快速档不加目录） |
| `references/parallel-strategy.md` | 大项目并行策略 | **不改**（目录段是模板固定内容，主 agent 聚合时照模板带上即可，spec §4.4 已定"倾向不改"） |

执行顺序：Task 1（standard 模板）→ Task 2（deep 模板）→ Task 3（SKILL 自检）→ Task 4（整体一致性自检）→ Task 5（提交 + 同步到安装副本）。先逐文件改 + 单文件验证，再整体自检，最后一次性提交并同步。

---

## Task 1: `template-standard.md` 插入 10 条目录段

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md`（元信息行与 `## 一页纸概览` 之间）

- [ ] **Step 1: 在元信息与一页纸概览之间插入目录段**

用 Edit 工具，把下面这段（标准档元信息 + 分隔 + 概览标题）：

````
> **调研对象**：`{{绝对路径或仓库地址}}` ｜ **时间**：{{YYYY-MM-DD}} ｜ **读者**：对项目不熟悉的工程师

---

## 一页纸概览
````

替换为（中间插入 `## 目录`）：

````
> **调研对象**：`{{绝对路径或仓库地址}}` ｜ **时间**：{{YYYY-MM-DD}} ｜ **读者**：对项目不熟悉的工程师

---

## 目录

- [一页纸概览](#一页纸概览)
- [1. 项目定位与功能](#1-项目定位与功能)
- [2. 整体架构](#2-整体架构)
- [3. 技术栈](#3-技术栈)
- [4. 代码结构与核心实现](#4-代码结构与核心实现)
- [5. 端到端代表性流程](#5-端到端代表性流程)
- [6. 配置、依赖与运行](#6-配置依赖与运行)
- [7. 项目类型专项分析](#7-项目类型专项分析)
- [8. 综合评价](#8-综合评价)
- [9. 未搞清楚 / 假设 / 已知问题](#9-未搞清楚--假设--已知问题)

---

## 一页纸概览
````

> 该 old_string（"调研对象…工程师" + `---` + `## 一页纸概览`）在文件中唯一匹配。

- [ ] **Step 2: 验证目录段落位、锚点正确、章节标题未被改动**

Run:
```bash
grep -nc "^## 目录$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md
grep -c "(#9-未搞清楚--假设--已知问题)" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md
grep -c "(#6-配置依赖与运行)" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md
grep -nc "^## 一页纸概览$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md
```
Expected:
- 第 1 条 = `1`（目录段已插入）
- 第 2 条 = `1`（多标点锚点 `--` 正确）
- 第 3 条 = `1`（顿号 `、` 已从锚点删除）
- 第 4 条 = `1`（概览标题仍在、未被破坏）

---

## Task 2: `template-deep.md` 插入 12 条目录段

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md`（元信息行与 `## 一页纸概览` 之间）

> **附录无死链确认**：深度档第 ~378 行已有 `## 附录 A：调研路径回放（可选）`，且模板开头要求"每个章节都保留标题、不省略"。目录里的 `附录 A` 链接指向这个已存在的标题，不会悬空。本 Task 只新增目录段，不动附录标题。

- [ ] **Step 1: 在元信息与一页纸概览之间插入目录段**

用 Edit 工具，把下面这段（深度档元信息末行 + 分隔 + 概览标题）：

````
> **报告读者**：对项目不熟悉的工程师

---

## 一页纸概览
````

替换为（中间插入 `## 目录`）：

````
> **报告读者**：对项目不熟悉的工程师

---

## 目录

- [一页纸概览](#一页纸概览)
- [1. 项目定位与功能](#1-项目定位与功能)
- [2. 整体架构](#2-整体架构)
- [3. 技术栈](#3-技术栈)
- [4. 代码结构与核心实现](#4-代码结构与核心实现)
- [5. 端到端代表性流程](#5-端到端代表性流程)
- [6. 配置、依赖与运行](#6-配置依赖与运行)
- [7. 工程实践与质量](#7-工程实践与质量)
- [8. 项目类型专项分析](#8-项目类型专项分析)
- [9. 综合评价（亮点 / 适合度 / 二次开发）](#9-综合评价亮点--适合度--二次开发)
- [10. 未搞清楚的部分 / 假设 / 已知问题](#10-未搞清楚的部分--假设--已知问题)
- [附录 A：调研路径回放（可选）](#附录-a调研路径回放可选)

---

## 一页纸概览
````

> 该 old_string（"报告读者…工程师" + `---` + `## 一页纸概览`）在文件中唯一匹配。

- [ ] **Step 2: 验证目录段落位、两条硬锚点正确、附录链接不悬空**

Run:
```bash
grep -nc "^## 目录$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
grep -c "(#9-综合评价亮点--适合度--二次开发)" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
grep -c "(#附录-a调研路径回放可选)" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
grep -c "^## 附录 A：调研路径回放（可选）$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
```
Expected:
- 第 1 条 = `1`（目录段已插入）
- 第 2 条 = `1`（全角括号 + 双斜杠锚点正确）
- 第 3 条 = `1`（附录锚点正确）
- 第 4 条 = `1`（正文附录标题存在，目录链接不悬空）

---

## Task 3: `SKILL.md` 第 5 步自检加 1 条 TOC 核对

**Files:**
- Modify: `/Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md`（第 5 步自检「🟡 标准调研档」首条之后）

- [ ] **Step 1: 在「标准调研档」清单首条后插入 TOC 核对条**

用 Edit 工具，把：

````
**🟡 标准调研档**：
- [ ] 一页纸概览能让读者扫一眼抓住大局吗？
````

替换为：

````
**🟡 标准调研档**：
- [ ] 一页纸概览能让读者扫一眼抓住大局吗？
- [ ] 报告开头（一页纸概览前）放了「## 目录」章节目录吗？目录条目与各 ## 章节真实标题一一对应、可点击跳转？（这是 TOC，与第 4 章的"目录地图 / 项目目录树"不是一回事）
````

> 该 old_string（"🟡 标准调研档" + "一页纸概览能让读者扫一眼抓住大局吗？"）在文件中唯一匹配。深度档自检已含"标准档全部检查项是否也满足（深度档是标准档超集）"，故无需在深度档清单重复。

- [ ] **Step 2: 验证自检条落位、未误伤其他清单**

Run:
```bash
grep -c "「## 目录」章节目录" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md
grep -nc "^\*\*🟡 标准调研档\*\*：$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md
```
Expected:
- 第 1 条 = `1`（新自检条已加，且措辞与"目录地图"区分）
- 第 2 条 = `1`（标准调研档清单标题仍唯一、结构未乱）

---

## Task 4: 整体一致性自检（对照 spec §5 验收标准）

**Files:**
- Read-only 核对：上述 3 个改动文件 + `template-quick.md` + spec

- [ ] **Step 1: 逐条核对 spec §5 验收标准 1~7**

打开 spec `docs/superpowers/specs/2026-06-06-codebase-analyzer-report-toc-design.md` 第 5 节，逐条确认：
1. standard 概览前有 10 条目录、锚点对应"概览 + 1~9 章" —— 看 Task 1 改后结果。
2. deep 概览前有 12 条目录、含附录 A、锚点对应"概览 + 1~10 章 + 附录" —— 看 Task 2 改后结果。
3. quick 档不加目录 —— Step 2 grep 确认。
4. 目录只到一级 `##`、无二级小节 —— 目测两段目录无 `1.1/2.1` 等条目。
5. 显示文字 = 标题原文、锚点按 GitHub 规则 —— 目测目录项 `[标题原文](#锚点)` 一致。
6. SKILL 第 5 步「标准调研档」已加 TOC 核对条、与"目录地图"区分 —— 看 Task 3 改后结果。
7. 任何章节 `##` 标题文字未被改动 —— Step 3 grep 确认标题计数不变。

- [ ] **Step 2: 确认快速档未被波及**

Run:
```bash
grep -c "^## 目录$" /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-quick.md
```
Expected: `0`（快速档没有目录段）。

- [ ] **Step 3: 确认两模板的一级章节标题数量未变（只增目录、未动标题）**

Run:
```bash
grep -c "^## " /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md
grep -c "^## " /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md
```
Expected:
- standard = `11`（原 10 个 `##` 章节 + 新增的 `## 目录`）
- deep = `13`（原 12 个 `##` 章节 + 新增的 `## 目录`）

> 若数字不符（多删或多增），说明误改了章节标题，回到对应 Task 检查。

- [ ] **Step 4: 若发现缺漏或不一致，修复后重跑对应 Task 的验证**

仅当 Step 1~3 有不符时执行：回到对应 Task 用 Edit 修正，再重跑该 Task Step 2 的 grep。若全部通过则跳过本步。

---

## Task 5: 提交 + 同步到安装副本

**Files:**
- Git 提交：上述 3 个改动文件
- 同步：`~/.claude/skills/codebase-analyzer/`

- [ ] **Step 1: 提交三个文件（先与用户确认）**

```bash
git -C /Users/chenjinfan/Project/codebase-analyzer add \
  codebase-analyzer/references/template-standard.md \
  codebase-analyzer/references/template-deep.md \
  codebase-analyzer/SKILL.md
git -C /Users/chenjinfan/Project/codebase-analyzer commit -m "报告标准/深度档加可跳转章节目录（TOC）+ SKILL 自检同步"
git -C /Users/chenjinfan/Project/codebase-analyzer log -1 --oneline
```
Expected: 提交成功，`log -1` 显示该 commit。

- [ ] **Step 2: 确认安装副本路径存在**

Run:
```bash
ls ~/.claude/skills/codebase-analyzer/SKILL.md ~/.claude/skills/codebase-analyzer/references/
```
Expected: 列出 `SKILL.md` 与 `references/`（含 template-standard.md、template-deep.md）。若路径不存在，先与用户确认安装副本的真实位置再调整下一步。

- [ ] **Step 3: 同步三个文件到安装副本**

```bash
cp /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-standard.md ~/.claude/skills/codebase-analyzer/references/template-standard.md
cp /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/references/template-deep.md ~/.claude/skills/codebase-analyzer/references/template-deep.md
cp /Users/chenjinfan/Project/codebase-analyzer/codebase-analyzer/SKILL.md ~/.claude/skills/codebase-analyzer/SKILL.md
```

- [ ] **Step 4: 验证安装副本已同步**

Run:
```bash
grep -c "^## 目录$" ~/.claude/skills/codebase-analyzer/references/template-standard.md
grep -c "^## 目录$" ~/.claude/skills/codebase-analyzer/references/template-deep.md
grep -c "「## 目录」章节目录" ~/.claude/skills/codebase-analyzer/SKILL.md
```
Expected: 三条均为 `1`（安装副本与开发仓库一致）。

---

## Self-Review（计划作者已执行）

**1. Spec coverage（spec §5 验收标准 → 计划任务映射）：**
- §5.1 standard 10 条目录 + 锚点对应 → Task 1 Step 1/2 ✓
- §5.2 deep 12 条目录 + 附录 + 锚点对应 → Task 2 Step 1/2 ✓
- §5.3 quick 档不加 → Task 4 Step 2 ✓
- §5.4 只到一级 `##` → Task 1/2 目录段无二级条目 + Task 4 Step 1.4 ✓
- §5.5 显示文字=原文 / GitHub 锚点 → Task 1/2 目录段逐字预置 ✓
- §5.6 SKILL 自检加 TOC 核对 + 与"目录地图"区分 → Task 3 ✓
- §5.7 章节 `##` 标题未改 → Task 4 Step 3（`##` 计数 = 原数 + 1）✓
- §5.8 同步到 `~/.claude/skills` → Task 5 Step 2/3/4 ✓
- spec §6 Non-goals（不加快速档 / 不到二级 / 不改标题 / 不引入 HTML 锚点 / 不新建文件 / 不改骨架）→ 计划只新增目录段、改 3 现有文件、parallel-strategy 与 quick 明确不改 ✓

**2. Placeholder scan:** 各 old/new 文本块均为完整成稿，无 TBD / TODO；`{{绝对路径或仓库地址}}` `{{YYYY-MM-DD}}` 是模板原有的面向终端用户的占位（保持原样），非计划缺口。✓

**3. 锚点字符串 consistency（对应"type consistency"）：** 计划中每条目录项的锚点与 spec §3.2/§3.3 逐字一致；Task 验证里的 grep 字符串（`#9-未搞清楚--假设--已知问题`、`#9-综合评价亮点--适合度--二次开发`、`#附录-a调研路径回放可选` 等）与目录段中的锚点逐字对应；standard 第 8 章"综合评价"（无括号）与 deep 第 9 章"综合评价（…）"（有括号）、standard 第 9 章"未搞清楚 / 假设…"与 deep 第 10 章"未搞清楚的部分 / 假设…"的差异已分别处理，未串用。✓

---

## Execution Handoff

计划已保存到 `docs/superpowers/plans/2026-06-06-codebase-analyzer-report-toc.md`。两种执行方式：

1. **Subagent-Driven（推荐项）** —— 每个任务派一个全新 subagent，任务间我来 review，迭代快。
2. **Inline Execution** —— 在本会话内用 executing-plans 批量执行、设检查点 review。

> 注：本计划只改 3 个文档文件、彼此有交叉引用，且 git commit 需你确认——**Inline Execution 在这里更顺手**（无需跨 subagent 传递文件状态，改完连贯，锚点这类逐字精度也便于我直接把控）。但你定。

选哪种？
