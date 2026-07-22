# Write Spec

## 用途

把一个**边界已经清晰**的想法 / 需求（理想情况下来自 refine-idea 的概念单），
钉成一份**可被验证的行为规格**：用 Requirement + MUST + Scenario（WHEN→THEN）
写清行为与验收，强制覆盖边界场景、把"不做什么"转成可验证的 MUST NOT，
经用户 review 才放行进入实现。greenfield 阶段还会先用**能力覆盖图（Coverage Map）**
系统圈定该领域的能力维度并逐项定档，防止整类功能被漏、也防全面变膨胀。

它填补"概念清晰"和"动手编码"之间的空档：止步于行为与验收，
**不做技术选型 / 架构、不拆任务**（技术方案归下游 make-design，任务拆解归再下游 split-task）。

## 触发场景

- "帮我写个 spec / 把这个需求写成规格文档 / 定义验收标准"
- "这个功能要做成什么样、怎么验收"
- "进开发前先把 spec 定下来"
- 手上有 refine-idea 的概念单，要继续往下钉成可验证规格。
- 不适用：概念还模糊（先用 refine-idea）；要技术方案 / 任务拆解（技术方案归 make-design，任务拆解归再下游 split-task）；
  已在写代码 / 调 bug / 评审；以及任何非交互场景（CI / 定时任务 / 自治循环）。

## 使用方式

将本目录下的 `SKILL.md` 和 `references/` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/write-spec/`；Codex：`.agents/skills/write-spec/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/spec-template.md`：行为契约 spec 的落盘模板（含 delta 写法、能力覆盖与档位节）。
- `references/coverage-probes.md`：双探针清单（边界 + 禁止），含怎么转成可验证项。
- `references/coverage-map.md`：能力覆盖图（greenfield）——功能空间调研、能力维度定档（纳入 / 默认不做 / 后续版本 / 必须确认）、问题分级。
- `docs/`：开发过程中的设计文档。
