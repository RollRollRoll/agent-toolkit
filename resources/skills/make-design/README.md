# Make Design

## 用途

把一份**已确认的行为规格**（理想情况下来自 write-spec），在动手编码前转化为一份
**可被 review、每个决策都可追溯的技术设计**：用决策探针逐项扫技术维度防漏，
重大且难逆的决策给候选 + trade-off + 推荐 + 理由锁成 Decision，
并逐条核对 spec 的 MUST / MUST NOT 都有设计落点（不落空、不镀金），
经用户 review 才放行进入实现。

它填补"行为定了"和"动手编码"之间的空档：止步于技术决策层，
**不下沉到 task-by-task 任务拆解与实现**（那是下游 split-task 与执行的事）。

## 触发场景

- "spec 定了，技术方案怎么做 / 帮我设计下怎么实现"
- "比较下几种技术方案 / 这里该用哪种做法"
- "进开发前先把架构、选型、数据模型定下来"
- 手上有 write-spec 的行为规格，要继续往下确定技术方案。
- 不适用：行为 / 需求还没钉死（先 write-spec）；想法还模糊（先 refine-idea）；
  要任务拆解 / 实现计划（那是下游 split-task）；已在写代码 / 调 bug / 评审。

## 使用方式

将本目录下的 `SKILL.md` 和 `references/` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/make-design/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/design-template.md`：技术设计文档落盘模板（含 greenfield 全量与 brownfield delta）。
- `references/decision-probes.md`：技术决策探针清单（11 个维度），含每个维度问什么、怎么判级。
- `references/decision-method.md`：决策方法——方案对比、决策分级、轻量 ADR、需求覆盖核对、推断与假设标注。
- `docs/`：开发过程中的设计文档。
