# Report template: standard investigation tier

> This is the default **standard investigation** skeleton. The goal is to help the reader build a complete mental model while keeping length and irrelevant detail under control.
> Use it when the user did not say how deep to go. Lighter → [template-quick.md](template-quick.md);
> deliverable-grade full report → [template-deep.md](template-deep.md).
>
> **Principles**:
> - Cover every main section. For content that does not concern the project, write one line; do not expand pointless subsections.
> - Attach source paths to key conclusions. For what you have not figured out yet, write "未搞清楚（原因）" (not figured out, with reason); for what you confirmed does not apply, write "不适用（原因）" (not applicable, with reason).
> - Keep the end-to-end flow; it is the most information-dense part of the report.
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
> | `7. 项目类型专项分析` | Project-type analysis |
> | `8. 综合评价` | Overall assessment |
> | `9. 未搞清楚的部分 / 假设 / 已知问题` | Unclear parts / assumptions / known issues |

---

# 项目调研报告：{{project name}}

> **调研对象**：`{{absolute path or repository URL}}` ｜ **时间**：{{YYYY-MM-DD}} ｜ **读者**：对项目不熟悉的工程师

---

## 目录

- [一页纸概览](#一页纸概览)
- [1. 项目定位与功能](#1-项目定位与功能)
- [2. 整体架构](#2-整体架构)
- [3. 技术栈](#3-技术栈)
- [4. 代码结构与核心实现](#4-代码结构与核心实现)
- [5. 端到端代表性流程](#5-端到端代表性流程)
- [6. 配置、依赖与运行](#6-配置依赖与运行)
- [7. 项目类型专项分析](#7-项目类型专项分析)
- [8. 综合评价](#8-综合评价)
- [9. 未搞清楚的部分 / 假设 / 已知问题](#9-未搞清楚的部分--假设--已知问题)

---

## 一页纸概览

- **一句话定义**：{{what it does, who it is for}}
- **核心价值**：{{which problem it solves}}
- **架构风格**：{{monolith / microservices / CLI / library / event-driven ...}}
- **主要技术栈**：{{language + key frameworks + database, all on one line}}
- **运行形态**：{{long-running server / CLI / scheduled job / SDK / frontend ...}}
- **代码规模感**：{{order of magnitude of lines / number of modules / monorepo or not}}

```text
{{architecture sketch in ASCII, 5-10 lines that show the whole picture}}
```

---

## 1. 项目定位与功能

### 1.1 定位与核心价值
{{which pain point it solves, who it is for, how it differs from existing solutions}}

### 1.2 功能地图

| 功能 | 触发方式 | 入口 | 核心实现 | 输入 → 输出 | 已源码确认 |
|---|---|---|---|---|---|
| {{feature}} | {{CLI / HTTP / call / event}} | `{{path:line}}` | `{{path:line}}` | {{in → out}} | 是 / 否 |

### 1.3 主要输入与输出
- **输入**：{{HTTP / CLI / files / messages ...}}
- **输出**：{{responses / database writes / files written / downstream messages ...}}

---

## 2. 整体架构

### 2.1 架构风格
{{monolith / layered / event-driven ...; give the evidence for the judgment, not just a label}}

### 2.2 主要模块

| 模块 | 路径 | 职责 | 依赖 |
|---|---|---|---|
| {{module}} | `{{path}}` | {{one sentence}} | {{modules / external systems it depends on}} |

### 2.3 数据流与控制流
- **数据流**：{{where data enters, which modules it passes through, where it ends up}}
- **控制流**：{{what drives execution (router / main loop / state machine), when it ends, how errors propagate, whether there is retry or fallback. If none, write "单次执行后退出" (exits after a single run)}}

### 2.4 与外部系统的交互
{{database / cache / third-party APIs / object storage ...; for each, its purpose + call site `path:line`. If none, write "不适用" (not applicable)}}

---

## 3. 技术栈
- **语言与框架**：{{main language + version (with evidence) + core frameworks + what they are used for}}
- **数据存储与中间件**：{{database / cache / message queue, and where they are configured}}
- **关键三方库**：{{list only libraries that shape the architecture, and where they are used}}

---

## 4. 代码结构与核心实现

### 4.1 目录地图

```text
{{root directory}}/
├── {{dir1}}/   # {{responsibility}}
├── {{dir2}}/   # {{responsibility}}
└── …
```
> 划分逻辑：{{by layer / by business domain / monorepo by package ...}}

### 4.2 程序入口与启动流程
{{the key steps in time order from the start command until the first request / task can be handled, with `path:line`}}

### 4.3 数据模型
- **核心实体与关系**：{{e.g. `User 1:N Order`}}
- **定义位置**：`{{path}}`，迁移在 `{{path}}`

### 4.4 核心业务逻辑 / 关键算法
- **位置**：`{{path:line}}`
- **思路**：{{written description; paste a 10-30 line key snippet only when needed}}

### 4.5 对外暴露的接口
{{HTTP routes / CLI commands / SDK functions / message events; list the main ones + where they are defined}}

---

## 5. 端到端代表性流程

> Guidance: **this is the most information-dense section; do not skip it**. Pick 1-2 flows that best show the core value and connect them hop by hop from entry point to output.

### 流程 A：{{flow name}}
**触发**：{{client action / timer / message / CLI}}

```text
[入口] {{path:line}}
   ↓ {{parsing / middleware}}
[层 1] {{path:line}}   # {{what it does; data shape}}
   ↓
[出口] {{path:line}}   # {{response / database write / message sent}}
```

**关键点**：{{where authentication / transaction boundaries / failure handling happen}}

---

## 6. 配置、依赖与运行

- **关键配置 / 环境变量**：{{the few most important variable names + purpose + required or not + where loaded; no real values or sensitive defaults; the full list belongs to the deep tier}}
- **依赖的外部服务**：{{which are required, which are optional with fallback}}
- **本地跑起来**：{{prerequisites → install `command` → configure → start `command` → how to verify}}
- **构建与部署**：{{build command / artifacts / deployment method / where CI is defined}}

---

## 7. 项目类型专项分析

> Guidance: judge the type (CLI / Web / SDK / Agent / MCP / DevTool) per [project-type-checklists.md](project-type-checklists.md).
> Write one subsection per matched type, each with its evidence. If no type matches, write "未匹配到专项类型" (no specific type matched). Every conclusion carries `path:line`.

### 7.x {{project type}}
- **判断依据**：{{dependency / entry point / directory evidence}}
- {{answer the checklist for that type item by item}}

---

## 8. 综合评价
- **项目亮点**：{{the cleverest / most distinctive / most worth-learning designs, with `path:line`; a technical-appreciation view, distinct from "优点" (strengths) below}}
- **优点 / 局限（决策视角）**：{{key points for each, based on facts from the source}}
- **适合 / 不适合场景**：{{which scenarios it suits, which to avoid}}
- **是否值得二次开发**：{{worth it / with caution / not recommended + evidence + where to start}}

---

## 9. 未搞清楚的部分 / 假设 / 已知问题

> Guidance: **do not omit this section**.

- **未搞清楚**：{{points still unclear after reading `path` + suggested way to confirm}}
- **做出的假设**：{{assumptions and the reasons for them}}
- **已知技术债 / 显眼 TODO**：{{location + symptom}}
