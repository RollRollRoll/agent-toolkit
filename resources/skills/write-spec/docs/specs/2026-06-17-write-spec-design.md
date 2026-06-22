# write-spec 设计文档

日期：2026-06-17

## 背景与目标

综合四个上游项目的设计精华，为 agent-toolkit 新增一个**编码前闸门** skill：
把一个边界已清晰的概念（理想情况下来自 refine-idea 概念单），钉成一份
**可被验证的行为规格**。**只写行为与验收，不做技术选型 / 架构、不拆任务**，
刻意止步于 plan 之前。

四个母体（综合，不照抄任何一个）：

- **agent-skills（spec-driven-development）**：spec 是编码前闸门。
- **OpenSpec**：区分行为 spec 与实现计划；delta 思路。
- **superpowers（brainstorming）**：先读上下文再写，spec 自检。
- **GSD Core**：边界场景与 must-NOT 覆盖。

## 定位

站在 refine-idea（概念边界）与 make-design（技术方案 + 任务）之间：

- 上游 refine-idea 给"做什么 / 不做什么"的概念 —— 可选输入。
- 本 skill 把概念翻译成"系统 MUST / MUST NOT / 边界如何 / 怎么验收"的行为契约。
- 下游 make-design 负责技术方案与任务拆解 —— 本 skill 不碰。

## 关键设计决策（本次确认）

1. **产物形态**：默认单份文档；内容采用 OpenSpec 的**行为契约思想**
   （Requirement + MUST + Scenario(WHEN/THEN)），不照搬多文件 bundle。
   规模极大 / 多能力时可提议升级为 per-capability 多文件（scale-up，非默认）。
2. **决策边界**：spec **纯行为 + 行为级约束**；技术选型 / 架构整体留给下游。
   "影响行为的约束"（如 MUST NOT 拉取 CI 状态）属 spec，"用什么技术"不属。
3. **工作流形态**：**先确认关键边界再起草**——扫上下文 +（可选）读概念单 →
   仅就少数关键验收 / 边界做确认式提问 → 起草 → 自检 → 用户 review 门禁。
   不重复 refine-idea 的意图挖掘。
4. **落盘**：spec 默认落盘（与 refine-idea 默认不落盘相反）——spec 是要进仓库、
   实现期持续更新的工件。位置跟随仓库既有约定，无则默认
   `docs/specs/<YYYY-MM-DD>-<主题>-spec.md`。

## 招牌机制：行为契约 + 双探针

- **关一 · 可验证性**：每条 Requirement 必须能写出可观察的 Scenario，
  否则是愿望不是需求。
- **关二 · 双探针强制覆盖**：
  - 边界探针：边界值 / 空值 / 排序 / 并发 / 幂等 / 精度 / 编码 / 超时。
  - 禁止探针：把每条"不做什么"转成可验证的 MUST NOT（含"怎么验证它没发生"）。

## 工作流程（阶段 0 + 四阶段）

- **阶段 0** 定位与上下文（扫项目 / 接上游概念单 / 判 greenfield-brownfield / 判规模）
- **阶段 1** 确认关键边界（聚焦提问，不重复意图挖掘）
- **阶段 2** 起草 spec（行为契约，纯行为）
- **阶段 3** 自检（spec 卫生 + 双探针覆盖）
- **阶段 4** 用户 review 门禁（落盘 → review → 未过不进 plan/code → 不自动往下）

## 四源如何被综合（不照抄）

- **agent-skills** → "spec 是编码前闸门 + 未过 review 不进 plan/code" → 阶段 4 硬门。
- **OpenSpec** → "行为契约（Requirement/MUST/Scenario）+ brownfield delta" → 产物内容；
  但不照搬多文件 bundle。
- **superpowers** → "先扫上下文再动笔 + spec 自检（占位/矛盾/范围/歧义）" → 阶段 0 与 3①。
- **GSD Core** → "边界探针 + 禁止探针" → 招牌机制与阶段 3②。

## 原创内核

把四源的离散主张，收束成一条可操作的纪律：**"每条需求都要过可验证性关 +
双探针关"**——让 spec 的"写完"有客观判据（有 Scenario、边界扫过、不做什么可验证），
而不是靠"看起来挺全"。

## 边界（本 skill 不做什么）

- 不做技术选型 / 架构 / 数据模型。
- 不拆任务、不排期。
- 不挖意图（那是 refine-idea）；概念还没清就退回上游。
- 不自动进入实现（不调用下游 skill、不写代码）。
- 不在非交互场景运行。

## 文件结构

```text
resources/skills/write-spec/
  SKILL.md
  README.md
  metadata.yaml
  references/
    spec-template.md      行为契约 spec 模板（含 delta）
    coverage-probes.md    双探针清单
  docs/specs/
    2026-06-17-write-spec-design.md   本文档
```

`.claude-plugin/plugin.json` 与 `marketplace.json`：`skills` 数组加入 `write-spec`，
version `0.2.0` → `0.3.0`。

## 2026-06-20 增强：greenfield 全面性（Coverage Map）

**动机**：greenfield 阶段只盯用户明说的需求展开，**整类能力维度会被静默漏掉**——
不是漏在边界（那有双探针兜着），而是漏在"领域本应有、但没人提起"的功能空间上。

**设计**：四个机制**收敛成一条链，以 Coverage Map 为枢纽**（不做成并列章节，避免 skill 自身膨胀）：

1. **功能空间调研（先问后调）**：greenfield 且领域成熟时，**先征求用户同意**，再用
   deep-research 调研该领域常见能力维度 / 丰富度分档 / 易漏点。产出是**功能空间参考，
   不是需求**，零默认纳入。
2. **Coverage Map**：把"需求已含 + 调研补充"的维度汇成一张表，**落盘进 spec 一节**，让全面性可被 review。
3. **档位**：每行必落一档 `纳入 / 默认不做 / 后续版本 / 必须确认`——防"全面变膨胀"的闸门。
4. **问题分级**：对"必须确认"分 `现在问 / 采用默认 / 放 Open Questions`，避免一次抛几十个问题。

**层次**：Coverage Map（宏观：有哪些维度、做不做）→ 双探针（微观：选定需求的边界与禁止）。
**边界**：只动 greenfield；brownfield 仍走 delta，不建 Coverage Map。

**落地**：

- 新增 `references/coverage-map.md`（调研纪律 + 列维度 + 判档 + 问题分级 + 模板）。
- `SKILL.md`：招牌机制加"greenfield 多一层"；阶段 1 升级为"调研 → 建图 → 分级确认"；
  核心原则 / 终止条件 / 自检清单 / 反例 / 示范同步。
- `spec-template.md`：greenfield 模板加「能力覆盖与档位」节。

**两个经用户确认的决策**：Coverage Map **落盘为固定章节**；deep-research **先问后调**（不自动跑）。
