# test-skill

在隔离沙箱中发起一次 headless 盲测，把被测 agent 的语义步骤逐一溯源到目标 skill 指令，并产出中文复盘报告。

它不属于 refine-idea → write-spec → make-design → split-task → execute-task 主链，而是横向质检工序。

## 输入与输出

- **输入**：目标 skill（仓库 id、`SKILL.md` 路径或已安装名称）与可选场景。
- **运行证据**：位于 scratchpad 的同级编排目录，包括 checklist、persona、逐轮 prompt、JSONL、stderr、会话 ID 与状态文件。
- **持久输出**：发起测试项目下 `skill-test-reports/<被测-id>/test-report-<时间>-<run-id>.md`。报告不写入目标 skill 原目录，也不会覆盖同日报告。

一次测试是完整的多轮 agent 会话，默认最多 10 轮。真实 headless 运行前必须向用户展示场景、工具边界和成本并取得确认。

## 平台支持

- **Claude Code**：保留原有 `scripts/run-headless.py`、`.claude/skills/` 注入和精确工具预授权。
- **Codex**：使用新增的 `scripts/run-codex-headless.py`、`.agents/skills/` 注入和 `codex exec` sandbox 隔离。
- 一次盲测只选择一个平台和对应 runner；失败时不静默切换平台。

将本目录完整复制到目标平台的 Skill 目录使用：Claude Code 为 `.claude/skills/test-skill/`，
Codex 为 `.agents/skills/test-skill/`。不要只复制 `SKILL.md`，两套 runner 和 references 都是执行契约的一部分。

## 执行边界

- 两个 runner 都使用 Python 标准库实现跨平台超时、可靠参数传递、会话校验和证据落盘。
- Claude runner 用 `--tools`、最小 `--allowedTools`、`dontAsk`、strict MCP 空配置和 project 设置源隔离。
- Codex runner 用 `workspace-write/read-only` sandbox、`approval_policy=never`、隔离 HOME、`--ignore-user-config`、`--ignore-rules` 和关闭 web search 隔离；不会使用危险的 bypass 参数。
- 单轮失败后保留现场并停止；需要重跑时使用全新的沙箱和编排目录。

## 文件导览

- `SKILL.md`：六阶段盲测流程与 fail-closed 红线。
- `scripts/run-headless.py`：Claude Code runner。
- `scripts/run-codex-headless.py`：Codex runner。
- `scripts/tests/`：两套 runner 使用 fake CLI 的无真实模型回归测试。
- `references/platform-runners.md`：平台选择、命令模板与各自 fail-closed 边界。
- `references/judging-criteria.md`：步骤判定和指令状态的唯一口径。
- `references/report-template.md`：六节复盘报告模板。
- `references/persona-template.md`：模拟用户剧本模板。
- `docs/`：早期设计与假设验证记录；其中命令样例仅作历史证据，现行执行契约以 `SKILL.md` 和 runner 为准。
