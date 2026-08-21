# skills/support/

## 这个目录装什么

**不直接产出代码的辅助能力**，三类：

1. **面向人的思考工具**——对象是用户的想法、计划、决策，产出是想清楚了的东西，不是代码。
2. **agent 自身的工程**——维护 agent 环境本身：配置同步、skill 盲测。
3. **通用小工具**——跨场景可用、跟软件开发没有必然关系的日常能力。

判断标准一句话：**它的对象不是这个仓库要开发的代码**。是代码就去 `../development/`。

## 当前成员

| skill | 类别 | 入口 | 职责 |
|---|---|---|---|
| `grilling` | 面向人 | 被调用 | 对计划、决策或想法持续深入追问，做一次彻底的压力测试 |
| `grill-me` | 面向人 | 仅人类（`disable-model-invocation`） | `grilling` 的 standalone 入口，传"不剪枝"（技术分支也问） |
| `create-questionnaire` | 面向人 | 仅人类 | 把用户自己答不出来的事，做成一份交给知情人填的 Markdown 问卷 |
| `re-explain` | 通用小工具 | 仅人类 | 补充上下文，用更简单、明确的中文重新解释一遍 |
| `teach` | 通用小工具 | 仅人类 | 把当前目录当有状态的教学工作区，跨会话产出自包含 HTML 课与参照文档 |
| `agent-config-sync` | agent 自身工程 | 用户直呼 | 从现有配置抽取统一声明，据此安全同步 Codex 与 Claude Code 的用户级配置 |
| `test-skill` | agent 自身工程 | 用户直呼 | 在隔离沙箱中对某个 skill 发起 headless 盲测，产出逐步骤溯源的复盘报告 |
| `handoff` | agent 自身工程 | 仅人类 | 把当前对话压成交接文档，存进系统临时目录供新 agent 接手 |
| `writing-for-agents` | agent 自身工程 | 模型可触发 | 写给 agent 读的文档的参照：上下文指针、两种负担、信息层级、完成判据、引导词、修剪 |

## 一个目录内的两种入口

这里同时住着两种 skill，看 frontmatter 区分：

- **带 `disable-model-invocation: true`**：只给人用的入口，模型不会自己触发，
  用户敲 `/<name>` 才进来。
- **不带的**：模型可以按 `description` 自行判断触发，或被别的 skill 当能力单元调用
  （`grilling` 就被 `../development/refine-idea` 调）。

`grilling` / `grill-me` 是这套设计的样板：**实现住在可被调用的那个，人类入口是薄壳**，
同一套访谈机制，只有"剪不剪技术分支"这一个参数不同。

## 和 `../development/` 的边界

分界在**对象**，不在难度，也不在"是否严肃"：

| 场景 | 归属 | 为什么 |
|---|---|---|
| 追问用户的技术方案 | `support/grilling` | 对象是用户的思路 |
| 把想清楚的方案写成规格 | `development/write-spec` | 产出进仓库、成为代码依据 |
| 审查一段改动 | `development/review-changes` | 对象是代码 |
| 盲测一个 skill 执行得对不对 | `support/test-skill` | 对象是 agent 自己的资源 |

## 新增时

放进 `skills/support/<skill-id>/`，主体文件 `SKILL.md`。纯人类入口记得加
`disable-model-invocation: true`，否则模型会在不该触发时触发。**换分类就是移动目录**。
