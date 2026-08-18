# Re-Explain

## 用途

上一条回复没能让人听懂时，**换一条路径重讲一遍**：补上缺的上文，用简明中文表达，术语沿用
项目里已经在用的说法，并且比原文更短。

不是重复，不是重排版，也不是把术语换成同义词再说一次。

## 触发场景

本 skill **由人类用户显式启动**：

- Claude Code：`/re-explain`（作为插件安装时使用带插件命名空间的命令）。
- Codex：`$re-explain` 或对应的显式 skill 选择入口。

`disable-model-invocation: true` 与 `allow_implicit_invocation: false` 使模型不会自行触发它。

可以直接点明卡点：`/re-explain 第二段没看懂`，这时只重讲那一段。

## 核心行为

- **先判断卡在哪**：缺上文 / 听不懂内容 / 不知道跟自己有什么关系，三选一；判断不出来就补上文。
- **四段结构**：落点先行 → 一句话结论 → 分点展开 → 一个具体例子。
- **简明中文**：一句一意、30 字以内、主动语态、一个概念一个词、拆名词堆、删模糊限定、先解释再比喻。
- **术语沿用不另造词**：按 `CONTEXT.md` → `CLAUDE.md` → `AGENTS.md` → `README.md` → 术语表 → 代码命名的顺序找既有说法。
- **必须更短**，不辩解，不追加新信息，不为了好懂而降低准确性，不顺势动手改东西。

## 与参考实现的差异

设计参考 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `productivity/wait-what`
（MIT，见 `LICENSE.upstream`）。上游是一条极简指令：重讲、补上下文、使用 ASD-STE100
简化技术英语、沿用 `CONTEXT.md` 的统一术语。按中文语境重新设计后的差异：

- **ASD-STE100 没有中文对应标准**，改为一套可逐条检查的简明中文约束，另附病句对照表，
  落在 `references/plain-chinese.md`。其中"拆名词堆""少用'的'字套娃""结论前置"是中文特有的问题，
  英文规范里没有对应条目。
- **术语来源本地化**：上游只指向 `CONTEXT.md`；本实现给出中文项目里更常见的查找顺序，
  并要求新起的说法必须明说，因为"听不懂"常常正是上一条回复造了词。
- **补了卡点分类与重讲结构**：上游把"重讲"整个交给模型自由发挥；本实现固定为三类卡点判断
  加四段结构，避免重讲变成重排版。
- **补了硬规则与反例**，与本仓库其他 skill 的写法保持一致；其中"必须更短"是把上游隐含的
  意图显式化。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/re-explain/`；
Codex：`.agents/skills/re-explain/`）即可使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/plain-chinese.md`：简明中文改写规则、病句对照表与重讲前自查。
- `agents/openai.yaml`：Codex 的展示名称、简短描述、默认提示词与调用策略。
- `LICENSE.upstream`：参考实现的上游许可证。
