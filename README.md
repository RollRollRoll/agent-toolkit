# agent-toolkit

中文 | [English](README.en.md)

个人 agent 工具资源仓库，用于管理自己创建的 `skill`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
Claude Code 通过 `.claude-plugin/` 发布，Codex 通过 `.codex-plugin/` 和
`.agents/plugins/` 发布；两平台直接加载根目录 `skills/` 下的同一套 Skill。

Skill 文件（`SKILL.md`、`references/`、`agents/openai.yaml`）统一用英文编写；
明确要求中文产出的 skill（如 `codebase-analyzer`、`test-skill` 的报告，
`re-explain`、`create-questionnaire`）仍输出中文。本 README 提供中文版和
[英文版](README.en.md)。

## Skill 一览

每个 skill 是一个单一职责的能力单元，谁需要谁调，没有固定的编排链。
下表按**使用场景**分组。「触发」列标 **仅人类** 的，模型不会自己调（frontmatter 带
`disable-model-invocation: true`），只有你敲 `/<name>` 才进来；标「模型可触发」的，
模型会按 `description` 自行判断，也可能被别的 skill 当能力单元调用。

### 立项与规划

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `setup-env` | **仅人类** | 第一次在某个仓库用这套 skill 之前 | 配好 issue tracker、triage 标签词汇与领域文档布局，写进 `docs/agents/` 与 `CLAUDE.md` |
| `triage` | **仅人类** | issue 与外部 PR 堆着，要判它们各自该走向哪 | 让它们走过 triage 角色状态机：分类、验证、必要时拷问，落成 agent brief 或 `.out-of-scope/` 记录 |
| `wayfinder` | **仅人类** | 一块工作大到一次会话装不下，路还裹在雾里 | 把它绘成 issue tracker 上的决策工单地图，一次解一张直到路清晰 |
| `grill-demand` | **仅人类** | 有个想法要从头聊透，聊完直接出 spec | 按覆盖清单把问题与范围、行为、技术决策逐层钉死，边聊边落 ADR 与术语表 |
| `to-spec` | **仅人类** | 一场讨论已经把要做什么聊清楚了 | 不再访谈，把当前对话综合成 spec（含 seam 决策）发布到 issue tracker 并打 `ready-for-agent` |
| `to-tickets` | **仅人类** | 计划 / spec 定了，要变成 tracker 上的工单 | 拆成曳光弹式纵向切片，每张声明阻塞边，按依赖顺序发到 tracker 并打 `ready-for-agent` |

### 设计与探路

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `codebase-design` | 模型可触发 | 要设计或改进某个模块的接口，判 seam 该放哪 | 提供深模块设计词汇与判据：接口深浅、seam 位置、深化路径、多版接口对比 |
| `domain-modeling` | 模型可触发 | 术语在打架，或要把定下来的说法与决策记下来 | 打磨项目领域语言，术语当场写进 `GLOSSARY.md`，难逆且反直觉的决策留成 ADR |
| `improve-codebase-architecture` | **仅人类** | 想系统地找出代码库里值得深化的地方 | 扫出深化机会做成可视化 HTML 报告，再就选中的那一个拷问到底 |
| `prototype` | 模型可触发 | 某个设计问题想不清楚，要用一次性代码验一验 | 逻辑分支做可分享的单 HTML 演示，界面分支在一条路由上出几个根本不同的变体 |
| `codebase-analyzer` | 模型可触发 | 接手一个陌生项目，要先全局搞懂它 | 全面调研并产出说明它做什么、怎么实现的结构化中文报告 |
| `research` | 模型可触发 | 编码前要把某个技术事实核准，并留下可复查的依据 | 派后台 agent 查一手来源，把带逐项引用的结论落成仓库里的单个 Markdown |

### 动手实现

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `setup-worktree` | 模型可触发 | 动手前要隔离工作区，或多条开发线并行 | 基于确定基线建立并验证隔离的 git worktree |
| `implement` | **仅人类** | 手上已有 spec 或工单，要直接把它做出来 | 照 spec / 工单实现：尽量用 `tdd` 在约定 seam 上做，收尾跑 `code-review`，再提交到当前分支 |
| `implement-spec` | **仅人类** | spec 已拆成关联工单，要一次执行完全部工单 | 按阻塞关系并行调度独立 worktree 中的子 agent（各自用 `tdd` 实现），逐个合入集成分支，整体审查；tracker 通过 PR 关闭工作时再开 PR |
| `tdd` | 模型可触发 | 要用测试先行的方式落地一段行为改动 | 红 → 绿循环的参照：什么算好测试、seam 定在哪、反模式、循环规则 |
| `diagnosing-bugs` | 模型可触发 | 有个难缠的 bug 或性能回退要定位 | 先造出能变红的紧回路，再复现、最小化、排假设、埋点，修完留回归测试 |
| `wizard` | 模型可触发 | 有些步骤只有人能做：开服务、拿密钥、点第三方控制台 | 生成交互式 bash 向导逐阶段带人走完，并把捕获到的值写进 `.env` / GitHub secret |

### 审查与收口

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `code-review` | 模型可触发 | 要审一段改动守不守规范、做的是不是 issue / spec 要的东西 | 双轴审查：标准轴（成文规范 + Fowler 坏味道基线）与规格轴各派并行 subagent，结果并排不合并 |
| `finish-branch` | 模型可触发 | 开发完了，分支 / worktree 该怎么收口 | 清理调试代码、跑最终测试，再由用户拍板合并 / 保留 / 开 PR / 丢弃 |
| `pr` | 模型可触发 | 要写 PR 正文 | 用最小的可视化说明改动，给出改动前后的证据，判断是单向门还是双向门（能否回退）以及影响范围 |
| `git-commit-push` | 模型可触发 | 要解冲突，或把已完成的改动拆成原子提交并推送 | 语义解冲突；或检查敏感信息与异常差异后拆成原子提交，确认后推送 |

### 帮人想清楚一件事

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `grilling` | 模型可触发 | 一个计划、决策或想法要被压力测试 | 持续深入地追问，把含糊处逼出来 |
| `grill-me` | **仅人类** | 你想让人拷问自己手上的方案 | `grilling` 的手动入口，多传一个「不剪枝」（技术分支也照问） |
| `create-questionnaire` | **仅人类** | 有些事你自己答不出来，得问知情人 | 把这些问题做成一份交给对方填的 Markdown 问卷 |
| `notify-doctor` | 人类 / agent | Telegram 通知收不到，或想看当前生效的通知配置 | 逐项检查配置、凭据、日志和 Bot 可达性，给出修复建议；只读，不发消息 |
| `notify-setup` | 人类 / agent | 第一次配置或更换 Telegram Bot | 给出配置向导命令，在你的终端里校验 token、获取 chat_id 并写入配置 |
| `notify-test` | 人类 / agent | 想确认 Telegram 通知配置是否正确 | 发送一条测试通知，报告成功或失败原因 |
| `re-explain` | **仅人类** | 上一段解释没看懂 | 补充上下文，用更简单、明确的中文重新解释一遍 |
| `teach` | **仅人类** | 想学一项新技能或新概念 | 把当前目录当有状态的教学工作区，跨会话产出自包含 HTML 课与参照文档 |

### 维护 agent 自身

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `writing-for-agents` | 模型可触发 | 要写或改 skill、`AGENTS.md`、`CLAUDE.md` | 写给 agent 读的文档的参照：上下文指针、两种负担、信息层级、完成判据、引导词、修剪 |
| `test-skill` | 模型可触发 | 想知道某个 skill 实际执行成什么样 | 在隔离沙箱中发起 headless 盲测，产出逐步骤溯源的中文复盘报告 |
| `retro` | **仅人类** | 一次编程会话结束，要找出工作环境与规则的改进点 | 读取会话记录，检查导航、自动检查、编码规范、指令、工具效率与信息访问，按严重程度提出建议；原样引入上游技能 |
| `agent-config-sync` | 模型可触发 | 多台机器 / 两个 CLI 的配置要对齐 | 从现有配置抽出统一声明，据此安全同步 Codex 与 Claude Code 的用户级配置 |
| `handoff` | **仅人类** | 当前会话装不下了，要换个 agent 接着做 | 把这场对话压成交接文档，存进系统临时目录供新 agent 接手 |

## Skill 之间怎么互相调用

一段开发的自然顺序（**只是阅读次序，不是调用约束**）：

```text
grill-demand → to-spec → to-tickets → implement → finish-branch
     │                                     │
     └─ grilling · domain-modeling         └─ tdd · code-review
```

现有的调用点：

| 调用方 | 调用点 | 被调 skill |
|---|---|---|
| `grill-me` | 人类入口薄壳 | `grilling` |
| `grill-demand` | 供 `to-spec` 的上游访谈 | `grilling` + `domain-modeling` |
| `implement` | 每段行为改动 | `tdd` |
| `implement` | 收尾审查 | `code-review` |
| `implement-spec` | 每个实现子 agent 完成工单 | `tdd` |
| `implement-spec` | 全部工单集成后的整体审查 | `code-review` |
| `finish-branch` | 创建 PR 时撰写正文 | `pr` |
| `retro` | 复盘开始时查阅写作规则 | `writing-for-agents` |

调用约定：

- **调用即交出判据定义权**：调用方不重述被调 skill 的规则，需要细节就去读那个 skill。
- **门禁归调用方**：被调 skill 只产内容并交回，"过没过、要不要往下"由调用方判定；
  它们对缺前置的处理是回 **BLOCKED**，不是自己补上游的活。
- **调用不等于派 subagent**：默认在调用方自己的上下文里加载执行；需要 fresh 上下文时
  由调用方显式派发并定档。
- **被调 skill 不可用时判据不变**：由调用方按同一套判据自己走一遍并说明降级原因。
- **产物落盘目录由调用方决定**：被调 skill 的脚本都接受可选输出目录，缺省落在自己的
  自忽略点目录（如 `.tdd/`）。
- 能不能被别的 skill 调用，由 `SKILL.md` 里的「调用契约」章节体现，没有单独的声明文件。

## 安装（Claude Code）

在 Claude Code 中执行：

```text
/plugin marketplace add RollRollRoll/agent-toolkit
/plugin install agent-toolkit@agent-toolkit
```

整个工具包作为单一插件 `agent-toolkit` 安装，按需启用方式：

- 插件级：`/plugin` 交互界面，或 `claude plugin enable|disable agent-toolkit`。
- skill 级：在 `/permissions` 中添加 deny 规则，如 `Skill(codebase-analyzer)`。

## 安装（Codex）

在 Codex CLI 中执行：

```text
codex plugin marketplace add RollRollRoll/agent-toolkit
codex plugin add agent-toolkit@agent-toolkit
```

也可以在 Codex CLI 的 `/plugins` 或 Codex App 的 Plugins 界面中，从已添加的
`agent-toolkit` marketplace 安装。安装或更新后新开任务，让 Codex 重新加载 Skill。

## Agent 通知（Telegram）

安装插件后，Claude Code 与 Codex CLI 在下列事件发生时向你的 Telegram 发送通知。一条通知长这样（正文默认折叠，点开展开）：

```text
🔐 agent-toolkit @ mbp
需要授权 · Codex · main · 1a2b3c4d
▸ Bash: curl -H "Authorization: Bearer ***" https://x
```

第一行是事件图标、项目和主机，系统弹窗里一眼就能看出来源；第二行依次是事件、Agent、git 分支、会话短 ID，缺的字段直接省略。

回合摘要（Agent 的回复）里的 Markdown 会转成 Telegram 支持的格式：粗体、行内代码、http(s) 链接、代码块照常显示，标题转成粗体，无序列表转成 `•`，分隔线去掉；有序列表、引用、斜体、表格保留原文。命令预览和错误详情不做转换，按原文显示。

| 事件 | 图标 | Claude Code | Codex CLI |
|---|---|---|---|
| 回合完成 | ✅ | 支持 | 与等待输入合并为「回合结束，等待输入」，通知里显示为「回合结束」 |
| 等待输入 | 💬 | 回合结束后约 60 秒无人回应；回合中途 MCP 服务器请求输入 | 同上 |
| 需要授权 | 🔐 | 授权提示出现约 6 秒仍未处理时才发，及时处理的不推送；用 AskUserQuestion 向你提问时也按这一类通知；auto 模式下不弹提示，也就不发 | 授权请求一出现就发 |
| 异常 | ❌ | 回合因 API 等错误终止 | 不支持 |

发送前会把正文和会话标题里的凭据替换成 `***`，覆盖 bot token、`Authorization` 头、常见密钥前缀、`password=` 这类键值、URL 里的密码。规则是固定的，不能保证覆盖所有格式；不想让正文经过 Telegram，就关掉 `include_summary` / `include_tool_detail`，或开启隐私模式。

### 配置

推荐在你自己的终端运行向导 `python3 <插件目录>/hooks/notify/bin/notify-setup.py`（或用 `notify-setup` skill 获取命令）。它会校验 token、自动获取 chat_id、询问可选的主机标签、以 600 权限写入配置文件并发送测试通知。向导里直接回车会保留已有的主机标签；要清除它，需手动编辑配置文件。

也可以手动编辑 `~/.config/agent-notify/config.json`（建议 `chmod 600`）。除 `telegram` 外的配置项都可以省略：

```json
{"telegram": {"token": "123:ABC", "chat_id": "42"},
 "host_label": "mbp",
 "events": {"turn_complete": true, "waiting_input": true, "permission": true, "error": true},
 "include_summary": true, "include_tool_detail": true, "privacy": false,
 "summary_max_chars": 1000, "request_timeout": 10, "log_level": "info"}
```

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `host_label` | 机器名第一个 `.` 之前的部分 | 通知里显示的主机名，多台电脑共用一个 Bot 时用来区分 |
| `events` | 全部开启 | 按事件类型关闭通知；Codex 的「回合结束，等待输入」要 `turn_complete` 和 `waiting_input` 都关闭才不发 |
| `include_summary` | `true` | 是否发送回合摘要、等待输入的提示、错误详情和会话标题 |
| `include_tool_detail` | `true` | 是否发送授权的命令预览 |
| `privacy` | `false` | 隐私模式，开启时等于上面两项都关 |
| `summary_max_chars` | `1000` | 正文最多多少字符，上限 3500 |
| `request_timeout` | `10` | 每条通知的发送总时限（秒），范围 1–60，含重试 |
| `log_level` | `info` | `error` 只记失败；`info` 另记每条通知的结果和耗时；`debug` 另记被跳过的事件及原因 |

布尔项写成字符串时，`"false"`、`"0"`、`"no"`、`"off"` 和空串视为关闭。非法值按默认值或边界值处理。

环境变量优先于配置文件：`AGENT_NOTIFY_TELEGRAM_TOKEN`、`AGENT_NOTIFY_TELEGRAM_CHAT_ID`、`AGENT_NOTIFY_PRIVACY`，以及指定配置文件和日志路径的 `AGENT_NOTIFY_CONFIG`、`AGENT_NOTIFY_LOG`。

### 测试与诊断

- 用 `notify-test` skill（或 `python3 hooks/notify/bin/notify-test.py`）发送一条测试通知。
- 收不到通知时，用 `notify-doctor` skill（或 `python3 hooks/notify/bin/notify-doctor.py`）诊断。它会逐项检查配置文件、权限、凭据来源、各配置项的生效值、Python 版本、日志，以及 Bot 是否可达（`getMe`、`getChat`），并给每个问题附上修复建议。它只读，不发消息，token 只显示首尾 4 位。
  - 符号：✅ 正常、⚠️ 值得注意、❌ 需要修复、⏭️ 因前置条件不满足而跳过；💡 开头的行是固定提示，不算检查项。
  - 退出码：0 表示没有 ❌，1 表示至少有一个 ❌，2 表示参数错误。
  - `--offline` 只做本地检查，不联网。
  - 日志里最近一次发送失败之后如果已有成功发送，这一项显示为「已恢复」。

### 其他

- Codex 首次使用，以及每次升级本插件后，都需要在 `/hooks` 中重新信任本插件的 hooks，否则不会触发通知；即使 hooks 配置本身没有变化也一样。Claude Code 无需额外操作。
- 只做单向通知，不会改变 Agent 的执行或审批；发送失败只记录到 `~/.local/state/agent-notify/notify.log`，不补发。
- 要求 Python ≥ 3.9，支持 macOS 与 Linux。

## 目录结构

```text
agent-toolkit/
  .claude-plugin/
    plugin.json
    marketplace.json
  .codex-plugin/
    plugin.json
  .agents/plugins/
    marketplace.json
  skills/
    development/<skill-id>/
      SKILL.md
      references/
      scripts/
    support/<skill-id>/
```

- `.claude-plugin/`：Claude Code 插件与市场清单。
- `.codex-plugin/`：Codex 插件清单。
- `.agents/plugins/`：Codex 仓库级 marketplace 清单。
- `skills/`：两平台共用的完整 Skill，成员与职责见上面的「Skill 一览」。

## 新增 Skill

1. 建目录 `skills/development|support/<skill-id>/`，主体文件 `SKILL.md`，
   辅助资料放 `references/`，脚本放 `scripts/`，Codex 侧的界面描述放 `agents/openai.yaml`。
   资源目录内不再单独写 `README.md` 或 `metadata.yaml`，说明以主体文件为唯一来源。
2. `SKILL.md` 的 frontmatter 写清 `name`（与目录名一致）和 `description`
   （决定模型认不认得出该用它）；只给人用的入口加 `disable-model-invocation: true`。
   若它会被别的 skill 调用，正文还要写明调用契约（传入 / 取回 / 不做什么）。
3. `description` 用英文书写，统一用「动词描述能力」模版（Action + Object）：
   动词开头、紧跟宾语、一句话说清做什么、句号收尾，
   不用介词或时间状语开场（如 When / For / By / Using），也不加分类标签前缀。
   `agents/openai.yaml` 的 `short_description` 同样用英文并遵守这条模版。
   从上游移植的 skill 例外：`description` 和 `short_description` 可以直接沿用上游原文，便于以后同步。
4. 随插件发布时：
   - 更新 `.claude-plugin/plugin.json` 的 `skills` 数组（路径含目录名，
     如 `./skills/development/tdd`）；
   - 确认 `.codex-plugin/plugin.json` 的 `skills` 指向根目录 `skills/`
     （它按目录扫描，新增 skill 无需改这一项）；
   - 同步递增 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`
     与 `.codex-plugin/plugin.json` 的版本。
5. 在 `README.md` 和 `README.en.md` 的「Skill 一览」里各补一行：什么时候用、它做什么。

## 当前非目标

- 不自动改写用户机器上的 Claude Code / Codex 已安装副本。
- 不做 CLI。
- 不做 schema 校验。
- 不做自动打包、发布或安装流程。
- 不做跨平台格式转换。
