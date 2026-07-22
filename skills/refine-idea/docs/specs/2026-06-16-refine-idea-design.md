# refine-idea 设计文档

日期：2026-06-16

## 背景与目标

融合三个上游 skill 的设计精华，为 agent-toolkit 新增一个**前置阶段** skill：
把用户模糊的期望打磨成边界清晰的可执行概念。**只确定"做什么 / 不做什么"，
不产出开发方向和任务拆解**，刻意止步于 spec 之前。

三个母体：

- **interview-me**：挖真实意图。
- **idea-refine**：发散—收敛，产出带 Not Doing 的 one-pager。
- **obra/superpowers brainstorming**：需求→spec 的闸门式流水线。

## 定位

站在 interview-me 与下游 spec 之间。前半段挖真实意图（interview-me 内核），
后半段轻发散照亮边界并收敛（idea-refine 内核），用闸门思想守住"不越界到
方案"（brainstorming 内核，但闸门挪到"概念"层）。

## 关键设计决策（本次确认）

1. **产出物**：默认对话确认，用户要才落盘一份轻量「概念单」。概念单只到
   边界，不含技术方案 / 任务。
2. **发散程度**：轻发散，只为照亮边界（用思维透镜），不生成技术方案变体。
3. **提问机制（招牌）**：先定位不确定性，再决定怎么问——问题层用 Q+GUESS
   （暴露完整假设让用户证伪），选项层用选择题（在已知集合里快速取舍）；
   时序上先 Q+GUESS 锁定问题，再选择题探索边界。

## 工作流程（四阶段）

- **阶段 0** 亮假设 + 定规模
- **阶段 1** 挖意图（Q+GUESS 主导）← 不确定性在问题层
- **阶段 2** 照亮边界（轻发散 + 选择题主导）← 不确定性降到选项层
- **阶段 3** 复述 + 严格确认（六行，Out of scope 强制）
- **阶段 4** 交付（默认不落盘；终态把概念交还用户，不自动进入实现）

## 与三个母体的对应

- **interview-me** → 假设 + 置信度、Q+GUESS、want vs should-want、六行复述、
  严格确认门、Loading 约束、95% 停止条件。
- **idea-refine** → 思维透镜发散、隐藏假设显式化、Not Doing 一等公民、
  诚实而非迎合、概念单 one-pager。
- **brainstorming** → 止步闸门（不越界到方案）、规模评估先拆分、提问偏选择题。

## 原创内核

"先定位不确定性，再决定怎么问"——把"何时 Q+GUESS、何时选择题"从静态
配比，升级为由不确定性层级驱动的动态规则。

## 边界（本 skill 不做什么）

- 不产出技术选型 / 架构 / 数据模型。
- 不拆任务、不排期。
- 不自动进入实现（不调用任何实现 skill）。
- 不在非交互场景运行。

## 文件结构

```text
skills/refine-idea/
  SKILL.md
  README.md
  metadata.yaml
  references/
    lenses.md          思维透镜清单
    concept-note.md    概念单模板
  docs/specs/
    2026-06-16-refine-idea-design.md   本文档
```

`.claude-plugin/plugin.json`：`skills` 数组加入 `refine-idea`，
version `0.1.0` → `0.2.0`。
