# Retrospective report template

Write the whole report in Chinese, with all six sections, following this template. The fixed headings, field labels, table headers, and judgment labels below stay in Chinese exactly as written (English glosses are listed after the template). Placeholders in `<...>` and the example rows only show the format: replace them with Chinese content, and delete the example rows when writing.

```markdown
# <target skill> 盲测复盘报告

- 测试日期：YYYY-MM-DD
- 被测平台：<Claude Code | Codex>
- 被测版本：<SKILL.md path + git commit it is at (if in a repo)>
- 实际加载来源：<sandbox injection path; if it cannot be confirmed, state the evidence gap>
- 运行 ID：<run_id from run-config.json>
- 沙箱路径：<absolute path>
- 编排目录：<absolute path>

## 1. 测试概要

- 测试场景：<one paragraph>
- 剧本要点：<simulated user identity, real intent, hidden pain point (you may state them openly here)>
- 实际轮数 / 时长：<N turns, about M minutes>
- 执行边界：<Claude: tools + allowed_tools; Codex: sandbox_mode + approval_policy>
- 设置 / 扩展隔离：<Claude: setting_sources + strict MCP; Codex: isolated_home + ignore_user_config/rules + web_search; effect of managed policies>
- 异常事件：<timeouts / permission denials / errors; if none, write "无">

## 2. 步骤溯源表

| # | 轮次 | 步骤描述 | 判定 | 说明 |
|---|------|----------|------|------|
| 1 | 1 | Asks a clarifying question: "Who is this dashboard for?" | 依据 R3 | R3 requires asking about the audience first |
| 2 | 1 | Asks a second question in the same message | 偏离 R4 | R4 requires one question at a time |
| 3 | 2 | Reads notes.md in the sandbox | 无依据 | The skill does not ask to read existing files |

(One row per semantic step, covering all turns. For a `存疑` judgment, say so in the notes column and attach a quote.)

## 3. 指令覆盖统计

- 指令总数：n (plus m background items, not counted)
- 遵守率：已遵守 ÷（已遵守 + 被违反 + 被跳过）= XX%
- 已遵守：R1, R3, ...
- 被违反：R4 (asked three questions in one message, see step 2), ...
- 被跳过：R7 (the scenario applied but there was no corresponding action at any point), ...
- 未触发：R9 (the scenario never reached the applicability condition), ...
- 存疑：R12 (not enough transcript evidence, see step 18)

## 4. 设计诊断

(For each problem instruction, give a hypothesis for why it failed, citing steps and the original text:)

- **R4 被违反**: the instruction is buried in the middle of a long paragraph and is in tension with R3 "understand the requirements as soon as possible", so the agent put efficiency first.
- **R7 被跳过**: it is phrased as "consider doing X" rather than "must do X", so it is not binding enough.
- **未触发指令审视**: R9/R10 were not covered by the scenario and need another scenario to test; R11 is hard to trigger in any scenario and may be redundant.
- **无依据步骤聚类**: steps 3/8/15 all explore the project context on their own. The skill lacks an instruction like "understand the current state before starting", so the agent had to fill the gap.

## 5. 修改建议

(Order by priority, and phrase each one as a concrete edit to SKILL.md:)

1. 【高】Pull R4 out of the section 3 paragraph into its own numbered list item, and reword it as "must ask only one question at a time".
2. 【中】Add an instruction: list the existing relevant files before starting the task (basis: the cluster of no-basis steps).
3. 【低】Consider deleting R11 (decide after it stays untriggered across several scenarios).

## 6. 附录

- 沙箱产物清单：<file list>
- 剧本全文（含即兴追记附录）
- 指令清单：<orchestration dir>/checklist.md
- 原始 transcript：<orchestration dir>/transcript-run.jsonl
- stderr：<orchestration dir>/stderr.log
- 逐轮状态：<orchestration dir>/run-state.json
  ⚠️ 沙箱与编排目录都位于会话级临时空间，如需长期留存原始证据请自行拷贝。
```

## English glosses for the fixed Chinese text

- Title: `<target skill> 盲测复盘报告` = "<target skill> blind-test retrospective report".
- Header fields: 测试日期 = test date; 被测平台 = platform under test; 被测版本 = version under test; 实际加载来源 = actual load source; 运行 ID = run ID; 沙箱路径 = sandbox path; 编排目录 = orchestration directory.
- Section headings: 1. 测试概要 = test summary; 2. 步骤溯源表 = step traceability table; 3. 指令覆盖统计 = instruction coverage statistics; 4. 设计诊断 = design diagnosis; 5. 修改建议 = suggested changes; 6. 附录 = appendix.
- Section 1 fields: 测试场景 = test scenario; 剧本要点 = script key points; 实际轮数 / 时长 = actual turns / duration; 执行边界 = execution boundaries; 设置 / 扩展隔离 = settings / extension isolation; 异常事件 = abnormal events; 无 = none.
- Section 2 table headers: 轮次 = turn; 步骤描述 = step description; 判定 = judgment; 说明 = notes.
- Section 3 fields: 指令总数 = total instructions; 遵守率 = compliance rate. The status labels (已遵守, 被违反, 被跳过, 未触发, 存疑) and step labels (依据 Rx, 偏离 Rx, 无依据) are defined in [judging-criteria.md](judging-criteria.md).
- Section 4 items: 未触发指令审视 = review of untriggered instructions; 无依据步骤聚类 = cluster of no-basis steps.
- Section 5 priorities: 【高】 = high; 【中】 = medium; 【低】 = low.
- Section 6 fields: 沙箱产物清单 = sandbox artifact list; 剧本全文（含即兴追记附录） = full script (including the improvised-answers appendix); 指令清单 = instruction inventory; 原始 transcript = raw transcript; 逐轮状态 = per-turn state.
- The ⚠️ line: "The sandbox and orchestration directory both live in session-scoped temporary space; copy the raw evidence yourself if you need to keep it long term."

## Writing requirements

- The step traceability table must cover every semantic step; do not sample.
- In the instruction coverage statistics, every instruction (R1..Rn) must appear in exactly one status list (except `存疑`, which is listed separately).
- Every suggested change must be directly actionable (which section to change and how). Empty advice such as "consider improving the wording" is forbidden.
- No ornate prose: when a plain statement exists, use it instead of metaphors and flowery wording. Write "this instruction still matters" (这条指令依然重要), not "this instruction still has a place at the table" (这条指令依然有一席之地). Metaphors bring associations the author did not choose and cannot control, and the reader has to work harder to decode them.
- The report must be written to the path returned by the runner's `report-path`. It must not be written into the target skill's own directory or overwrite an existing file.
