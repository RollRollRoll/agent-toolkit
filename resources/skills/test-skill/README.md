# test-skill

对目标 skill 发起一次 **headless 盲测跑**，逐步骤溯源 agent 的每个动作依据 skill 哪条指令，产出中文复盘报告——回答"这个 skill 写得好不好、哪里要改"。

它不在五工序链（refine-idea → write-spec → make-design → split-task → execute-task）之内，是横向的**质检工序**：五工序链生产 skill，test-skill 检验 skill。

## 输入 / 输出

- **输入**：目标 skill（仓库 id / SKILL.md 路径 / 已安装 skill 名）+ 可选测试场景（缺省时自动设计并请用户确认）。
- **输出**：中文复盘报告——步骤溯源表、指令覆盖统计（已遵守 / 被违反 / 被跳过 / 未触发）、设计诊断与可直接执行的修改建议。仓库内 skill 的报告落在 `resources/skills/<被测id>/docs/`。

## 成本提示

一次测试 = 一个完整的多轮 headless agent 会话（默认上限 10 轮），token 消耗可观。流程内置成本确认门：开跑前会给出预估并等待确认。

## 文件导览

- `SKILL.md` —— 主体：六阶段流程（预检 → 指令清单化 → 沙箱 → 剧本 → 盲测驱动 → 溯源分析 → 报告）。
- `references/judging-criteria.md` —— 溯源判定的唯一口径（步骤三类判定、指令四类状态、置信度与统计规则）。
- `references/report-template.md` —— 复盘报告六节模板。
- `references/persona-template.md` —— 模拟用户剧本模板（隐藏痛点机关）。
- `docs/2026-07-02-test-skill-design.md` —— 技术设计（含核心决策：盲测 + 事后溯源、headless CLI 驱动的理由）。
- `docs/2026-07-02-test-skill-plan.md` —— 实现计划。
- `docs/2026-07-02-assumption-test-notes.md` —— headless 驱动 4 条技术假设的实测记录与命令模板终稿。
