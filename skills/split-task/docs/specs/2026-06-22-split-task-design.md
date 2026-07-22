# split-task 设计文档

日期：2026-06-22

## 背景与目标

综合五个上游项目在"技术方案确定后如何拆任务"上的设计精华，为 agent-toolkit 新增
refine-idea → write-spec → make-design 之后的**第四道闸门** skill：把一份已确认的
**技术设计**（理想来自 make-design），拆成一份**可被 review、每个任务都可独立验收**的
开发任务清单。**只到任务拆分层，不下沉到逐行实现与施工**，止于"任务清单确认"。

五个母体（综合，不照抄任何一个）：

- **superpowers（writing-plans）**：任务=独立可测试交付物；先定文件结构再拆；不留 TODO/TBD 占位。
- **GSD Core（plan-md）**：任务结构化（depends_on / wave / files_modified / acceptance）；wave 控并行、不冲突文件；plan-checker 质量门禁。
- **agent-skills（planning-and-task-breakdown）**：依赖图 → vertical slice → 任务大小 S/M（XL 必拆）→ 每 2-3 任务设 checkpoint → 高风险前置。
- **OpenSpec（tasks）**：轻量 checkbox 清单、按依赖排序、每任务一个 session 内可完成、可被执行阶段勾选追踪。
- **mattpocock（to-issues）**：tracer-bullet vertical slice（穿透 schema/API/UI/test）、每片可独立 demo、**先展示拆分让用户确认粒度与依赖**再落地。

## 定位

站在 make-design（技术设计）与执行（编码）之间：

- 上游 make-design 给"用这套架构 / 这些有取舍有理由的技术决策来实现"的技术设计 —— 主要输入。
- 上游 write-spec 的行为规格提供"验收口径 / MUST / MUST NOT" —— 任务验收标准的来源。
- 本 skill 把技术设计翻译成"**按什么顺序、拆成哪些可独立验收的任务**来实现它"。
- 下游执行（TDD 编码；单任务若需含代码的逐步施工单，可选用 superpowers writing-plans 等）—— 本 skill 不碰。

> **链路最终形态**：
> `refine-idea → write-spec → make-design → split-task → 执行`
> split-task 是这条链上"任务拆解"这一棒的承担者。

## 关键设计决策（本次确认）

1. **任务粒度 = 中量级（用户拍板）**：每个任务含 目标 / 切片 / 涉及文件 / 依赖 / 验收标准 /
   验证方式 / 覆盖的 design&spec 条目 + checkbox；**不内嵌实现代码**。
   - 理由：契合本链"可验证"基因；不与下游执行阶段重复（重量级含测试代码+实现片段+commit 是 writing-plans/执行的活）；
     也不退化成纯 checkbox（丢掉依赖图与覆盖核对的深度）。
2. **招牌机制方向 = 与上游同构·切片三件套（用户拍板）**：垂直切片定序 + 拆分探针 + 两道闸门，
   阶段 0~4 与 make-design 一一对应。GSD 的 wave 并行、agent-skills 的高风险前置/checkpoint
   作为**轻量元素吸收**，不套 GSD 那套重门禁。
   - 理由：五个 skill 一个心智模型，学习成本最低；同构的"探针 + 覆盖核对"正是本链区别于"随手拆个 todo"的核心价值。
3. **不软依赖 codebase-analyzer（用户拍板）**：brownfield 现状认知**信任上游 design**
   （make-design 阶段已做过现状调研，现状已沉淀在 design 的 delta/现状节）。design 现状不足以
   支撑拆任务 → **退回 make-design 补**，split-task 不自己重做架构调研。
   - 注意区分：阶段 0 的**轻量扫代码库**（摸技术栈 / 测试怎么跑 / 构建怎么跑）保留——那是让任务的
     "涉及文件 / 验证命令"落地，不是架构调研。
4. **交互姿态 = 推断优先 + 关键点必停 + 最终 review（沿用 make-design）**：允许从 design + spec +
   代码库推断常规拆分（显式标注假设），但**切片边界 / 粒度 / 关键依赖顺序 / 需用户偏好的取舍**必停下确认；
   任务清单定稿必经活人 review 才进执行。吸收 mattpocock"先展示拆分让用户确认粒度与依赖"。
5. **产物形态 = 本地单份 tasks 文档（推断，用户认可）**：默认 `docs/tasks/<YYYY-MM-DD>-<主题>-tasks.md`，
   跟随仓库既有约定（若有 OpenSpec 式 `openspec/changes/<change>/tasks.md` 或 `docs/tasks/` 就跟随）；
   brownfield 用 delta（聚焦改动相关任务 + 迁移/兼容/回滚任务，不重列全量）。
6. **不做 issue tracker 集成（推断，用户认可）**：不接 gh/jira API（mattpocock to-issues 风格）。
   本链是本地文档驱动，引入外部集成偏离定位、增复杂度（YAGNI）。列入非目标/反例。

## 招牌机制：切片三件套（与 make-design 严格同构）

与 make-design「决策探针 + 方案对比锁定」同构：

- **关一 · 每个任务独立可验收**：每个任务必须写得出「完成判据 + 怎么验证」（验收标准 + 验证命令）。
  写不出验收的，不是任务，是模糊占位——打回拆清或合并。（对应 spec 的 Scenario 可验证、Decision 的可追溯）
- **关二 · 拆分探针强制覆盖**：逐项扫**易漏任务维度**，每项强制表态〔需任务 / 不适用 / 延后〕——
  数据迁移、测试、配置/环境变量、文档、回滚、可观测（日志/指标）、集成点、依赖安装、构建/CI、接口契约落地、种子数据……
  "忘了想"和"想过判定不适用"是两回事。
- **闸门一 · 任务分级**（防笨重 + 防过碎）：任务大小以 S/M 为宜，**XL 必拆、过碎则合并**；
  垂直切片优先，但允许必要的地基任务（建表 / 脚手架 / 公共依赖）。不给每个琐碎动作单列一个任务。
- **闸门二 · 设计&spec 覆盖核对**（防落空与镀金）：design 每个组件/Decision、spec 每条 Requirement/MUST NOT →
  由哪个任务覆盖；**不落空**（每个设计点都有任务落地）、**不镀金**（无 design/spec 之外的任务）。这是本 skill 独有闸门。
- **漏斗顺序**：垂直切片**圈出任务**（覆盖面）→ 拆分探针**补漏**（易漏维度）→ 任务分级**收敛**（大小/合并/前置，防笨重）→
  设计&spec 覆盖核对**对回上游**（对齐 design+spec）。

## 工作流程（阶段 0 + 四阶段，与 make-design 同构）

- **阶段 0 · 定位与上下文**：读 design（主）+ spec（验收口径）；轻量扫代码库（技术栈 / 现有结构 /
  **测试怎么跑、构建怎么跑**）；判 greenfield/brownfield；判规模（多子系统→提议拆多份 tasks）。
  **无 design → 退回 make-design**，不自己补技术决策。
- **阶段 1 · 切片与定序**：按垂直切片切任务 → 跑拆分探针补漏 → 建依赖关系 / 可并行标注 / 高风险前置 →
  任务分级（大小 / 合并）。推断优先；**切片边界 / 粒度 / 关键依赖顺序**这类会改变清单形状、或需用户偏好的，停下确认。
- **阶段 2 · 起草 tasks**（按 task-template）：每个任务含 目标 / 切片 / 涉及文件 / 依赖 / 验收标准 /
  验证方式 / 覆盖的 design&spec 条目 + checkbox；附依赖与并行视图、checkpoint 标注。
- **阶段 3 · 自检（双重）**：① 任务卫生（占位 / 矛盾 / 范围 / 歧义）② 覆盖自检（探针每维表态？
  每任务有验收+验证？design&spec 每条有任务落点、无镀金？依赖**无环**、顺序可执行？）。就地修复。
- **阶段 4 · 用户 review 门禁（硬门）**：落盘 → 请 review（"未过 review 不进入执行/编码"）→
  用户**显式确认**才过门 → 过门后提示"可据此开始执行"，但**不自动执行、不写代码**。

## 五源如何被综合（不照抄）

- **superpowers** → 任务=独立可测试交付物 + 先定文件结构 + 不留占位 → 招牌机制关一、任务条目含"涉及文件"、自检卫生。
- **GSD Core** → 结构化任务（依赖 / wave 并行 / files_modified / 验收）+ plan-checker 门禁 → 任务条目结构 + 闸门二覆盖核对 + 阶段 3 自检。
- **agent-skills** → 依赖图 + vertical slice + 大小分级(S/M, XL 必拆) + checkpoint + 高风险前置 → 招牌机制（切片 + 闸门一分级）+ 阶段 1 定序。
- **OpenSpec** → 轻量 checkbox + 按依赖排序 + 可勾选追踪 + 一 session 可完成 → 产物形态（中量级条目 + checkbox）+ 粒度判据。
- **mattpocock** → tracer-bullet vertical slice（穿透各层、可独立 demo）+ 先展示拆分让用户确认粒度依赖 → 招牌机制关一切片 + 阶段 1 推断后确认 + 阶段 4 review。

## 原创内核

把五源的离散主张收束成一条可操作的纪律：**"每个任务都要过覆盖关（拆分探针逐项扫、易漏维度不漏）+
质量关（独立可验收：有完成判据与验证方式），并逐条对回 design 与 spec（不落空、不镀金）"**——
让任务拆分的"拆完了"有客观判据（每维度有结论、每任务可验收、每个设计点有落地、依赖无环可执行），
而不是靠"任务列表看起来挺全"。

## 边界（本 skill 不做什么）

- 不下沉到逐行实现代码 / 含代码的施工单（那是执行 / 可选 writing-plans）。
- 不定技术决策（那是 make-design）；design 没定就退回上游。
- 不定行为（那是 write-spec）；不挖意图（那是 refine-idea）。
- 不做 issue tracker / 外部平台集成（本地文档驱动，YAGNI）。
- 不自动进入执行（不写代码、不自动跑任务）。
- 任务清单不无人 review 就定稿往下跑（禁 CI/自治循环里自动产清单）。

## 文件结构

```text
skills/split-task/
  SKILL.md
  README.md
  metadata.yaml
  references/
    task-template.md     任务清单落盘模板（中量级条目 + checkbox + 依赖/并行视图 + 覆盖核对表；含 brownfield delta）
    split-probes.md      拆分探针清单（易漏任务维度逐项 + 怎么判"需任务/不适用/延后"）
    slicing-method.md    切片与定序方法（垂直切片判据 / 任务大小分级 / 依赖与 wave 并行 / 高风险前置 / checkpoint / 覆盖核对怎么做）
  docs/specs/
    2026-06-22-split-task-design.md   本文档
```

贯穿案例延续「实验清单」：把 make-design 那份技术设计（`list_experiments()` 纯函数、
`GET /experiments` 路由、`experiments` 表、测试策略、需求覆盖核对）拆成 4~5 个中量级垂直切片任务，
演示切片 / 探针 / 定序 / 覆盖核对。

## 衔接修订（下游措辞校正）

split-task 落地后，本链"任务拆解"这一棒由 split-task 承担。需同步校正上游两个 skill 里把
"任务拆解"归于外部 `writing-plans` 的措辞——与当年 make-design 落地时校正 write-spec 措辞同理。

**校正原则**：
- 凡把"**任务拆解 / 拆任务**"职责归于 writing-plans 的措辞 → 改归 **split-task**（本仓库下游）。
- 凡指"**含代码的逐步实现 / 施工单**"的，保留为更下游"执行（可选 writing-plans）"。
- 即：make-design 的下游第一棒从 writing-plans 改为 split-task；writing-plans 退为 split-task 之后、针对单任务的可选实现工具。

**涉及文件与主要位置**：
- `make-design/SKILL.md`：description、"你的任务·刻意止步"、核心理念、"何时不用"、阶段 4 提示、核心原则 8、反例——凡"下游 writing-plans（任务拆解）"改指 split-task。
- `make-design/README.md`：同方向措辞同步校正。
- `write-spec/SKILL.md`："你的任务·刻意止步"（L18 一带）、核心原则 5——"任务拆解属再下游 writing-plans"改指 split-task。
- `write-spec/README.md`：同方向措辞同步校正。
- 历史 design 快照（write-spec / make-design 的 `docs/specs/*`）**不回溯**，只校正当前 SKILL.md / README.md。

## 发布

按 `docs/conventions.md` 新增资源流程：

- 新建 `skills/split-task/` 下 SKILL.md / README.md / metadata.yaml / references / docs。
- `metadata.yaml`：id=split-task，type=skill，status=draft，created_at/updated_at=2026-06-22。
- `.claude-plugin/plugin.json` 的 `skills` 数组加入 `./skills/split-task`。
- **双清单版本同步**：`plugin.json` 与 `marketplace.json` 版本 `0.4.0` → `0.5.0`。
- 如属某 collection，按约定更新 `collections/*.yaml`（按需）。
- 用 `claude plugin validate . --strict` 校验。
