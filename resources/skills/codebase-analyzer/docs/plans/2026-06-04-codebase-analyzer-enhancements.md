# Codebase Analyzer 三项增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 codebase-analyzer skill 落地三项增强——项目亮点输出、Workflow 工具工作场景全景穷举、Claude Code 扩展件逐条画像+装配图+按条目并行。

**Architecture:** 纯文档（markdown）skill 项目，路线 A——只扩展现有 7 个文件、不新建文件。每处改动是一次 markdown 段落的整段替换或追加。

**Tech Stack:** Markdown。无代码、无自动化测试框架。

---

## 前置说明（必读）

- 这是**文档型 skill**，没有 pytest/jest 之类测试。每个任务的"验证步骤"用 `grep -n` 确认新文本已落地、旧文本已消除，并人工核对章节结构。
- 所有路径相对仓库根目录 `/Users/chenjinfan/Project/codebase-analyzer`。
- Edit 时 `old_string` 必须与文件现有内容**逐字匹配**（含 `{{}}` 占位符、全角标点、空格）。下文每个 Edit 都给出完整 `old_string` / `new_string`。
- commit message 沿用项目惯例：**中文描述式，不加 `feat:` 前缀**（见 `git log`）。
- **任务独立性**：5 个任务各自改不同文件 / 不同章节，锚点互不重叠，可任意顺序、可并行派发。唯一约定：**Task 5 建议最后做**（串联性质，便于最后统一核对一致性）。
  - Task 1 改 `template-deep.md` 第 9 章；Task 4 改 `template-deep.md` 第 8 章——同文件不同章节，old_string 互不包含，顺序无关。
  - Task 2 内部 3 个 Edit 有先后（见任务内说明），但对外不依赖其他任务。
- 设计来源：`docs/superpowers/specs/2026-06-04-codebase-analyzer-enhancements-design.md`。

---

## Task 1: 诉求 1 — 项目亮点（3 个文件）

**Files:**
- Modify: `codebase-analyzer/references/template-deep.md`（第 9 章）
- Modify: `codebase-analyzer/references/template-standard.md`（第 8 章）
- Modify: `codebase-analyzer/references/investigation-checklist.md`（第 9 章）

- [ ] **Step 1: 重构 template-deep.md 第 9 章（改名 + 亮点置顶 + 子节重编号）**

对 `codebase-analyzer/references/template-deep.md` 执行 Edit：

old_string:
````
## 9. 适合程度评估 / 是否值得二次开发

> 帮读者做决策：这个项目能不能用、值不值得在它基础上改。结论要基于前面章节的事实，不要凭印象。

### 9.1 项目优点
- {{基于源码 / 架构观察到的强项，如设计清晰、测试完善、扩展点明确}}

### 9.2 项目局限
- {{观察到的短板，如耦合紧、缺测试、文档过时、强绑定某框架}}

### 9.3 适合使用场景
- {{什么场景下直接拿来用是合适的}}

### 9.4 不适合使用场景
- {{什么场景下不建议用，以及原因}}

### 9.5 是否值得二次开发
- **结论**：{{值得 / 谨慎 / 不建议}}
- **依据**：{{代码可读性、模块化程度、扩展点、社区活跃度、技术债规模等}}
- **二开切入点**：{{若值得，从哪些模块 / 扩展点入手；若不建议，替代方案是什么}}
````

new_string:
````
## 9. 综合评价（亮点 / 适合度 / 二次开发）

> 帮读者做决策：这个项目能不能用、值不值得在它基础上改，以及有哪些值得学习借鉴的设计。结论要基于前面章节的事实，不要凭印象。

### 9.1 项目亮点

> 这个项目**最巧妙 / 最有特色 / 最值得学习借鉴**的设计——技术欣赏视角，区别于下面"优点"（决策视角）。每条落到具体 `path:line`，说清**妙在哪、为什么别人难做到这么好**，不准泛泛说"架构清晰"。

- {{亮点 1：如某个精巧的抽象 / 独特算法 / 干净的扩展机制 / 聪明的工程取舍，`path:line`，妙在哪}}

### 9.2 项目优点（决策视角）
- {{基于源码 / 架构观察到的强项，如设计清晰、测试完善、扩展点明确}}

### 9.3 项目局限
- {{观察到的短板，如耦合紧、缺测试、文档过时、强绑定某框架}}

### 9.4 适合使用场景
- {{什么场景下直接拿来用是合适的}}

### 9.5 不适合使用场景
- {{什么场景下不建议用，以及原因}}

### 9.6 是否值得二次开发
- **结论**：{{值得 / 谨慎 / 不建议}}
- **依据**：{{代码可读性、模块化程度、扩展点、社区活跃度、技术债规模等}}
- **二开切入点**：{{若值得，从哪些模块 / 扩展点入手；若不建议，替代方案是什么}}
````

- [ ] **Step 2: 给 template-standard.md 第 8 章加"项目亮点"条**

对 `codebase-analyzer/references/template-standard.md` 执行 Edit：

old_string:
````
## 8. 适合程度评估
- **优点 / 局限**：{{基于源码事实，各列要点}}
- **适合 / 不适合场景**：{{什么场景能用、什么场景别用}}
- **是否值得二次开发**：{{值得 / 谨慎 / 不建议 + 依据 + 切入点}}
````

new_string:
````
## 8. 综合评价
- **项目亮点**：{{最巧妙 / 最有特色 / 最值得学习的设计，带 `path:line`；技术欣赏视角，区别于下面的"优点"}}
- **优点 / 局限**：{{基于源码事实，各列要点}}
- **适合 / 不适合场景**：{{什么场景能用、什么场景别用}}
- **是否值得二次开发**：{{值得 / 谨慎 / 不建议 + 依据 + 切入点}}
````

- [ ] **Step 3: 给 investigation-checklist.md 第 9 章改名 + 加亮点追问点**

对 `codebase-analyzer/references/investigation-checklist.md` 执行 Edit：

old_string:
````
## 9. 适合程度评估 / 是否值得二次开发

> 对应模板第 9 章。基于前面看到的**事实**回答，不要凭印象。

- **优点**：从源码 / 架构看到的强项是什么？（设计清晰 / 测试完善 / 扩展点明确 / 文档齐全…）
````

new_string:
````
## 9. 综合评价（亮点 / 适合度 / 二次开发）

> 对应模板第 9 章。基于前面看到的**事实**回答，不要凭印象。

- **亮点**：这个项目有没有"最巧妙 / 最有特色 / 最值得学习"的设计？（精巧的抽象 / 独特算法 / 干净的扩展机制 / 聪明的工程取舍…）它**妙在哪**、在哪个 `path:line`、为什么别人难做到这么好？亮点要落到具体源码，**不能泛泛说"架构清晰"**。
- **优点**：从源码 / 架构看到的强项是什么？（设计清晰 / 测试完善 / 扩展点明确 / 文档齐全…）
````

- [ ] **Step 4: 验证三处改动落地**

```bash
grep -n "## 9. 综合评价" codebase-analyzer/references/template-deep.md
grep -n "### 9.1 项目亮点" codebase-analyzer/references/template-deep.md
grep -n "### 9.6 是否值得二次开发" codebase-analyzer/references/template-deep.md
grep -n "## 8. 综合评价" codebase-analyzer/references/template-standard.md
grep -n "项目亮点" codebase-analyzer/references/template-standard.md
grep -n "## 9. 综合评价" codebase-analyzer/references/investigation-checklist.md
```
Expected: 每条都有输出（行号），证明新章名、亮点子节、重编号后的 9.6 都在。

确认 deep 模板里旧标题已无残留：
```bash
grep -n "适合程度评估" codebase-analyzer/references/template-deep.md
```
Expected: 无输出（第 9 章是 deep 里唯一用过该词的地方，已改名）。

- [ ] **Step 5: Commit**

```bash
git add codebase-analyzer/references/template-deep.md codebase-analyzer/references/template-standard.md codebase-analyzer/references/investigation-checklist.md
git commit -m "新增项目亮点维度，评价章改名为综合评价

- 深度档第9章改名综合评价，新增9.1项目亮点并置顶，原子节顺延
- 标准档第8章新增项目亮点条
- investigation-checklist 第9章同步改名并补亮点追问点
- 亮点=技术欣赏视角，与优点（决策视角）界定区分"
```

---

## Task 2: 诉求 2+3 — project-type-checklists.md 专项清单（f 类深度专项 + 新增 g 类）

**Files:**
- Modify: `codebase-analyzer/references/project-type-checklists.md`（判断小节 + f 类 + 文末新增 g 类）

> 本任务 3 个 Edit **按 A→B→C 顺序执行**：Edit C 的锚点是 Edit A 的产物。三者只改这一个文件，对外不依赖其他任务。

- [ ] **Step 1（Edit A）: f 类拆为"通用追问 + 🔴深度档专项：工作场景全景穷举"**

对 `codebase-analyzer/references/project-type-checklists.md` 执行 Edit：

old_string:
````
## f. DevTool / Workflow 工具

- **正常开发流程**：使用者用它的标准流程是几步？入口命令 / 触发方式是什么？
- **产物文件**：会生成 / 修改哪些文件？产物落在哪个目录？
- **与 Git / CI / Spec / Issue 的关系**：是否读写 git、触发 CI、消费 spec / issue？集成点在哪？
- **是否改代码 / 生成文档**：直接改用户代码，还是只生成文档 / 配置？改动范围与可逆性如何？
````

new_string:
````
## f. DevTool / Workflow 工具

### 通用追问（各档通用）
- **正常开发流程**：使用者用它的标准流程是几步？入口命令 / 触发方式是什么？
- **产物文件**：会生成 / 修改哪些文件？产物落在哪个目录？
- **与 Git / CI / Spec / Issue 的关系**：是否读写 git、触发 CI、消费 spec / issue？集成点在哪？
- **是否改代码 / 生成文档**：直接改用户代码，还是只生成文档 / 配置？改动范围与可逆性如何？

### 🔴 深度档专项：工作场景全景穷举

> **仅深度报告档需要**。目标是覆盖"用户能拿它干哪些活"，一个不漏。按「意图 → 入口 → 流程」三层展开：

1. **用户意图 / 任务清单**：穷举用户能用它完成哪些任务，每个意图一行（看证据不看名字）。
2. **每个意图 → 对应入口**：哪些命令 / 触发方式服务这个意图？（带 `path`）
3. **每个入口 → 主路径 + 分支路径**：完整流程，含成功 / 失败 / 降级 / 特殊输入等关键分支。

**要求**：
- 覆盖**全部入口**，不漏。
- 一个意图可能对应多个入口，一个入口也可能服务多个意图——如实交叉标注。
- 每条结论带 `path:line`。
- 与深度模板第 5 章「端到端流程」分工：第 5 章挑 1~2 条最核心流程**逐跳深追**；本节**广度覆盖**所有场景，流程可略粗（主路径 + 关键分支）。
````

- [ ] **Step 2（Edit B）: "如何先判断类型"小节补 g 类识别信号**

对 `codebase-analyzer/references/project-type-checklists.md` 执行 Edit：

old_string:
````
- **DevTool / Workflow 工具**：本身面向开发者，用来生成代码 / 文档、编排流程、对接 Git/CI/Issue。

> 判不出明确类型也没关系——写明"未匹配到专项类型"，只产出通用报告即可，不要硬套。
````

new_string:
````
- **DevTool / Workflow 工具**：本身面向开发者，用来生成代码 / 文档、编排流程、对接 Git/CI/Issue。
- **Claude Code 插件 / 扩展**：有 `.claude/` 目录、`SKILL.md`、`commands/*.md`、`settings.json` 里的 `hooks`、`agents/` 或 subagent 定义、`plugin.json` / `.claude-plugin/`。

> 判不出明确类型也没关系——写明"未匹配到专项类型"，只产出通用报告即可，不要硬套。
````

- [ ] **Step 3（Edit C）: 文件末尾追加 g 类专项**

> 锚点是 Edit A 追加的 f 类最后一行，因此本 Edit 必须在 Edit A 之后执行。

对 `codebase-analyzer/references/project-type-checklists.md` 执行 Edit：

old_string:
````
- 与深度模板第 5 章「端到端流程」分工：第 5 章挑 1~2 条最核心流程**逐跳深追**；本节**广度覆盖**所有场景，流程可略粗（主路径 + 关键分支）。
````

new_string:
````
- 与深度模板第 5 章「端到端流程」分工：第 5 章挑 1~2 条最核心流程**逐跳深追**；本节**广度覆盖**所有场景，流程可略粗（主路径 + 关键分支）。

---

## g. Claude Code 插件 / AI 编程工具扩展

> 含 skill / slash command / hooks / subagent 设计的项目。**仅深度报告档**做逐条完整解读。

### 判断依据（看证据，不看名字）
- `.claude/` 目录；`SKILL.md` 文件（skill 定义）
- `commands/*.md` 或 `.claude/commands/`（slash command）
- `settings.json` / `settings.local.json` 里的 `hooks` 配置，或 `hooks/` 目录
- `agents/` 目录或 subagent 定义
- `plugin.json` / `.claude-plugin/`（插件清单）

### 逐条画像模板（每个 skill / command / hook / subagent 统一画像）
- **是什么 + 触发条件**：skill 的 `description` / command 的调用方式 / hook 的匹配时机与事件 / subagent 的角色定位
- **输入输出 / 副作用**：吃什么、产出什么、有无写文件 / 改代码 / 执行命令等副作用
- **内部关键逻辑**：带 `path:line`，引用了哪些 references / 脚本 / 模板
- **依赖与协作**：调用谁、被谁调用

### 整体装配图
> 这些扩展件如何"**技术编排**"成一个整体——哪个 command 触发哪个 skill、hook 在什么时机插入、subagent 被谁调起。**技术视角**，区别于 f 类场景全景的用户视角。

### 条目多时：并行解读
> 条目较多、一次性解读会撑满上下文时，按 [parallel-strategy.md](parallel-strategy.md) 的「按扩展条目并行」节派子 agent 分批解读。
````

- [ ] **Step 4: 验证**

```bash
grep -n "### 通用追问（各档通用）" codebase-analyzer/references/project-type-checklists.md
grep -n "🔴 深度档专项：工作场景全景穷举" codebase-analyzer/references/project-type-checklists.md
grep -n "Claude Code 插件 / 扩展" codebase-analyzer/references/project-type-checklists.md
grep -n "## g. Claude Code 插件 / AI 编程工具扩展" codebase-analyzer/references/project-type-checklists.md
grep -n "逐条画像模板" codebase-analyzer/references/project-type-checklists.md
grep -n "整体装配图" codebase-analyzer/references/project-type-checklists.md
```
Expected: 每条有输出。

- [ ] **Step 5: Commit**

```bash
git add codebase-analyzer/references/project-type-checklists.md
git commit -m "专项清单新增Workflow场景穷举与g类Claude Code扩展

- f类新增深度档专项：意图→入口→主/分支穷举工作场景
- 判断小节补g类识别信号
- 新增g类：判断依据+逐条画像模板+装配图+并行解读指引"
```

---

## Task 3: 诉求 3 — parallel-strategy.md 新增「按扩展条目并行」

**Files:**
- Modify: `codebase-analyzer/references/parallel-strategy.md`（"聚合"节之后、"反例"节之前插入新节）

- [ ] **Step 1: 在"反例"节之前插入"按扩展条目并行"节**

对 `codebase-analyzer/references/parallel-strategy.md` 执行 Edit：

old_string:
````
## 反例（不要这样做）

❌ 把项目 `src/` 平均切成 5 份派给 5 个 agent —— 切到了高耦合点。
````

new_string:
````
## 变体：按扩展条目并行（服务 Claude Code 插件 / 扩展类项目）

> 上面的并行按"业务模块"切；当项目是 Claude Code 插件、含大量 skill / command / hook / subagent 时，改按"扩展条目"切。对应 [project-type-checklists.md](project-type-checklists.md) 的 g 类。

### 何时启用
- 深度报告档 + 命中 g 类（Claude Code 插件 / 扩展）+ 条目数较多（一次性逐条解读会撑满上下文）。

### 切分方式
- **按单个条目切**：一个 skill / command / hook / subagent 各派一个子 agent。
- **分批**：一批不超过 5~6 个；在同一条消息里发出该批全部 Agent 调用才会真并行。

### 给子 agent 的产出要求
- 单条目**画像简报**（按 g 类「逐条画像模板」：是什么+触发条件 / 输入输出+副作用 / 内部关键逻辑带 `path:line` / 依赖与协作）。
- 中文、结构化、~400 字，必填"未搞清楚 / 异常"一项。

### 主 agent 职责
- 聚合所有画像，统一术语、消除冲突。
- **自己画整体装配图**——装配图需要全局视角，不外包给子 agent。

### 退化
- 当前环境无子 agent 工具时，退化为顺序逐条解读，并在报告注明"未启用并行"。

---

## 反例（不要这样做）

❌ 把项目 `src/` 平均切成 5 份派给 5 个 agent —— 切到了高耦合点。
````

- [ ] **Step 2: 验证**

```bash
grep -n "变体：按扩展条目并行" codebase-analyzer/references/parallel-strategy.md
grep -n "按单个条目切" codebase-analyzer/references/parallel-strategy.md
grep -n "自己画整体装配图" codebase-analyzer/references/parallel-strategy.md
grep -n "## 反例（不要这样做）" codebase-analyzer/references/parallel-strategy.md
```
Expected: 前 3 条有输出；第 4 条恰好 1 条输出（"反例"节仍在，只是被下移）。

- [ ] **Step 3: Commit**

```bash
git add codebase-analyzer/references/parallel-strategy.md
git commit -m "并行策略新增按扩展条目并行变体

单条目切+分批5~6个+子agent回画像+主agent画装配图，服务g类项目"
```

---

## Task 4: 诉求 2/3 — 深度模板第 8 章追加专项骨架

**Files:**
- Modify: `codebase-analyzer/references/template-deep.md`（第 8 章末尾追加两个专项表骨架）

> 本任务集中改 template-deep 第 8 章，与 Task 1（第 9 章）锚点不重叠，顺序无关。

- [ ] **Step 1: 在第 8 章通用 8.x 段落后追加 Workflow 场景表 + g 类画像表 + 装配图**

对 `codebase-analyzer/references/template-deep.md` 执行 Edit：

old_string:
`````
### 8.x {{项目类型，如 "CLI 项目" / "Web 服务" / "Library / SDK" / "Agent 项目" / "MCP Server" / "DevTool / Workflow 工具"}}

- **判断依据**：{{为什么归为此类，给出依赖 / 入口 / 目录证据}}
- {{按该类型清单逐条作答，每条带 `path:line`；不适用的写"不适用（原因）"，没查清的写"未确认"}}
`````

new_string:
`````
### 8.x {{项目类型，如 "CLI 项目" / "Web 服务" / "Library / SDK" / "Agent 项目" / "MCP Server" / "DevTool / Workflow 工具" / "Claude Code 插件 / 扩展"}}

- **判断依据**：{{为什么归为此类，给出依赖 / 入口 / 目录证据}}
- {{按该类型清单逐条作答，每条带 `path:line`；不适用的写"不适用（原因）"，没查清的写"未确认"}}

#### 若命中 DevTool / Workflow 工具：工作场景全景（穷举）

> 按「意图 → 入口 → 流程」穷举所有工作场景（详见 [project-type-checklists.md](project-type-checklists.md) 的 f 类深度档专项）。

| 用户意图 / 任务 | 对应入口 | 主路径 | 关键分支 | 源码位置 |
|---|---|---|---|---|
| {{意图 1}} | {{命令 / 触发}} | {{主流程简述}} | {{失败 / 降级 / 特殊输入}} | `{{path:line}}` |
| … | … | … | … | … |

#### 若命中 Claude Code 插件 / 扩展：扩展件逐条画像 + 装配图

> 每个 skill / command / hook / subagent 逐条画像（详见 [project-type-checklists.md](project-type-checklists.md) 的 g 类）。条目多时按 [parallel-strategy.md](parallel-strategy.md) 的「按扩展条目并行」派子 agent。

| 条目 | 类型 | 触发条件 | 输入 → 输出 | 内部关键逻辑 | 依赖 / 被依赖 |
|---|---|---|---|---|---|
| {{名称}} | skill / command / hook / subagent | {{触发}} | {{入 → 出}} | `{{path:line}}` | {{协作关系}} |
| … | … | … | … | … | … |

**整体装配图**：

```
{{ASCII：command → skill → subagent → hook 的编排关系，5~15 行看懂全貌}}
```
`````

- [ ] **Step 2: 验证**

```bash
grep -n "若命中 DevTool / Workflow 工具：工作场景全景" codebase-analyzer/references/template-deep.md
grep -n "若命中 Claude Code 插件 / 扩展：扩展件逐条画像" codebase-analyzer/references/template-deep.md
grep -n "整体装配图" codebase-analyzer/references/template-deep.md
```
Expected: 每条有输出。人工核对两个表格与装配图 fenced code block 闭合正确。

- [ ] **Step 3: Commit**

```bash
git add codebase-analyzer/references/template-deep.md
git commit -m "深度模板第8章追加Workflow场景表与扩展件画像表+装配图骨架"
```

---

## Task 5: 串联 — SKILL.md + 全局一致性（建议最后做）

**Files:**
- Modify: `codebase-analyzer/SKILL.md`（第 2 步类型列表、第 5 步自检、相关参考、措辞同步）

- [ ] **Step 1: 第 2 步项目类型列表补 g 类**

对 `codebase-analyzer/SKILL.md` 执行 Edit：

old_string:
````
- **CLI 项目**、**Web 服务**、**Library / SDK**、**Agent 项目**、**MCP Server**、**DevTool / Workflow 工具**
````

new_string:
````
- **CLI 项目**、**Web 服务**、**Library / SDK**、**Agent 项目**、**MCP Server**、**DevTool / Workflow 工具**、**Claude Code 插件 / 扩展**
````

- [ ] **Step 2: 标准档自检措辞同步（适合度评估 → 综合评价）**

对 `codebase-analyzer/SKILL.md` 执行 Edit：

old_string:
````
- [ ] 识别了项目类型并做了专项分析？（判不出写"未匹配"）适合度评估给了吗？
````

new_string:
````
- [ ] 识别了项目类型并做了专项分析？（判不出写"未匹配"）综合评价（含项目亮点）给了吗？
````

- [ ] **Step 3: 深度档自检追加 3 条检查项**

对 `codebase-analyzer/SKILL.md` 执行 Edit：

old_string:
````
**🔴 深度报告档**：
- [ ] 模板全部章节都在、没有省略标题？空章节写了"未搞清楚 / 不适用（原因）"？
- [ ] 标准档的全部检查项是否也都满足？（深度档是标准档的超集）
- [ ] 配置/环境变量、可观测性、安全等深度档独有章节是否完整填写或标注不适用？
````

new_string:
````
**🔴 深度报告档**：
- [ ] 模板全部章节都在、没有省略标题？空章节写了"未搞清楚 / 不适用（原因）"？
- [ ] 标准档的全部检查项是否也都满足？（深度档是标准档的超集）
- [ ] 配置/环境变量、可观测性、安全等深度档独有章节是否完整填写或标注不适用？
- [ ] 综合评价章（第 9 章）是否给出**项目亮点**，且每条落到 `path:line`（不是泛泛"架构清晰"）？
- [ ] 若命中 **DevTool / Workflow 工具**：是否按「意图 → 入口 → 主/分支」**穷举了工作场景全景**？
- [ ] 若命中 **Claude Code 插件 / 扩展**：是否**逐条画像 + 画了整体装配图**？条目多时是否用了并行（或注明未启用）？
````

- [ ] **Step 4: 相关参考区两行描述同步**

对 `codebase-analyzer/SKILL.md` 执行 Edit：

old_string:
````
- [references/project-type-checklists.md](references/project-type-checklists.md) —— 按项目类型（CLI / Web / SDK / Agent / MCP / DevTool）的专项分析清单
- [references/parallel-strategy.md](references/parallel-strategy.md) —— 大项目分阶段 / 并行调研策略
````

new_string:
````
- [references/project-type-checklists.md](references/project-type-checklists.md) —— 按项目类型（CLI / Web / SDK / Agent / MCP / DevTool / Claude Code 扩展）的专项分析清单
- [references/parallel-strategy.md](references/parallel-strategy.md) —— 大项目分阶段 / 并行调研策略（含"按扩展条目并行"变体）
````

- [ ] **Step 5: 全局措辞残留排查**

```bash
grep -rn "适合度评估\|适合程度评估" codebase-analyzer/
```
Expected: 无输出。若任何文件里还有"适合度评估 / 适合程度评估"作为**章节名/自检项**残留，逐条改为"综合评价"。

确认 g 类与自检新项已落地：
```bash
grep -n "Claude Code 插件 / 扩展" codebase-analyzer/SKILL.md
grep -n "穷举了工作场景全景" codebase-analyzer/SKILL.md
grep -n "逐条画像 + 画了整体装配图" codebase-analyzer/SKILL.md
```
Expected: 每条有输出。

- [ ] **Step 6: Commit**

```bash
git add codebase-analyzer/SKILL.md
git commit -m "SKILL串联三项增强

第2步补g类、第5步自检补亮点/场景穷举/画像3项、相关参考与评价章措辞同步"
```

---

## 收尾验证（全部任务完成后）

- [ ] **跨文件一致性检查**

```bash
# 三档模板/清单章名统一为综合评价
grep -rn "综合评价" codebase-analyzer/references/
# g 类在 checklist / 模板 / SKILL 三处都出现
grep -rn "Claude Code 插件" codebase-analyzer/
# 并行变体被 g 类正确引用，无断链
grep -n "按扩展条目并行" codebase-analyzer/references/project-type-checklists.md codebase-analyzer/references/parallel-strategy.md
# 旧章名彻底清除
grep -rn "适合度评估\|适合程度评估" codebase-analyzer/
```
Expected: 前 3 组有交叉一致的输出；最后 1 组无输出。

- [ ] **人工核对 template-deep.md**：通读第 8、9 章，确认 9.1→9.6 编号连续、两个专项表骨架格式正确、所有 fenced code block 完整闭合。

- [ ] **git 历史核对**：`git log --oneline -6` 应看到 5 个增强 commit（Task 1–5 各一）顺序在 spec commit 之后。

---

## Self-Review（写计划后自检，已完成）

**1. Spec coverage（spec 每节 → 任务映射）：**
- spec §3 诉求 1 亮点 → Task 1 ✅
- spec §4 诉求 2 Workflow：清单 → Task 2；模板 → Task 4 ✅
- spec §5 诉求 3：g 类清单 → Task 2；并行 → Task 3；模板 → Task 4 ✅
- spec §6 SKILL 串联 + 措辞同步 → Task 5 ✅
- spec §7 验收标准 → 各任务验证步骤 + 收尾验证 ✅
- spec §8 Non-goals（不新建文件、不进 quick 档、不泛化）→ 计划未触碰这些，符合 ✅

**2. Placeholder scan：** 计划内 `{{}}` 均为**写进 skill 模板的骨架示例**（本就要保留供未来报告填充），非计划自身的未完成项。无 TBD/TODO。✅

**3. Type consistency（命名一致性）：**
- 章名统一"综合评价"（deep 9 章 / standard 8 章 / checklist 9 章 / SKILL 自检）。
- 类型名统一"Claude Code 插件 / 扩展"（SKILL 第 2 步、checklist 判断小节与 g 类标题、模板 8.x、parallel-strategy）。
- 并行节名统一"按扩展条目并行"，Task 2（g 类引用）与 Task 3（节定义）一致。
- 任务间文件/锚点无重叠，已消除原稿中 Task 2/3 的跨任务锚点依赖。✅
