# Report template: deep report tier

> This is the full skeleton for the **deep report**. For lighter output use instead:
> - Quick overview → [template-quick.md](template-quick.md)
> - Standard investigation → [template-standard.md](template-standard.md)
>
> Write the deep report in this template's chapter order and hierarchy, and keep every heading. When there is no content, say so explicitly:
> - **"未搞清楚（原因：…）"** (not figured out, reason: ...): you did not read it / cannot infer it / it needs confirmation from the business side (this is a blind spot).
> - **"不适用（原因：…）"** (not applicable, reason: ...): the project does not involve this item (this is a firm conclusion).
>
> Do not mix the two. When a conditional section does not concern the project, one line "不适用（原因）" is enough; no need for subheadings and placeholder content.
>
> **Speeding up the deep tier on large projects**: when investigating a large project, the descriptive chapters (1/2/3/4/6/7/8) can be handed to subagents to draft in parallel, while the main agent writes the one-page overview and chapters 5/9/10 itself,
> and output is streamed in phases. See "Variant: parallel drafting by report chapter" in [parallel-strategy.md](parallel-strategy.md). **The chapter structure, order, and hierarchy of this template do not change.**
>
> **How to fill this template** (same rules in all three templates):
> - Everything below the first `---` line is the report skeleton. Headings, bold field labels, table headers, and the `目录` links are **fixed Chinese strings**: copy them verbatim.
> - `{{...}}` placeholders describe what goes there, in English. Replace each one with Chinese content.
> - Blockquotes starting with `> Guidance:` are instructions for you. Do not copy them into the report.
> - English meaning of the fixed `##` headings (`###` subheadings are explained by the placeholders under them):
>
> | Heading | Meaning |
> |---|---|
> | `项目调研报告` | Project investigation report (report title) |
> | `目录` | Table of contents |
> | `一页纸概览` | One-page overview |
> | `1. 项目定位与功能` | Positioning and features |
> | `2. 整体架构` | Overall architecture |
> | `3. 技术栈` | Tech stack |
> | `4. 代码结构与核心实现` | Code structure and core implementation |
> | `5. 端到端代表性流程` | Representative end-to-end flows |
> | `6. 配置、依赖与运行` | Configuration, dependencies, and running |
> | `7. 工程实践与质量` | Engineering practice and quality |
> | `8. 项目类型专项分析` | Project-type analysis |
> | `9. 综合评价（亮点 / 适合度 / 二次开发）` | Overall assessment (highlights / fit / further development) |
> | `10. 未搞清楚的部分 / 假设 / 已知问题` | Unclear parts / assumptions / known issues |
> | `附录 A：调研路径回放（可选）` | Appendix A: investigation path replay (optional) |

---

# 项目调研报告：{{project name}}

> **调研对象**：`{{absolute path or repository URL}}`
> **调研时间**：{{YYYY-MM-DD}}
> **报告读者**：对项目不熟悉的工程师

---

## 目录

- [一页纸概览](#一页纸概览)
- [1. 项目定位与功能](#1-项目定位与功能)
- [2. 整体架构](#2-整体架构)
- [3. 技术栈](#3-技术栈)
- [4. 代码结构与核心实现](#4-代码结构与核心实现)
- [5. 端到端代表性流程](#5-端到端代表性流程)
- [6. 配置、依赖与运行](#6-配置依赖与运行)
- [7. 工程实践与质量](#7-工程实践与质量)
- [8. 项目类型专项分析](#8-项目类型专项分析)
- [9. 综合评价（亮点 / 适合度 / 二次开发）](#9-综合评价亮点--适合度--二次开发)
- [10. 未搞清楚的部分 / 假设 / 已知问题](#10-未搞清楚的部分--假设--已知问题)
- [附录 A：调研路径回放（可选）](#附录-a调研路径回放可选)

---

## 一页纸概览

> Guidance: the goal is that a reader who reads only this section grasps in 1 minute "what this project is, what it looks like, and what technology it is built with".

- **一句话定义**：{{one sentence on what the project does and who it is for}}
- **核心价值**：{{which problem it solves and what it means for users}}
- **架构风格**：{{monolith / microservices / separate frontend and backend / CLI tool / library / event-driven / serverless, etc.}}
- **主要技术栈**：{{language + key frameworks + database / middleware, all on one line}}
- **运行形态**：{{long-running server / one-shot CLI / scheduled job / SDK library / browser frontend / desktop app ...}}
- **代码规模感**：{{order of magnitude of lines, number of modules, monorepo or not}}

```text
{{architecture sketch in ASCII, 5-10 lines that show the whole picture}}
```

---

## 1. 项目定位与功能

### 1.1 解决什么问题
{{the pain points / workflow breaks users face without this project}}

### 1.2 目标用户
{{end users, developers, ops, a specific industry ...}}

### 1.3 核心价值
{{how it differs from existing solutions}}

### 1.4 功能地图

> Guidance: do not just list feature names. Tie each core feature to "how it is triggered, where it enters, what implements it, what goes in and out", and mark whether it was verified in the source.

| 功能 | 用户触发方式 | 入口文件 | 核心实现 | 输入 | 输出 | 已在源码确认 |
|---|---|---|---|---|---|---|
| {{feature 1}} | {{CLI command / HTTP request / function call / event}} | `{{path:line}}` | `{{path:line}}` | {{input shape}} | {{output shape}} | 是 / 否（仅据 README） |
| … | … | … | … | … | … | … |

### 1.5 主要用户流程
{{how users use the project in a typical scenario, 2-5 steps}}

### 1.6 功能边界
- **做什么**：{{capabilities clearly within the project's responsibility}}
- **不做什么**：{{capabilities clearly out of scope, to prevent misreading}}

### 1.7 主要输入与输出
- **输入**：{{HTTP requests / CLI arguments / files / messages / events ...}}
- **输出**：{{HTTP responses / stdout / files / database writes / downstream messages ...}}

---

## 2. 整体架构

### 2.1 架构风格
{{monolith / microservices / separate frontend and backend / event-driven / layered / hexagonal / CQRS ...; give the evidence for the judgment, not just a label}}

### 2.2 主要模块 / 服务
| 模块 | 路径 | 职责 | 对外暴露 | 依赖 |
|---|---|---|---|---|
| {{module name}} | `{{path}}` | {{one-sentence responsibility}} | {{API / functions / events}} | {{modules or external systems it depends on}} |
| … | … | … | … | … |

### 2.3 模块间通信
{{in-process function calls / HTTP / gRPC / message queue / shared database ...; give one or two concrete call sites for each kind}}

### 2.4 数据流
{{where data goes after it enters, which modules it passes through, where it ends up: a written description + a simplified flow diagram}}

### 2.5 控制流
> Guidance: data flow answers "where does the data go"; control flow answers "what drives execution, when does it end, what happens on error".

- **主入口如何调度**：{{after the entry point receives a request / command, how is it dispatched to the handling logic (route table / command dispatch / task queue)}} `{{path:line}}`
- **主循环 / 状态机**：{{is there a long-running main loop, event loop, or state machine, and how do states change}} `{{path:line}}` {{if none, write "无，单次执行后退出" (none, exits after a single run)}}
- **异常如何冒泡**：{{how errors pass upward from lower layers; is there unified error handling / a catch-all}} `{{path:line}}`
- **任务何时结束**：{{the normal termination condition (request returns / command finishes / stop signal received)}}
- **失败处理**：{{is there retry / rollback / fallback / circuit breaking, and where is it implemented}} `{{path:line}}` {{if none, write "无" (none)}}

### 2.6 与外部系统的交互
| 外部系统 | 用途 | 调用方式 | 调用点 |
|---|---|---|---|
| {{e.g. PostgreSQL / Redis / S3 / third-party API}} | {{what it is used for}} | {{protocol / SDK}} | `{{path:line}}` |

---

## 3. 技术栈

### 3.1 语言与框架
- **主语言**：{{language + version, with the evidence you read, e.g. `python = "^3.11"` in `pyproject.toml`}}
- **核心框架**：{{framework + version + purpose}}
- **次要框架 / 工具链**：{{ORM / template engine / build tool / package manager ...}}

### 3.2 数据存储与中间件
| 类别 | 选型 | 用途 | 配置位置 |
|---|---|---|---|
| 数据库 | {{e.g. PostgreSQL 14}} | {{primary storage / business data}} | `{{path}}` |
| 缓存 | {{e.g. Redis}} | {{purpose}} | `{{path}}` |
| 消息队列 | {{e.g. Kafka / RabbitMQ}} | {{purpose}} | `{{path}}` |
| 搜索 | … | … | … |

### 3.3 关键三方库
> Guidance: list only libraries that **shape the architecture** or **carry core business capability**. Small utility libraries need not be listed.

| 库 | 作用 | 在哪里用 |
|---|---|---|
| {{lib}} | {{why the project cannot do without it}} | `{{path}}` |

### 3.4 部署与基础设施
- **运行环境**：{{container / bare metal / serverless / Kubernetes ...}}
- **构建产物**：{{binary / image / npm package / static site ...}}
- **基础设施定义**：{{location of Dockerfile / docker-compose / k8s manifests / Terraform / CDK}}

---

## 4. 代码结构与核心实现

### 4.1 目录结构与模块划分逻辑

```text
{{project root}}/
├── {{dir1}}/         # {{responsibility of this directory}}
│   ├── {{subdir}}/   # {{sub-responsibility}}
│   └── …
├── {{dir2}}/         # …
└── …
```

> 划分逻辑：{{by layer (controller/service/repo) / by business domain / modules in a monorepo / hybrid ...}}

### 4.2 关键文件 / 目录地图

> Guidance: do not list everything; **highlight what matters**: where the reader should look for "entry point, core algorithm, external interfaces, data models".

| 文件 / 目录 | 角色 | 备注 |
|---|---|---|
| `{{path}}` | 程序入口 | {{evidence that it is the entry point}} |
| `{{path}}` | 路由 / 接口注册 | {{which routes it contains}} |
| `{{path}}` | 核心业务逻辑 | {{what the core does}} |
| `{{path}}` | 数据模型定义 | {{ORM / schema}} |
| `{{path}}` | 配置加载 | {{which environment variables it reads}} |
| … | … | … |

### 4.3 程序入口与启动流程
{{what happens between the start command and the point where the first request / task can be handled, in time order}}

1. `{{path:line}}`：{{what it does}}
2. `{{path:line}}`：{{what it does}}
3. …

### 4.4 数据模型 / Schema
- **核心实体**：{{entity 1, entity 2, ...}}
- **关系**：{{text + a simple ER description, e.g. `User 1:N Order N:1 Product`}}
- **定义位置**：`{{path}}`、迁移在 `{{path}}`

### 4.5 核心业务逻辑 / 关键算法
{{the implementation most essential to the project's unique value, including but not limited to scheduling algorithms, matching rules, state machines, parsers, inference pipelines}}

- **位置**：`{{path:line}}`
- **思路**：{{written description of the core idea; avoid pasting large blocks of code; paste a 10-30 line key snippet only when needed}}
- **复杂度 / 性能敏感点**：{{if any}}

### 4.6 对外暴露的接口

> Guidance: list all externally exposed capabilities: HTTP / gRPC / GraphQL / CLI commands / SDK functions / message events, etc.

| 类型 | 名称 / 路径 | 描述 | 定义位置 |
|---|---|---|---|
| {{REST}} | `GET /api/xxx` | {{what it does}} | `{{path:line}}` |
| {{CLI}} | `xxx run` | {{what it does}} | `{{path:line}}` |
| … | … | … | … |

---

## 5. 端到端代表性流程

> Guidance: **the most information-dense chapter of the report**. Pick 1-2 flows that best show the project's core value and connect them end to end from entry point to output.

### 流程 A：{{flow name, e.g. "user login request"}}

**触发**：{{client action / timer / message / CLI call}}

**调用链**：

```text
[入口] {{path:line}}
   ↓ {{argument parsing / middleware}}
[层 1] {{path:line}}     # {{what it does; data shape}}
   ↓
[层 2] {{path:line}}     # {{what it does}}
   ↓ {{calls external system}}
[层 3] {{path:line}}     # {{what it does}}
   ↓
[出口] {{path:line}}     # {{response / database write / message sent}}
```

**关键点**：
- {{at which step authentication / authorization checks happen}}
- {{where the transaction boundaries are}}
- {{where retry / fallback / rate limiting is handled}}
- {{possible failure points and how they are handled}}

### 流程 B：{{second flow, optional}}

{{optional: if one flow is enough to explain the project's core, omit this. If there is a clearly different second main line, such as read flow + write flow, or synchronous API + asynchronous job, add one.}}

---

## 6. 配置、依赖与运行

### 6.1 配置项与环境变量
> Guidance: take evidence only from example config and loading code. Do not read or copy real environment values; do not write credential defaults into the report as-is.

| 变量 | 含义 | 必填 | 加载位置 |
|---|---|---|---|
| `{{ENV_VAR}}` | {{purpose}} | 是 / 否 | `{{path:line}}` |

### 6.2 不同环境差异（dev / staging / prod）
{{which config files each environment uses / which variables are switched}}

### 6.3 依赖的外部服务与集成点
{{database, cache, third-party APIs, SSO, object storage ...; for each, state "can the project start without it / which features become unavailable"}}

### 6.4 构建与部署
- **本地构建**：`{{command}}`
- **打包产物**：`{{artifact path / image name}}`
- **部署方式**：{{CI-triggered / manual / GitOps ...}}
- **CI/CD 定义**：`{{path}}`

### 6.5 可观测性
- **日志**：{{logging library, log-level config, where output goes}}
- **监控 / 指标**：{{Prometheus / OpenTelemetry / custom instrumentation ..., where it is initialized}}
- **错误追踪**：{{Sentry / Bugsnag / in-house}}
- **trace / 链路追踪**：{{integrated or not}}

---

## 7. 工程实践与质量

### 7.1 测试
- **类型**：{{unit / integration / e2e / performance ...}}
- **框架**：{{pytest / jest / go test ...}}
- **目录**：`{{path}}`
- **运行方式**：`{{command}}`
- **覆盖度**：{{if there is coverage config / a coverage report, write the actual number, or "未读到" (not found)}}

### 7.2 本地开发环境搭建
> Guidance: by following the steps in this section, a newcomer should be able to get the project running.

1. 前置依赖：{{language version / tools / docker ...}}
2. 安装：`{{command}}`
3. 配置：{{whether to copy `.env.example`, which kinds of credentials to request; write only names and how to obtain them, never actual values}}
4. 启动：`{{command}}`
5. 验证：{{which URL to visit / what output means it is OK}}

### 7.3 文档现状
{{is the README complete; are there architecture docs, ADRs, API docs; are they up to date}}

### 7.4 代码质量信号
- **静态检查**：{{linter / formatter / type checker, and their config files}}
- **PR / commit 规范**：{{commit conventions or PR templates, if any}}
- **明显的 TODO / FIXME / HACK**：{{are they widespread, which areas they cluster in}}

### 7.5 认证与安全
- **认证机制**：{{session / JWT / OAuth / API key ..., where it is implemented}}
- **授权 / 权限模型**：{{RBAC / ABAC / custom}}
- **敏感数据处理**：{{confirm encryption / redaction / credential storage from config code, ignore rules, and file tracking status; do not read or show credential contents}}
- **常见安全考量**：{{CSRF / CORS / SQL injection protection / rate limiting ...; are they addressed}}

---

## 8. 项目类型专项分析

> Guidance: add the type-specific analysis for the project types identified per [project-type-checklists.md](project-type-checklists.md). Write one subsection per matched type,
> each with its evidence (go by evidence, not names). If no clear type matches, write "未匹配到专项类型（原因：…）" (no specific type matched, reason: ...) for this chapter. Every conclusion also needs a source path.

### 8.x {{project type, e.g. "CLI 项目" / "Web 服务" / "Library / SDK" / "Agent 项目" / "MCP Server" / "DevTool / Workflow 工具" / "Agent 编程工具插件 / 扩展（Claude Code / Codex）"}}

- **判断依据**：{{why it falls in this type, with dependency / entry point / directory evidence}}
- {{answer the checklist for that type item by item, each with `path:line`; write "不适用（原因）" for items that do not apply and "未确认" (not confirmed) for items you did not figure out}}

#### 若命中 DevTool / Workflow 工具：工作场景全景（穷举）

> Guidance: exhaustively list all work scenarios as "intent → entry point → flow" (see the deep-tier section of type f in [project-type-checklists.md](project-type-checklists.md)).
> **Division of work with chapter 5**: chapter 5 traces 1-2 core flows hop by hop; this table covers breadth, and the main path can be coarser.

| 用户意图 / 任务 | 对应入口 | 主路径 | 关键分支 | 源码位置 |
|---|---|---|---|---|
| {{intent 1}} | {{command / trigger}} | {{brief main flow}} | {{failure / fallback / special input}} | `{{path:line}}` |
| … | … | … | … | … |

#### 若命中 Claude Code / Codex 插件或扩展：扩展件逐条画像 + 装配图

> Guidance: profile each skill / command / hook / subagent / custom agent one by one,
> and mark its platform and discovery path (see type g in [project-type-checklists.md](project-type-checklists.md)).
> With many items, dispatch subagents per "Variant: parallel by extension item" in [parallel-strategy.md](parallel-strategy.md).

| 条目 | 类型 | 平台 / 发现路径 | 触发条件 | 输入 → 输出 | 内部关键逻辑 | 依赖 / 被依赖 |
|---|---|---|---|---|---|---|
| {{name}} | skill / command / hook / subagent / custom agent | {{Claude / Codex / both; manifest or directory}} | {{trigger}} | {{in → out}} | `{{path:line}}` | {{collaboration}} |
| … | … | … | … | … | … | … |

**整体装配图**：

```text
{{ASCII of how platform manifests → skills / commands → subagents / custom agents → hooks are orchestrated, 5-15 lines that show the whole picture; a technical-orchestration view, distinct from the user view of the scenario table}}
```

---

## 9. 综合评价（亮点 / 适合度 / 二次开发）

> Guidance: help the reader decide whether the project can be used, whether it is worth building on, and which designs are worth learning from. Base conclusions on facts from earlier chapters, not impressions.

### 9.1 项目亮点

> Guidance: the project's **cleverest / most distinctive / most worth-learning** designs, from a technical-appreciation view, distinct from "优点" (strengths) below, which is a decision view. Tie each one to a specific `path:line`, and explain **what is clever about it and why others find it hard to do this well**.
> Do not write a generic "clear architecture".

- {{highlight 1: e.g. an elegant abstraction / a unique algorithm / a clean extension mechanism / a smart engineering trade-off, `path:line`, and what is clever about it}}

### 9.2 项目优点（决策视角）
- {{strengths observed in the source / architecture, e.g. clear design, thorough tests, well-defined extension points}}

### 9.3 项目局限
- {{weaknesses observed, e.g. tight coupling, missing tests, outdated docs, hard dependency on a framework}}

### 9.4 适合使用场景
- {{scenarios where using it directly is appropriate}}

### 9.5 不适合使用场景
- {{scenarios where it is not recommended, and why}}

### 9.6 是否值得二次开发
- **结论**：{{值得 / 谨慎 / 不建议 (worth it / with caution / not recommended)}}
- **依据**：{{code readability, modularity, extension points, community activity, size of technical debt, etc.}}
- **二开切入点**：{{if worth it, which modules / extension points to start from; if not, what the alternative is}}

---

## 10. 未搞清楚的部分 / 假设 / 已知问题

> Guidance: **do not omit this section**. List everything you did not read, could not infer, or that needs confirmation from the business side. From this the reader knows which conclusions to trust and which to re-check.

### 10.1 未搞清楚（需要进一步确认）
- {{question 1}}
  - 我看了：`{{path}}`
  - 仍不明：{{the specific point still unclear}}
  - 建议确认方式：{{which document to read / whom to ask / what experiment to run}}

### 10.2 调研中做出的假设
- {{assumption 1, and why you made it}}

### 10.3 已知技术债 / 明显坏味道
- {{debt 1}}：位置 `{{path}}`，表现：{{symptom}}

### 10.4 显眼的 TODO / FIXME
- `{{path:line}}`：{{summary of the original text}}

---

## 附录 A：调研路径回放（可选）

> Guidance: if the user wants to check how deep your investigation went, list "which files I read / what I looked at in each file" here. After reading it, the reader can reproduce your investigation.

- `{{path}}`：用于确认 {{what it confirmed}}
- `{{path}}`：用于追踪 {{which flow it traced}}
- …
