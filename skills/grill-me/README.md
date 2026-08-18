# Grill Me

## 用途

对一个计划、设计或决定做不留情面的访谈。把决策建成一棵**设计树**，按**轮次**推进：
每轮把所有前置已定、当下就问得动的问题（frontier）一次问完，每题都附上你的推荐答案；
用户回答后重算 frontier，问下一轮。直到设计树再无未访问的分支。

## 触发场景

本 skill **只由人类用户显式启动**：

- Claude Code：`/grill-me`（作为插件安装时使用带插件命名空间的命令）。
- Codex：`$grill-me` 或对应的显式 skill 选择入口。

`disable-model-invocation: true` 与 `allow_implicit_invocation: false` 使模型不会自行触发它。

## 核心行为

- **设计树 + 轮次**：每个决策分叉出挂在它下面的决策；依赖本轮未定问题的问题，留到后面的轮次。
- **整轮批量提问**：一轮问完整个 frontier，编号 `❓ **Q1**`，每题跟一行 `➡️ 推荐答案`，然后等回答。
- **事实自己查**：需要环境事实时派 subagent 去查，绝不问用户他不必回答的东西；
  探查不阻塞本轮，只有它下游的问题等结果。
- **决策交给用户**：逐条摆出来，等他定。
- **frontier 空了才算完**：每个分支都访问过，没有东西被默默假设；用户确认达成共同理解前不采取行动。

## 与参考实现的差异

移植自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `productivity/grill-me`
与 `productivity/grilling`（MIT，见 `LICENSE.upstream`）。差异：

- **两层合一**：上游把用户入口（`grill-me`，正文只有一句 `Call the Skill tool with "grilling"`）
  与可复用访谈原语（`grilling`，模型可隐式触发）拆成两个 skill；本仓库只提供单个 `grill-me`，
  正文即完整实现，并继承上游 `grill-me` 那层的禁隐式调用策略。因此本仓库没有 `grilling`，
  也没有对应的 `grill-with-docs` 组合。
- 全部改写为中文，问题格式的 `❓` / `➡️` 标记与上游一致。
- 访谈机制（设计树、轮次、frontier、subagent 查事实且不阻塞、frontier 空即结束、确认前不行动）
  与上游 `grilling` 逐条对齐，未增删规则。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/grill-me/`；
Codex：`.agents/skills/grill-me/`）即可使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `agents/openai.yaml`：Codex 的展示名称、简短描述与调用策略。
- `LICENSE.upstream`：上游 MIT 许可证副本。
