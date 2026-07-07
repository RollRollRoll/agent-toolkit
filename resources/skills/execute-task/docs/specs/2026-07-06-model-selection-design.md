# execute-task 补充「模型选择」机制设计文档

日期：2026-07-06

## 背景与目标

用户提出通用的 subagent 模型选型策略（核心点）：

- 用**够用的最省档位**控成本、提速度；按角色分档——机械实现用便宜档，集成/判断类用标准档，
  架构/设计类与最终整体 review 用最强档。
- **派发时必须显式指定模型**——不写等于继承主 agent 当前档位（通常最贵最强），悄悄废掉分档的意义。
- **轮次数比单价更重要**：便宜档在多步任务上常要 2-3 倍轮次，折算下来不一定省；按文字描述实现的执行者、
  以及 reviewer，至少要标准档兜底；只有"简报已给完整代码的转录类任务"或"单文件机械修复"才用最便宜档。

execute-task 是这条 skill 链里**唯一真正派发 subagent 写代码 / 审查 / 修复**的一环（阶段 2 逐任务闭环 + 阶段 3
整体验收），此前完全没有模型选择相关内容——派发时用什么档位没有规定，默认行为等同"继承主 agent"，与上述策略
背道而驰。本次把这份策略落地成 execute-task 的具体机制。

## 关键决策

1. **新增独立 reference 文件 `references/model-selection.md`**，不塞进 `orchestration.md`——模型选择是横切
   执行 / review / fix 三类派发 + 阶段 3 整体验收的独立关注点，且延续本 skill"重内容拆独立文件、SKILL.md
   只留指针"的既有模式（呼应 orchestration / execution-loop / handoff-templates / acceptance 的既有拆分）。
2. **四类派发对象的默认档位映射**（对照 execute-task 自身的任务粒度具体化，而非照抄通用文案）：
   - 执行 subagent：默认 cheap（因为 split-task 已把任务拆细、简报给足验收标准），简报只有文字描述需要
     自己拼接多文件时升 standard，需要架构判断时升 most-capable（但正常不该出现——出现即提示上游 make-design
     可能漏了决策，不当作常态处理）。
   - review subagent：跟执行同等判断力档位，按 diff 规模/复杂度/风险走。
   - fix subagent：与被修任务的执行档位一致或降一档。
   - 阶段 3 整体验收（whole-branch review）：**固定 most-capable**，不沿用 session 默认——对应用户策略里
     "架构与设计类任务、以及最终整体 review 用最强档"这一条，在 execute-task 里唯一对应的就是闸门二。
3. **铁律前置**：model-selection.md 开篇即"派发时必须显式指定模型"，并在 SKILL.md 核心一、orchestration.md
   派发一节、handoff-templates.md 模板说明、acceptance.md 闸门二、以及三处自检清单（SKILL.md / orchestration.md /
   handoff-templates.md）都加了对应的判据引用或自查项——确保这条铁律不会因为只写在一个文件里而被派发时忽略。
4. **模型档位不写进派发 prompt 正文**：handoff-templates.md 里的三个模板是"照抄填空"的 prompt 文本，模型档位
   是派发参数（如 Claude Code Agent 工具的 `model`），不是 prompt 内容——在模板文件顶部加了一条说明区分二者，
   避免误把档位当成要写进 prompt 里的一句话。

## 改动文件清单

- 新增：`references/model-selection.md`（铁律 + 角色定档表 + 复杂度信号 + 轮次提醒 + 派发前自查）。
- `SKILL.md`：核心一新增一条模型定档要点、自检清单+1、反例+1、相关参考+1。
- `references/orchestration.md`：四·派发一节新增模型定档要点、收尾自检+1。
- `references/handoff-templates.md`：顶部说明新增模型档位与 prompt 正文的边界、自查+1。
- `references/acceptance.md`：二·整体五轴 review 明确固定 most-capable、收尾自检更新。
- `README.md`：目录说明补充 model-selection.md 条目。

## 发布

本次是既有资源的内容修改（非新增 skill / mcp / command / hook 资源），按 `docs/conventions.md` 不强制触发
`.claude-plugin/plugin.json` 版本递增；仅 `metadata.yaml` 的 `updated_at` 需要保持为最后维护日期
（已是 2026-07-06，无需改动）。如需随插件发布这次改动，再按 `docs/conventions.md` 新增资源流程走版本递增
与 `claude plugin validate . --strict` 校验。
