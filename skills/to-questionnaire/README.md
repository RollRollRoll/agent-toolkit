# To Questionnaire

## 用途

把一件**用户一个人答不出来**的事，变成一份**问卷**——一份 Markdown 文档，
可以异步发给某个人填，也可以拿着它开一次会一起填完。知识在收件人手里，问卷负责把它挖出来。

## 触发场景

本 skill **由人类用户显式启动**：

- Claude Code：`/to-questionnaire`（作为插件安装时使用带插件命名空间的命令）。
- Codex：`$to-questionnaire` 或对应的显式 skill 选择入口。

`disable-model-invocation: true` 与 `allow_implicit_invocation: false` 使模型不会自行触发它。

## 核心行为

- **盘问"发送"，不盘问"主题"**：只问用户一定答得上来的两件事——发给谁、要拿回什么。
- 两次交换定下收件人画像与需求清单，然后直接起草，不把用户拖进他本来就答不了的细节。
- 问题对准**收件人知道、而用户不知道**的那段缺口。
- 最重要的问题排最前（异步只有一次机会），一题一个意思，每题下面留空的 `>` 答题位。
- 落盘为 `to-questionnaire-<slug>.md` 并报告路径；只产出问卷，不替用户执行背后的决策。

## 与参考实现的差异

设计参考 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `productivity/to-questionnaire`
（MIT，见 `LICENSE.upstream`）。差异：

- 全部改写为中文，产出的问卷默认也用中文（收件人使用其他语言时整份切换）。
- 上游把问卷模板内联在 `SKILL.md` 里；本仓库按既有约定拆到 `references/questionnaire-template.md`，
  并补了一份写完自查清单。
- 补充了硬规则、完成标准与反例三节，与本仓库其他 skill 的写法保持一致。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/to-questionnaire/`；
Codex：`.agents/skills/to-questionnaire/`）即可使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/questionnaire-template.md`：问卷模板与写完自查清单。
- `agents/openai.yaml`：Codex 的展示名称、简短描述、默认提示词与调用策略。
- `LICENSE.upstream`：参考实现的上游许可证。
