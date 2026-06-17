# Write Spec

## 用途

把一个**边界已经清晰**的想法 / 需求（理想情况下来自 refine-idea 的概念单），
钉成一份**可被验证的行为规格**：用 Requirement + MUST + Scenario（WHEN→THEN）
写清行为与验收，强制覆盖边界场景、把"不做什么"转成可验证的 MUST NOT，
经用户 review 才放行进入实现。

它填补"概念清晰"和"动手编码"之间的空档：止步于行为与验收，
**不做技术选型 / 架构、不拆任务**（那是下游 write-plan 的事）。

## 触发场景

- "帮我写个 spec / 把这个需求写成规格文档 / 定义验收标准"
- "这个功能要做成什么样、怎么验收"
- "进开发前先把 spec 定下来"
- 手上有 refine-idea 的概念单，要继续往下钉成可验证规格。
- 不适用：概念还模糊（先用 refine-idea）；要技术方案 / 任务拆解（那是 write-plan）；
  已在写代码 / 调 bug / 评审；以及任何非交互场景（CI / 定时任务 / 自治循环）。

## 使用方式

将本目录下的 `SKILL.md` 和 `references/` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/write-spec/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/spec-template.md`：行为契约 spec 的落盘模板（含 delta 写法）。
- `references/coverage-probes.md`：双探针清单（边界 + 禁止），含怎么转成可验证项。
- `docs/`：开发过程中的设计文档。
