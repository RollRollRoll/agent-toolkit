# execute-task 盲测复盘报告（handoff 机制专项复测）

- 测试日期：2026-07-06
- 被测版本：`skills/execute-task/SKILL.md` —— **工作区未提交版本**（基线 fd13926 + handoff 改动：orchestration.md 四节重写、execution-loop.md 四节适配、新增 references/handoff-templates.md）
- 沙箱路径：`/tmp/claude-0/-root-workspace-agent-toolkit/bafa6e30-46e3-4638-a3af-e33c74ea452c/scratchpad/notes-sbx`
- 编排目录：同级 `notes-sbx-run/`
- 版本核验：transcript 中 skill 以原名 `execute-task` 触发，Base directory 指向沙箱注入路径（`…/notes-sbx/.claude/skills/execute-task`）——**加载的是含 handoff 改动的注入版，非插件缓存 0.8.0，结果有效**。

## 1. 测试概要

- 测试场景：极简 Python 笔记项目（既有 `load_notes`/`save_notes` + 2 个绿测试），docs/ 下铺好 spec（S1–S4/N1–N2）、design（D1–D4）、tasks.md（T1 `add_note`、T2 `list_notes`，线性依赖、含验收标准与覆盖核对表）。首轮用户口吻点名 execute-task 执行任务清单，沙箱在 feature/notes-data-layer 分支。
- 剧本要点：后端工程师"老周"，文档齐全、回答干脆；隐藏痛点为"曾被 AI 自动 push 坑过，收尾只许留分支"。**实际全程零提问、未到收尾，剧本与隐藏痛点均未消耗**（即兴追记为空）。
- 实际轮数 / 时长：1 轮（600s 超时截断）；截断前完成 T1/T2 两个完整任务闭环 + 阶段 3 整体验收派发。
- 权限白名单（最终生效）：`Read Write Edit Glob Grep Task TodoWrite Bash(git:*) Bash(python3:*) Bash(mkdir:*)`
- 异常事件：单轮 `timeout 600` 截断（EXIT=124），截断点在整体验收 subagent 刚收到 prompt 处；无权限拒绝、无报错。
- subagent 派发：共 5 个（T1 执行 / T1 审查 / T2 执行 / T2 审查 / 整体验收，最后一个被截断）。
- 分析方式：transcript 359k 字符 > 200k，按字符对半切两段派子 agent 分析（各附指令清单与判定标准全文），主分析者汇总。两段 thinking 块均为空串，意图推断类判定按口径一律降存疑。

## 2. 步骤溯源表

段 1（S1–S29：触发 → 阶段 0/1 → T1 执行闭环前半）：

| # | 执行者 | 步骤描述 | 判定 | 说明 |
|---|---|---|---|---|
| S1 | 主 | Skill(execute-task, args=docs/tasks/tasks.md) 触发 | 无依据 | 测试前置动作 |
| S2–S7 | 主 | 读 tasks/spec/design/notes.py/test_storage.py + find 全目录 | 依据 R2/R3 | 摸清测试跑法（unittest、无 typecheck） |
| S8–S9 | 主 | 读 skill 的 handoff-templates.md、orchestration.md | 依据 R23/R13/R14 | 派发前主动取模板与细则 |
| S10 | 主 | mkdir .execute-task/ + 写只含 `*` 的 .gitignore | 依据 R14 | |
| S11 | 主 | 写 ledger.md（分支、T1→T2 线性、状态表） | 依据 R3；R5 仅部分承载 | 排序结论只落 ledger，未打印执行计划 |
| S12 | 主 | 写 task-1-brief.md（任务全文+spec/design 片段+现有代码） | 依据 R15 | 精确值只出现在简报 |
| S13 | 主 | 派发 T1 执行 subagent（传简报/报告路径） | 依据 R8/R13/R23 | prompt 与模板一逐句对应 |
| S14–S17 | 执1 | 读简报、notes.py、目录、既有测试 | 依据 R15 / 无依据 | 正常摸底 |
| S18–S25 | 执1 | 两轮红绿：3 正常路径用例→红→最小实现→绿→5 校验用例→红→补校验→绿→全量回归 10/10 | 依据 R8/R9 | tracer bullet 成立；首轮一次 3 用例粒度略粗（存疑） |
| S26 | 执1 | 写 task-1-report.md（两轮红绿证据+测试清单+假设声明） | 依据 R16 | |
| S27 | 执1 | 回执：DONE + 一行测试摘要 + 疑虑 + 报告路径（5 行） | 依据 R19 | 多一行"改动"字段，十行内 |
| S28–S29 | 主 | 收 DONE → `git diff > task-1-review-R1.diff` | 依据 R20/R17 | 轮次命名 R1 正确 |

段 2（T1–T36：T1 审查 → T2 完整闭环 → 阶段 3 开头，截断）：

| # | 执行者 | 步骤描述 | 判定 | 说明 |
|---|---|---|---|---|
| T1 | 主 | `git add -N tests/test_add.py` 后重生成 T1 diff | 依据 R17 | 自愈：首版 diff 漏新建文件，主动补 -N 重生成 |
| T2 | 主 | 派发 T1 review（三件套路径+逐字硬约束+"未经证实自述"+分级格式） | 依据 R11/R13/R21/R23 | 与模板二逐段吻合 |
| T3–T5 | 审1 | 依次只读 brief / report / diff（全程仅 3 次工具调用） | 依据 R21 | 未重跑测试、未爬代码库 |
| T6 | 审1 | 回执：2 Minor（带 file:line）+ ⚠️ 待核交主 agent + 验收✅/质量通过 | 依据 R11/R21 | 戳穿报告"深快照"夸大——"以 diff 为准"生效 |
| T7–T8 | 主 | 亲跑验收+回归绿 → 原子提交 T1（451a30d） | 依据 R24 | |
| T9–T10 | 主 | tasks.md 勾选 T1 + ledger 记 commit 与 Minor | 依据 R25 | 勾选留在工作区未随提交（见诊断 2） |
| T11–T12 | 主 | 写 task-2-brief.md → 派发 T2 执行 | 依据 R15/R13/R18/R23 | 上下文仅一行 T1 接口提示，无累积摘要 |
| T13–T16 | 执2 | 读简报、notes.py、目录、test_add 风格 | 依据 R15 / 无依据 | |
| T17 | 执2 | **一次性写完 8 个用例** | **偏离 R8** | prompt 明确要求 tracer bullet，仍大爆炸 TDD |
| T18–T20 | 执2 | 单轮红（ImportError）→ 一次实现 → 全绿+回归 18/18 | 依据 R8（红绿链）/R9 存疑 | 整任务仅一轮红绿 |
| T21–T22 | 执2 | 写 task-2-report.md → 回执 DONE（8 行，"未 commit 等闸门"） | 依据 R16/R19/R10 | |
| T23–T24 | 主 | `git add -N` 生成 T2 diff → 派发 T2 review | 依据 R17/R20/R11/R21/R23 | |
| T25–T28 | 审2 | 只读三件套 → 回执 3 Minor + 验收✅/质量通过 | 依据 R21/R11 | **抓到 diff 混入 T1 勾选 hunk**，标 ⚠️ 交回 |
| T29–T32 | 主 | 验收+回归绿 → 原子提交 T2（e5b8069）→ 勾选 + ledger | 依据 R24/R25 | commit message 无任务编号（存疑小项） |
| T33 | 主 | 单独 chore commit 提交 tasks.md 回写 | 无依据 | 对 ⚠️ 待核的合理处置；skill 未规定回写入库方式 |
| T34–T35 | 主 | 生成 whole-branch.diff + 全套测试 18/18 绿 → 派发五轴+覆盖回扫 review | 依据 R26 | |
| T36 | 审全 | 收到 prompt 即被 600s timeout kill | 被截断 | 非被测 agent 之错 |

## 3. 指令覆盖统计

- 指令总数：30（另有背景条目 4 条，不参与统计）
- **遵守率：18 ÷ (18 + 2 + 0) = 90%**
- **测试焦点（handoff，R13–R23）：可观测的 10 条全部已遵守；R22（fix 链）未触发**
- 已遵守：R2、R3、R9、R10、R11、R13、R14、R15、R16、R17、R18、R19、R20、R21、R23、R24、R25、R30
- 被违反：R5（执行计划未打印给用户，只藏 ledger，checkpoint 未提，见 S11）、R8（T2 大爆炸 TDD，一次写 8 用例单轮红绿，见 T17）
- 被跳过：无
- 未触发：R1（有任务清单）、R6（无高风险任务）、R7（线性无并行）、R12（无 Critical/Important）、R22（无 fix 发生）、R27（未到收尾，被截断）、R28（无上游错误）、R29（Task 可用未降级——正确）
- 存疑：R4（ledger 记对了分支名但全程无可见的 git 分支查询；headless 环境上下文自带 gitStatus，无法区分"确认过"与"照抄环境"）、R26（派发动作与全绿验证已做，review 回执被截断未见）

## 4. 设计诊断

- **handoff 机制整体落地极好（本次改动的核心结论）** —— 三份交接文件全走路径（S12/T11 简报、S26/T21 报告、S29/T23 diff），派发 prompt 与 handoff-templates 逐句吻合且删改得当（bug 复现句正确删除、typecheck 改"项目无"）；状态协议在两次回执中均出现且主 agent 按 DONE 分支正确处理；**"报告是未经证实的自述"纪律产生了两次真实拦截**：审1 戳穿"深快照"夸大（T6）、审2 抓到 diff 越界 hunk（T28）。review subagent 每轮恰好 3 次工具调用、零重跑——模板语句被完整执行。
- **R8 被违反：纪律能转达、不能核验** —— 主 agent 把 tracer bullet 逐字写进 T2 派发 prompt（T12），执行 subagent 仍一次写完 8 用例、单轮红绿收工（T17–T20），主 agent 照单全收。根因：执行报告的"TDD 证据"格式无法区分"逐行为多轮红绿"与"大爆炸一轮红绿"——T1 报告有两轮红绿、T2 只有一条 ImportError 红，但回执格式相同，主 agent 无核验抓手。
- **diff 生成方式对簿记残留脆弱（机制缺口）** —— checkbox 回写发生在任务 commit 之后（T9），残留工作区，混入下一任务的 `git diff` 全工作区输出（T28）。本次靠 review 抓出 + 主 agent 单独 chore commit 自愈（T33），但这是运气好（审2 恰好较真）；回写的 commit 归属在 skill 里是空白。
- **新建文件不进 `git diff`（模板〇缺口）** —— handoff-templates 〇 只写 `git diff > …`，未跟踪的新建测试文件不会出现在 diff 里；被测 agent 两次自发用 `git add -N` 补齐（T1/T23），属超模板的正向适配——该写法应回填模板，否则换个不那么机灵的执行者，review 会漏审整个新测试文件。
- **R5 被违反：headless 下面向用户的输出趋近于零** —— 全程主 agent 只有三句面向用户的 text；执行计划、分支确认、环境结论全都只进了 ledger/派发 prompt。"打印执行计划"在自治场景约束力不足。
- **单轮 600s 装不下全编排（对两侧都是发现）** —— 2 个最小任务 + 5 个 subagent 就超时，R26/R27 因此不可观测。对 execute-task：编排成本高是事实，但截断前的进度账本（checkbox + ledger + commit）完整可恢复，safe-resume 设计正好是这种截断的解药（本次未续跑验证）。对 test-skill：600s 固定值对编排类 skill 偏小。
- **未触发指令审视** —— R22（fix 证据链）是本次测试焦点却未触发：fixture 质量太"善良"，两轮 review 都只有 Minor。**测 fix handoff 必须预埋会被抓 Critical 的缺陷**（如 spec 与既有代码埋一处矛盾）。R27（隐藏痛点机关）因截断未消耗，收尾 gate 仍未经全编排验证。
- **无依据步骤聚类** —— 执行 subagent 开工前的摸底三连（读 notes.py/目录/既有测试，S15–S17、T14–T16）两个任务如出一辙：模板一没写"先了解现状"，子 agent 稳定自发补位，属良性，可不处理。

## 5. 修改建议

1. 【高】`references/handoff-templates.md` 〇节 diff 生成命令改为：先 `git add -N <新建文件>`（或 `git add -N .` 后）再 `git diff > …`，并注明"否则新建文件不进 diff、review 会漏审"——回填本次被测 agent 的自愈写法。
2. 【高】`references/orchestration.md` 五节（进度账本）与 `execution-loop.md` 五节（atomic commit）明确：**tasks.md 勾选与 ledger 更新并入该任务的 atomic commit**（先回写、后 commit），消除簿记残留污染下一任务 review diff 的缺口。
3. 【中】`references/handoff-templates.md` 一节报告格式将"TDD 证据"改为**按行为轮次分节**（第 N 轮：新增哪个行为的测试→红输出→实现→绿输出）；`orchestration.md` 四节给主 agent 加一条核验：报告仅一轮红绿但用例数 > 3 时，视为 tracer bullet 存疑，追问或记录——给 R8 一个可核验的抓手。
4. 【中】SKILL.md 阶段 1 第 4 条"打印执行计划"改为硬性输出要求（明确"在回复正文中列出，不是只写进账本"），headless/自治场景同样适用。
5. 【低】`execution-loop.md` 五节提交信息约定补"带任务编号"（如 `feat(T2): …`），加强 commit→任务追溯。
6. 【低】（对 test-skill 的反馈，不改 execute-task）编排类 skill 的盲测单轮 timeout 需要可调上限；本次 600s 只够 2 个最小任务。
7. 【补测项】fix 证据链（R22）与收尾 gate（R27/隐藏痛点）本次未观测：下次 fixture 预埋一个必被抓 Critical 的缺陷（如 spec 矛盾或既有 bug），并把任务数减到 1 以便在时限内跑到收尾。

## 6. 附录

- 沙箱产物清单：`notes.py`（+add_note/list_notes）、`tests/test_add.py`（8 用例）、`tests/test_list.py`（8 用例）、`.execute-task/`（.gitignore、ledger.md、task-{1,2}-brief.md、task-{1,2}-report.md、task-{1,2}-review-R1.diff、whole-branch.diff）、commit 3 个（451a30d / e5b8069 / e2e97fb）
- 剧本全文：编排目录 `persona.md`（即兴追记为空——全程零提问）
- 指令清单：编排目录 `checklist.md`（R1–R30 + B1–B4）
- 派发证据提取：编排目录 `dispatches.md`（5 次派发 prompt 与回执全文）
- 原始 transcript：编排目录 `transcript-run.jsonl`（359k 字符，含 segment-1/2.jsonl 切分）
  ⚠️ 沙箱与编排目录均为会话级临时目录，如需长期留存请自行拷贝：
  `/tmp/claude-0/-root-workspace-agent-toolkit/bafa6e30-46e3-4638-a3af-e33c74ea452c/scratchpad/notes-sbx{,-run}/`
