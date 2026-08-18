# Grill Me

## 用途

**人类专用入口**：对一个计划、设计或决定发起一次不留情面的访谈。本 skill 自己不定义访谈规则，
它调用 composable 层的 **[grilling](../grilling/)**，并把范围设为**全部展开、不剪枝**——
技术选型、架构、实现路线都在树内。

访谈机制（设计树、轮次、frontier、事实自查、frontier 空即止）住在 `grilling` 里，改规则改那边。

## 触发场景

本 skill **只由人类用户显式启动**：

- Claude Code：`/grill-me`（作为插件安装时使用带插件命名空间的命令）。
- Codex：`$grill-me` 或对应的显式 skill 选择入口。

`disable-model-invocation: true` 与 `allow_implicit_invocation: false` 使模型不会自行触发它。
模型自己想找人对齐时应当直接用 `grilling`，而不是走这个入口。

## 调用契约

| 方向 | 内容 |
|---|---|
| 传入 | 当前对话里的访谈对象、范围＝全部展开、已定事实与约束、交回形态＝口头结论不落盘 |
| 取回 | 已定决策清单、树的终态（穷尽 / 挂起）、暴露的假设与风险、用户是否已显式确认 |
| 不做 | 不实现、不落盘、不替用户决策、不自动调下游 skill（判据见 `grilling`） |

## 与参考实现的差异

移植自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `productivity/grill-me`
与 `productivity/grilling`（MIT，见 `LICENSE.upstream`）。两层结构与上游一致：
入口层禁隐式调用，机制层可复用。差异：

- 全部改写为中文，问题格式的 `❓` / `➡️` 标记与上游一致。
- `grilling` 增加了上游没有的**范围（scope）与剪枝**约定，供 `refine-idea` 只展开概念层时使用；
  本 skill 作为入口传的是"不剪枝"，行为与上游等价。
- 未实现上游的 `grill-with-docs`（grilling + domain-modeling 的组合入口）。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/grill-me/`；
Codex：`.agents/skills/grill-me/`），**并同时安装 `grilling`**——缺了它本 skill 无事可做。

## 目录说明

- `SKILL.md`：入口本体（平台原生格式，含 frontmatter），正文只有调用契约。
- `agents/openai.yaml`：Codex 的展示名称、简短描述与调用策略。
- `LICENSE.upstream`：上游 MIT 许可证副本。
