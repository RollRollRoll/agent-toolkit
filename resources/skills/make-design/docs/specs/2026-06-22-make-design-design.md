# make-design 设计文档

日期：2026-06-22

## 背景与目标

综合五个上游项目在"技术方案确定"上的设计精华，为 agent-toolkit 新增 refine-idea →
write-spec 之后的**第三道闸门** skill：把一份已确认的行为规格（理想来自 write-spec），
翻译成一份**可被 review、每个决策都可追溯的技术设计**。**只到技术决策层，不下沉到
task-by-task 实现步骤**，刻意止步于 writing-plans 之前。

五个母体（综合，不照抄任何一个）：

- **superpowers（brainstorming）**：2-3 方案 + trade-off + 推荐；先读上下文再写；设计自检。
- **GSD Core（discuss-phase）**：把技术决策结构化为可追溯 Decision，后续强制消费；assumptions 模式从代码推断。
- **agent-skills**：按决策类型分治（API 设计 / ADR / 源码验证 / 反向审查）；source-driven 不凭记忆。
- **OpenSpec**：design 专承载 HOW（Context / Decisions / Risks-Trade-offs / Migration / Open Questions），与 spec 分层。
- **mattpocock/skills**：grilling 拷问设计树、codebase-design（deep module / seam / locality）、重大且难逆才 ADR、prototype 消除不确定性。

## 定位

站在 write-spec（行为契约）与 writing-plans（任务拆解 + 实现计划）之间：

- 上游 write-spec 给"系统 MUST / MUST NOT / 边界 / 验收"的行为契约 —— 主要输入。
- 本 skill 把行为契约翻译成"用这套架构、这些有取舍有理由的技术决策来实现它"。
- 下游 writing-plans 负责 task-by-task 拆解与实现计划 —— 本 skill 不碰。

> **边界调整说明**：write-spec 早期设计（2026-06-17）曾把"任务拆解"也预期为 make-design 的职责；
> 本次确认 make-design **只到技术设计层**，任务拆解归 writing-plans。已同步校正 write-spec **当前**
> SKILL.md / README 中相关措辞（write-spec 的历史 design 快照不回溯）。

## 关键设计决策（本次确认，两处经用户拍板）

1. **下边界（用户拍板）**：make-design **止于技术设计决策层**——产出技术设计文档（选型 / 架构 /
   数据模型 / 接口 / 错误处理 / 测试策略 / 风险 / 迁移 / 待解问题），不写 task-by-task 步骤与验证命令；
   任务拆解交 writing-plans。理由：与 refine-idea / write-spec"各守一层"纪律一致，与"明确技术方案"
   诉求吻合，不与 superpowers/writing-plans 重复。
2. **交互姿态与加载约束（用户拍板）**：**推断优先 + 重大必停 + 最终 review**。允许从 spec + 代码库 +
   最佳实践推断常规决策（显式标注假设），但重大且难逆 / 需用户偏好的决策必停下问；技术方案定稿必经
   活人 review 才进实现。比 refine-idea / write-spec 的"非交互硬禁用"略松（技术决策多可推断），
   并吸收 GSD 的 assumptions 模式。
3. **产物形态**：默认单份技术设计文档；brownfield 用 delta（聚焦改动 + 对现有影响）。位置跟随仓库
   既有约定，无则默认 `docs/design/<YYYY-MM-DD>-<主题>-design.md`。
4. **brownfield 软依赖 codebase-analyzer**：现状不清时先调研现有架构再设计；软依赖，缺了降级为
   有限扫描 + 标注，不卡死。

## 招牌机制：技术决策探针 + 方案对比锁定

与 write-spec「双探针 + 行为契约」严格同构：

- **关一 · 每条决策可追溯**：重大决策给候选 + trade-off + 推荐 + 理由，锁成 Decision（轻量 ADR）。
- **关二 · 决策探针强制覆盖**：逐项扫 11 个技术决策维度，每个强制表态（需决策 / 不适用 / 延后）。
- **闸门一 · 决策分级**：重大 / 常规 / 延后三档，防笨重（不给琐碎决策硬凑方案）。
- **闸门二 · 需求覆盖核对**：spec 每条 MUST / MUST NOT → 设计落点，防落空与镀金。
- **漏斗**：探针圈点 → 重大的方案对比 → 分级收敛 → 需求覆盖核对。

## 工作流程（阶段 0 + 四阶段）

- **阶段 0** 定位与上下文（接 spec / 扫代码库 / 判 greenfield-brownfield / 判规模）
- **阶段 1** 圈定技术决策并分级（决策探针 + 推断优先 + 重大停下问）
- **阶段 2** 起草技术设计（方案对比锁定 + 选型查证）
- **阶段 3** 自检（设计卫生 + 覆盖自检）
- **阶段 4** 用户 review 门禁（落盘 → review → 未过不进 task/code → 不自动往下）

## 五源如何被综合（不照抄）

- **superpowers** → 方案对比（候选 + 取舍 + 推荐）+ 先扫上下文 + 设计自检 → 招牌机制关一、阶段 0/3。
- **GSD Core** → 技术决策结构化为可追溯 Decision + assumptions 推断模式 → 招牌机制 + 阶段 1 推断优先。
- **agent-skills** → 决策分类处理 + 选型查证不凭记忆 + 反向审查 → 决策探针分维度 + 核心原则 5 + 阶段 3。
- **OpenSpec** → design 专承载 HOW、与 spec 分层 + Migration / Open Questions → 定位 + 产物结构。
- **mattpocock** → 重大且难逆才 ADR + codebase-design（seam / locality）+ 拷问 → 决策分级 + test seam 维度。

## 原创内核

把五源的离散主张收束成一条可操作的纪律：**"每个技术决策都要过覆盖关（探针逐项扫）+ 质量关
（重大的有候选与取舍），并逐条对回 spec（不落空、不镀金）"**——让技术方案的"写完"有客观判据
（每维度有结论、重大决策可追溯、每条需求有落点），而不是靠"架构看起来挺合理"。

## 边界（本 skill 不做什么）

- 不下沉 task-by-task 步骤 / 验证命令 / 排期（那是 writing-plans）。
- 不定行为（那是 write-spec）；spec 没钉死就退回上游。
- 不挖意图（那是 refine-idea）。
- 不自动进入实现（不调用下游、不写代码）。
- 重大决策不无人 review 就定稿往下跑。

## 文件结构

```text
resources/skills/make-design/
  SKILL.md
  README.md
  metadata.yaml
  references/
    design-template.md      技术设计模板（含 brownfield delta）
    decision-probes.md    技术决策探针清单（11 维度）
    decision-method.md    决策方法（方案对比 / 分级 / 轻量 ADR / 需求覆盖核对 / 推断标注）
  docs/specs/
    2026-06-22-make-design-design.md   本文档
```

**衔接修订**：write-spec `SKILL.md`（3 处）与 `README.md`（2 处）把"任务拆解"从 make-design 职责
校正为归其后的实现计划。

**发布**：`.claude-plugin/plugin.json` 与 `marketplace.json` 的 `skills` 数组加入 make-design，
version `0.3.4` → `0.4.0`。
