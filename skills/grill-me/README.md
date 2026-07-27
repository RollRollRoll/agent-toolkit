# Grill Me

## 用途

通过一次一个问题的高强度访谈，沿决策依赖逐项压力测试用户的想法、计划或设计，主动暴露隐藏假设、矛盾、取舍与失败风险，直到双方明确确认已达成共同理解。

## 触发场景

本 skill **只能由人类用户通过平台入口显式启动**：

- Claude Code：直接安装时使用 `/grill-me`；作为插件安装时使用带插件命名空间的命令。
- Codex：使用 `$grill-me` 或对应的显式 skill 选择入口。

普通自然语言提到“压力测试计划”不会触发本 skill。模型、其他 skill、agent、subagent、自动路由、CI、定时任务和自治循环均不得调用或复用它。

## 核心行为

- 一次只问一个问题，并等待回答后再决定下一条分支。
- 每个问题都附推荐答案、理由和主要代价。
- 能从环境查到的事实先自行查证，只把真正的决策交给用户。
- 按依赖关系优先处理上游、高影响、难逆的决定。
- 在用户明确确认共同理解前，不执行计划或自动进入其他工作流。
- 不提供 `grilling` 配套 skill，也不作为其他 skill 的共享访谈原语。

## 与参考实现的差异

设计参考 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `grill-me` / `grilling` 工作流。上游当前把用户入口与可复用访谈原语拆为两个 skill；本仓库明确不采用该拆分，也不允许其他 skill 复用访谈能力。这里只提供单个、完整且仅限人类显式调用的 `grill-me`。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/grill-me/`；Codex：`.agents/skills/grill-me/`）即可使用。Claude Code 通过 `disable-model-invocation: true` 禁止模型调用；Codex 通过 `policy.allow_implicit_invocation: false` 禁止隐式调用。正文还会检查调用来源并拒绝代理链路或自动化调用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `agents/openai.yaml`：Codex 的展示名称、简短描述、默认提示词与调用策略。
