# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、`command` 和 `hook`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
Claude Code 通过 `.claude-plugin/` 发布，Codex 通过 `.codex-plugin/` 和
`.agents/plugins/` 发布；两平台直接加载根目录 `skills/` 下的同一套 Skill，
不随插件自动加载 SSH MCP。

SSH MCP 配置仍保留在 `mcp/ssh-mcp.json`，仅供手动配置时使用。该文件不在
Claude Code 和 Codex 的插件默认发现位置，也未被插件清单引用。

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
| `domain-modeling` | 模型可触发 | 术语在打架，或要把定下来的说法与决策记下来 | 打磨项目领域语言，术语当场写进 `CONTEXT.md`，难逆且反直觉的决策留成 ADR |
| `improve-codebase-architecture` | **仅人类** | 想系统地找出代码库里值得深化的地方 | 扫出深化机会做成可视化 HTML 报告，再就选中的那一个拷问到底 |
| `prototype` | 模型可触发 | 某个设计问题想不清楚，要用一次性代码验一验 | 逻辑分支做可分享的单 HTML 演示，界面分支在一条路由上出几个根本不同的变体 |
| `codebase-analyzer` | 模型可触发 | 接手一个陌生项目，要先全局搞懂它 | 全面调研并产出说明它做什么、怎么实现的结构化中文报告 |
| `research` | 模型可触发 | 编码前要把某个技术事实核准，并留下可复查的依据 | 派后台 agent 查一手来源，把带逐项引用的结论落成仓库里的单个 Markdown |

### 动手实现

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `setup-worktree` | 模型可触发 | 动手前要隔离工作区，或多条开发线并行 | 基于确定基线建立并验证隔离的 git worktree |
| `implement` | **仅人类** | 手上已有 spec 或工单，要直接把它做出来 | 照 spec / 工单实现：尽量用 `tdd` 在约定 seam 上做，收尾跑 `code-review`，再提交到当前分支 |
| `tdd` | 模型可触发 | 要用测试先行的方式落地一段行为改动 | 红 → 绿循环的参照：什么算好测试、seam 定在哪、反模式、循环规则 |
| `diagnosing-bugs` | 模型可触发 | 有个难缠的 bug 或性能回退要定位 | 先造出能变红的紧回路，再复现、最小化、排假设、埋点，修完留回归测试 |
| `wizard` | 模型可触发 | 有些步骤只有人能做：开服务、拿密钥、点第三方控制台 | 生成交互式 bash 向导逐阶段带人走完，并把捕获到的值写进 `.env` / GitHub secret |

### 审查与收口

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `code-review` | 模型可触发 | 要审一段改动守不守规范、做的是不是 issue / spec 要的东西 | 双轴审查：标准轴（成文规范 + Fowler 坏味道基线）与规格轴各派并行 subagent，结果并排不合并 |
| `finish-branch` | 模型可触发 | 开发完了，分支 / worktree 该怎么收口 | 清理调试代码、跑最终测试，再由用户拍板合并 / 保留 / 开 PR / 丢弃 |
| `git-commit-push` | 模型可触发 | 要解冲突，或把已完成的改动拆成原子提交并推送 | 语义解冲突；或检查敏感信息与异常差异后拆成原子提交，确认后推送 |

### 帮人想清楚一件事

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `grilling` | 模型可触发 | 一个计划、决策或想法要被压力测试 | 持续深入地追问，把含糊处逼出来 |
| `grill-me` | **仅人类** | 你想让人拷问自己手上的方案 | `grilling` 的手动入口，多传一个「不剪枝」（技术分支也照问） |
| `create-questionnaire` | **仅人类** | 有些事你自己答不出来，得问知情人 | 把这些问题做成一份交给对方填的 Markdown 问卷 |
| `re-explain` | **仅人类** | 上一段解释没看懂 | 补充上下文，用更简单、明确的中文重新解释一遍 |
| `teach` | **仅人类** | 想学一项新技能或新概念 | 把当前目录当有状态的教学工作区，跨会话产出自包含 HTML 课与参照文档 |

### 维护 agent 自身

| skill | 触发 | 什么时候用 | 它做什么 |
|---|---|---|---|
| `writing-for-agents` | 模型可触发 | 要写或改 skill、`AGENTS.md`、`CLAUDE.md` | 写给 agent 读的文档的参照：上下文指针、两种负担、信息层级、完成判据、引导词、修剪 |
| `test-skill` | 模型可触发 | 想知道某个 skill 实际执行成什么样 | 在隔离沙箱中发起 headless 盲测，产出逐步骤溯源的中文复盘报告 |
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
  mcp/
    ssh-mcp.json
  skills/
    development/<skill-id>/
      SKILL.md
      references/
      scripts/
    support/<skill-id>/
  commands/
  hooks/
```

- `.claude-plugin/`：Claude Code 插件与市场清单。
- `.codex-plugin/`：Codex 插件清单。
- `.agents/plugins/`：Codex 仓库级 marketplace 清单。
- `mcp/ssh-mcp.json`：保留的 SSH MCP 手动配置，不随两平台插件自动加载。
- `skills/`：两平台共用的完整 Skill，成员与职责见上面的「Skill 一览」。
- `commands/`：存放自定义 command。
- `hooks/`：存放 hook 定义或说明。

## 新增 Skill

1. 建目录 `skills/development|support/<skill-id>/`，主体文件 `SKILL.md`，
   辅助资料放 `references/`，脚本放 `scripts/`，Codex 侧的界面描述放 `agents/openai.yaml`。
   资源目录内不再单独写 `README.md` 或 `metadata.yaml`，说明以主体文件为唯一来源。
2. `SKILL.md` 的 frontmatter 写清 `name`（与目录名一致）和 `description`
   （决定模型认不认得出该用它）；只给人用的入口加 `disable-model-invocation: true`。
   若它会被别的 skill 调用，正文还要写明调用契约（传入 / 取回 / 不做什么）。
3. `description` 统一用「动词描述能力」模版（Action + Object）：
   动词开头、紧跟宾语、一句话说清做什么、句号收尾，
   不用介词或时间状语开场（对 / 把 / 用 / 在…时 / 从 / 通过），也不加分类标签前缀。
   `agents/openai.yaml` 的 `short_description` 同样遵守这条模版。
4. 随插件发布时：
   - 更新 `.claude-plugin/plugin.json` 的 `skills` 数组（路径含目录名，
     如 `./skills/development/tdd`）；
   - 确认 `.codex-plugin/plugin.json` 的 `skills` 指向根目录 `skills/`
     （它按目录扫描，新增 skill 无需改这一项）；
   - 同步递增 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`
     与 `.codex-plugin/plugin.json` 的版本。
5. 在本文件的「Skill 一览」里补一行：什么时候用、它做什么。

## 当前非目标

- 不自动改写用户机器上的 Claude Code / Codex 已安装副本。
- 不做 CLI。
- 不做 schema 校验。
- 不做自动打包、发布或安装流程。
- 不做跨平台格式转换。
