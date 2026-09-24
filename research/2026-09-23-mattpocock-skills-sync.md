# mattpocock/skills 同步比对记录

比对日期：2026-09-23。

结论：目前没有发现已有移植技能必须补同步的上游改动。值得考虑的是新增 `retro` 与 `pr`，两者仍在上游实验目录；本地已有定制应保留。

## 依据与范围

- 本地基线：`8b5eb0d4b78b786d431fad0ec1f6b4bdc45620b4`，2026-09-14。
- 上游快照：[c55ee46073ed923f86ce59a5eb3b6d895095d1b7](https://github.com/mattpocock/skills/commit/c55ee46073ed923f86ce59a5eb3b6d895095d1b7)，2026-09-18。
- 本地提交 `0d2d63d` 的正文明确记载，上次比对使用上游 `3cca18b`（2026-09-04）。本次以这条可追溯记录为增量基线，同时检查当前技能正文和辅助资源，避免只依据提交日期判断。
- 上游共有 38 个技能：正式工程类 18 个、正式生产力类 7 个、实验类 9 个、杂项 4 个。本地共有 30 个技能，其中 25 个可对应上游技能，另 5 个为本地独有能力。
- 本次是静态内容与提交历史比对，不是技能执行效果测试，也不对文档内所有第三方 CLI 命令重新做兼容性验证。

从 `3cca18b` 到上游当前快照，净变化只有 7 个文件：两个 changeset、实验目录 README、`pr` 的三个文件，以及 `retro/SKILL.md`。正式技能目录没有净变化。可用以下只读命令复核：

```bash
git diff --name-status 3cca18b..c55ee46073ed923f86ce59a5eb3b6d895095d1b7
```

此命令应在上游仓库中运行。来源：[上游提交比较](https://github.com/mattpocock/skills/compare/3cca18b...c55ee46073ed923f86ce59a5eb3b6d895095d1b7)。

## 值得引入的内容

### 1. 优先考虑新增 retro

上游 8 月 24 日新增，9 月 15 日强化了自动检查相关规则。它根据实际编码会话，找出文件导航、信息访问、工具调用、指令文档和检查机制的问题，再向用户提出改进建议。

这与本地 `test-skill` 不同：后者验证某个技能在隔离场景中的执行效果，`retro` 则分析真实开发会话及其工作环境。它也不同于 `writing-for-agents`：后者提供写作规则，前者判断哪里需要改进。

最值得吸收的两点：

- 先检查仓库已有的 lint、类型检查、测试与 CI，区分“没有检查”和“检查已有但未接通或已失效”。
- 能通过固定规则判定的问题，优先交给确定性检查；需要判断的问题才写入供审查使用的规范。

建议作为仅由用户触发的 `skills/support/retro/` 引入，沿用上游先分析、再呈现候选的职责。检查机制的具体修改仍应遵循实际任务范围；不需要为了同步此技能给本仓库另建 CI。

来源：[retro 正文](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/retro/SKILL.md)、[9 月 15 日规则修改](https://github.com/mattpocock/skills/commit/0243b6e)。

### 2. 可选新增 pr，或由现有收尾技能引用其格式

上游 9 月 17 日新增，9 月 18 日仍在调整。当前内容是 PR 正文格式参照，主要包含：简洁的变更说明、修改前后证据、回滚难度和影响范围。适用时用图、伪代码、输出或截图解释行为。

本地 `finish-branch` 管分支收尾，`implement-spec` 管整份规格的实现和 PR 交付，目前没有独立的 PR 正文格式参照，因此存在补充价值。

建议先作为模型可触发的 `skills/development/pr/` 评估。保留本地直白中文风格，将上游有关回滚的比喻写成“是否容易回滚”等具体表达；格式详略应与实际变更相称。它只负责正文质量，创建或发布 PR 的授权仍由实际任务与调用方负责。

若移植，应同时保留上游 `metadata.credits`、`CREDITS.md` 中对 Humanlayer `show-me` 的来源说明，不能只复制模板。

来源：[pr 正文](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/SKILL.md)、[来源说明](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/CREDITS.md)。

两项均属于上游 `in-progress`，未列入正式插件技能清单。应按实验候选评估，不作为现有技能的必需补丁。上游实验目录 README 仍将 `retro` 描述为 STUB，但正文已有完整步骤，目录摘要存在滞后，应以正文和提交记录为依据。来源：[实验目录说明](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/README.md)、[上游插件清单](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/.claude-plugin/plugin.json)。

## 已有技能的核对结果

### 已完成的近期同步

| 项目 | 本地证据 | 结论 |
| --- | --- | --- |
| `grilling` 每轮问题间加分隔线 | [SKILL.md](../skills/support/grilling/SKILL.md)，本地提交 `0d2d63d` | 已包含上游 `85f83d3` |
| `wait-what` 沿 `CONTEXT-MAP.md` 找到相应术语表 | [re-explain/SKILL.md](../skills/support/re-explain/SKILL.md)，同一提交 | 已包含上游 `d6cd26f`，保留本地技能名 |
| `implement-spec` 并行实现、逐项合入、整体审查 | [SKILL.md](../skills/development/implement-spec/SKILL.md)，本地提交 `dc797d2`、`8b5eb0d` | 已包含上游 `84b5ee5` 与后续 `5b15a47` 修正，无更新遗漏 |

来源：[grilling 修改](https://github.com/mattpocock/skills/commit/85f83d3)、[wait-what 修改](https://github.com/mattpocock/skills/commit/d6cd26f)、[implement-spec 最后修正](https://github.com/mattpocock/skills/commit/5b15a47)。`implement-spec` 在上游也仍属于实验技能，本地引入它不意味着必须同步其他实验技能。

### 名称映射与应保留的定制

| 上游 | 本地 | 判断 |
| --- | --- | --- |
| `setup-matt-pocock-skills` | `setup-env` | 配置流程与模板齐全；本地将标签配置条件扩大到所有标签消费方，保留 |
| `grill-with-docs` | `grill-demand` | 本地增加分层访谈、覆盖清单，与 Delivery Spec 配套，保留 |
| `to-spec` | `to-spec` | 本地明确改用 Implementation-Ready Delivery Spec，保留需求、场景、决策与验证追踪 |
| `to-tickets` | `to-tickets` | 上游纵向切片、阻塞边、expand–contract 已覆盖；本地增加编号需求覆盖核对，保留 |
| `to-questionnaire` | `create-questionnaire` | 本地重写为中文问卷流程，保留已有约束，不按英文逐句覆盖 |
| `wait-what` | `re-explain` | 本地中文解释规则和 `plain-chinese.md` 为有意适配，保留 |
| `resolving-merge-conflicts` | `git-commit-push` 的冲突处理部分 | 核心语义合并能力已覆盖，并扩展操作识别、cherry-pick 和确认要求，无须重复引入 |

本地历史依据：`8568af6` 明确替换 spec 模板，`f1619db` 与 `77c11a1` 重构并改名访谈技能，`fb21ae7` 增加需求覆盖核对，`82b816c` 补齐初始化配置，`59f2e58` 重写问卷技能。对照来源：[上游工程技能](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering)、[上游生产力技能](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/productivity)。

其余已核对的对应技能为：`code-review`、`codebase-design`、`diagnosing-bugs`、`domain-modeling`、`implement`、`improve-codebase-architecture`、`prototype`、`research`、`tdd`、`triage`、`wayfinder`、`wizard`、`grill-me`、`handoff`、`teach`、`writing-for-agents`。连同前述条目，共覆盖本地 25 个对应技能。

核对包括相应的辅助 Markdown、脚本模板和 `agents/openai.yaml`。其中 `diagnosing-bugs` 的脱敏要求与 HITL 模板提醒已包含；tracker 模板、triage brief、拒绝请求记录和本地文件阻塞约定也已覆盖。

### 可选修正文案：TDD 的展示说明

[tdd/agents/openai.yaml](../skills/development/tdd/agents/openai.yaml) 将技能描述为“红、绿、重构循环”，[正文](../skills/development/tdd/SKILL.md) 第 52 行却明确将重构放在评审阶段。README 的技能一览也使用“红 → 绿循环”，三处说明不完全一致。

上游也存在同样差异，所以这不是漏同步。可以只将界面短描述调整为“确认测试边界，按纵向切片执行红绿循环”，与当前正文保持一致，无须改变执行规则。来源：[上游界面描述](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/agents/openai.yaml)、[上游正文](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md)。

## 其他未引入项

| 上游候选 | 建议 |
| --- | --- |
| `ask-matt` | 低优先级可选。它负责推荐使用哪个技能；若移植，应按本地名称和实际流程重写，不能照搬上游路由表。不是近期新增 |
| `claude-handoff` | 暂不引入。已有通用 `handoff`，另一个入口偏平台特定 |
| `loop-me` | 暂不引入。主要配置循环执行，需先有明确使用场景 |
| `setup-ts-deep-modules` | 按需。面向 TypeScript 依赖边界，非通用工具库的必需能力 |
| `writing-shape`、`writing-fragments`、`writing-beats` | 按需。偏内容写作，不是现有工程技能的更新 |
| `git-guardrails-claude-code` | 按需。平台特定的 Git 拦截机制，不能直接作为双平台统一规则 |
| `setup-pre-commit` | 按需。与 `retro` 的自动检查建议相关，但不应默认替所有项目安装钩子 |
| `migrate-to-shoehorn`、`scaffold-exercises` | 暂不引入。适用领域较窄 |

来源：[ask-matt](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/ask-matt/SKILL.md)、[实验技能目录](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress)、[杂项技能目录](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/misc)。以上取舍是基于本地仓库定位的建议，不是上游维护者的结论。

本地独有的 `codebase-analyzer`、`finish-branch`、`setup-worktree`、`agent-config-sync`、`test-skill` 没有对应的上游技能，不应当作上游已删除内容处理。

## 验证与后续维护

- 本地 30 个技能目录与 Claude 插件登记集合一致。
- 全部 30 个技能的 `disable-model-invocation` 与 `agents/openai.yaml` 中显式调用策略对应一致。
- 所核对移植技能中的本地 Markdown 文件链接未发现实际缺失；`context-format.md` 中三个上下文路径属于模板示例。
- 若新增技能，按本地 README 同时补齐中文正文、辅助资源、Codex 元数据、Claude 登记、技能一览和发布版本；本次不修改这些文件。
- 建议后续同步继续记录上游 SHA、名称映射和保留定制，避免仅按日期或英文文本差异覆盖本地内容。本报告可作为下一次比对的基线。

本次仅新增这份研究报告，未修改技能、发布配置或提交 Git 记录。
