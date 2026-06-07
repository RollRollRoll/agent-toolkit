# 项目类型专项分析清单

> 在第 1 步自顶向下扫读后，**先判断项目属于哪一类**，再按对应小节追加专项分析。
> 判断类型同样要看证据（依赖清单、入口、目录结构），**不要凭项目名或 README 猜**。
> 一个项目可能同时命中多类（如 "Web 服务 + 运维 CLI"），命中几类就追加几类，并各自说明判断依据。
> 本清单是在所选档报告模板（[template-standard.md](template-standard.md) / [template-deep.md](template-deep.md)，对应"项目类型专项分析"章节）之上的"加餐"，通用章节照常写。快速概览档一般省略专项分析。

---

## 如何先判断类型（看证据，不看名字）

- **CLI 项目**：依赖含 `argparse`/`click`/`cobra`/`commander`/`yargs`；`package.json` 的 `bin` 字段 / `pyproject.toml` 的 `[project.scripts]` / `cmd/` 目录。
- **Web 服务**：依赖含 `express`/`fastapi`/`flask`/`spring-boot`/`gin`/`nest`；有路由注册 / controller；启动时监听端口。
- **Library / SDK**：以"被别人 import"为目的，无独立长驻入口；`package.json` 有 `main`/`exports` 而无 `bin`；发布到 npm / PyPI / crates / Maven。
- **Agent 项目**：依赖含 `langchain`/`langgraph`/`autogen`/`crewai` 或某家 LLM SDK；代码里有 prompt 模板、tool 注册、agent 循环。
- **MCP Server**：依赖含 `@modelcontextprotocol/sdk` 或 `mcp`；声明 tools/resources/prompts；走 stdio / SSE / HTTP transport。
- **DevTool / Workflow 工具**：本身面向开发者，用来生成代码 / 文档、编排流程、对接 Git/CI/Issue。
- **Claude Code 插件 / 扩展**：有 `.claude/` 目录、`SKILL.md`、`commands/*.md`、`settings.json` 里的 `hooks`、`agents/` 或 subagent 定义、`plugin.json` / `.claude-plugin/`。

> 判不出明确类型也没关系——写明"未匹配到专项类型"，只产出通用报告即可，不要硬套。

---

## a. CLI 项目

- **命令清单**：有哪些命令 / 子命令？在哪注册的（给路径）？
- **参数解析**：用什么库？参数 / 选项 / 标志怎么定义？必填项与默认值在哪？
- **命令 → 业务逻辑**：每个命令映射到哪个函数 / handler（给路径）？
- **输出格式**：输出到 stdout 还是文件？纯文本 / 表格 / JSON / 彩色 TTY？退出码约定是什么？

## b. Web 服务

- **API 路由**：全部路由在哪注册？列出主要路由 → handler 映射（给路径）。
- **分层**：是否有 Controller / Service / Repository（或等价）分层？各层职责与目录。
- **数据库模型**：核心实体定义在哪？ORM 还是裸 SQL？迁移目录在哪？
- **认证鉴权**：身份从哪传入（cookie/header/token）？在哪个中间件校验？授权模型是什么？
- **部署方式**：Dockerfile / compose / k8s / Serverless？怎么发布？

## c. Library / SDK

- **对外 API / public interface**：公开导出在哪（`index.ts` / `__init__.py` / `mod.rs` 的 re-export）？哪些是 public、哪些是 internal？
- **示例用法**：README / `examples/` / 文档里给的最小可用示例是什么？
- **版本兼容性**：如何做语义化版本？有无 deprecation 标记、breaking change 记录（CHANGELOG）？支持的运行时 / 语言版本范围？
- **扩展方式**：使用者怎么扩展（插件 / 回调 / 子类化 / 配置注入）？扩展点在哪定义？

## d. Agent 项目

- **Agent 角色**：有几个 agent？各自承担什么角色（给定义位置）？
- **Prompt**：system / 角色 prompt 写在哪？硬编码、模板还是外部文件？
- **Tool**：注册了哪些工具？工具的 schema / 实现在哪？怎么被调用？
- **Memory / Context**：有无记忆机制？短期 / 长期记忆存哪？context 怎么拼装与裁剪？
- **Planner / Executor / Reviewer**：是否区分规划、执行、复核角色？各自在哪实现？
- **状态流转**：一次任务的状态机 / 循环怎么走？终止条件是什么（给代码位置）？
- **多 Agent 协作**：多个 agent 之间怎么协作（编排 / 对话 / 黑板 / 主从）？协作逻辑在哪？
- **多轮交互**：是否支持多轮对话 / 持续会话？轮次状态存哪？
- **副作用能力**：agent 是否会读写代码、执行命令、访问网络 / 文件系统？这些能力在哪声明与触发？
- **输出可追溯性**：agent 的产出能否追溯到源码 / 文档依据，还是纯生成？有无引用 / 证据机制？
- **安全护栏**：是否有防幻觉（事实校验 / 引用约束）、防越权（权限边界）、防误操作（危险操作确认 / 沙箱）的机制？在哪实现？
- **可集成性**：是否适合 / 已经接入 MCP、OpenSpec、CI/CD 或代码审查流程？集成点在哪？

## e. MCP Server

- **能力清单**：提供哪些 tools / resources / prompts？各自定义在哪？
- **transport**：stdio / SSE / HTTP？在哪初始化？
- **tool schema**：每个 tool 的输入输出 schema 怎么声明？参数校验在哪？
- **权限边界**：能访问哪些资源？有无路径 / 操作白名单、危险操作确认？
- **外部系统连接**：连了哪些外部系统（DB / API / 文件系统）？连接配置在哪？

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
- 与深度模板第 5 章「端到端代表性流程」分工：第 5 章挑 1~2 条最核心流程**逐跳深追**；本节**广度覆盖**所有场景，流程可略粗（主路径 + 关键分支）。

---

## g. Claude Code 插件 / 扩展

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
