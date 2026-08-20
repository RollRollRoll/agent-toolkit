# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、
`command` 和 `hook`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
Claude Code 通过 `.claude-plugin/` 发布，Codex 通过 `.codex-plugin/` 和
`.agents/plugins/` 发布；两平台直接加载根目录 `skills/` 下的同一套 Skill，
不随插件自动加载 SSH MCP。

SSH MCP 配置仍保留在 `mcp/ssh-mcp.json`，仅供手动配置时使用。该文件不在
Claude Code 和 Codex 的插件默认发现位置，也未被插件清单引用。

## 架构：一条开发链 + 一批能力单元

Skill 分两类，职责与调用方向固定：

- **开发链的四棒编排器**：`idea → plan → task → execute`。
  每一棒**只做编排、闸门与用户确认**，把具体能力交给被调 skill，**自己不定义能力判据**。
  产物交给下一棒，过门后不自动往下。
- **可复用能力单元**：单一职责、可被任何调用方复用。
  每个都在 `SKILL.md` 里声明**调用契约**（传入 / 取回 / 不做什么），判据住在自己这里，不被调用方复制。
  它们**只产内容、不判定放行**——review 门禁归调用它的那一棒。
- **链外独立工具**：不参与这条链的工具型 skill（代码库调研、一手来源调研、Skill 盲测、配置同步等），标为 `standalone`。

```text
开发链      idea  →  plan  →  task  →  execute
              │        │        │         │
              │        │        │         └─ setup-worktree · tdd · review-changes · finish-branch
              │        │        └─ split-task
              │        └─ write-spec · make-design
能力单元      └─ refine-idea ─→ grilling ←─ grill-me（standalone，人类专用入口）
```

各棒的调用点：

| 编排器 | 调用点 | 被调 skill | 传入 | 取回 |
|---|---|---|---|---|
| `idea` | 阶段 1 打磨概念 | `refine-idea` | 原始想法、已知约束、是否落盘 | 六行概念复述、被剪分支、挂起项 |
| `plan` | 阶段 1 写行为规格 | `write-spec` | 需求依据、落盘位置、调研决策、范围提示 | spec 路径、自检结论、待解问题 |
| `plan` | 阶段 3 定技术方案 | `make-design` | 已确认的 spec、约束与偏好 | design 路径、需拍板的点、推断假设 |
| `task` | 阶段 1 拆任务 | `split-task` | 已确认的 design、spec、切片偏好 | tasks 路径、需拍板的点、推断假设 |
| `execute` | 阶段 1 需要隔离 / 并行 | `setup-worktree` | expected base、用途 | worktree 路径 + 已验证 HEAD |
| `execute` | 阶段 2 每个任务 | `tdd` | 简报、约定的 seam、验证方式、记录路径 | 证据齐否、改动文件、疑虑 |
| `execute` | 阶段 3 整体验收 | `review-changes` | BASE、design/spec/tasks、疑虑 | 分级 findings + 六关判定 |
| `execute` | 阶段 4 收尾 | `finish-branch` | 最终验证命令、本次开发范围、调用来源 | 收尾决策与已执行动作 |

`refine-idea` 自己还有一个调用点：阶段 2 调 `grilling` 照亮概念层边界（传"只展开概念层"，
技术分支剪出去）。`grilling` 同时是 standalone 入口 `grill-me` 的实现：同一套访谈机制，
`grill-me` 传"不剪枝"（技术分支也问）。

调用约定：

- **调用即交出判据定义权**：调用方不重述被调 skill 的规则，需要细节就去读那个 skill。
- **门禁归编排器**：被调 skill 产出内容并交回，"过没过、要不要往下"由调用它的那一棒判定；
  它们对缺前置的处理是回 **BLOCKED**，不是自己补上游的活。
- **调用不等于派 subagent**：默认在调用方自己的上下文里加载执行；需要 fresh 上下文时
  （如 `review-changes` 的独立性要求）由调用方显式派发并定档。
- **被调 skill 不可用时闸门判据不变**：由调用方按同一套判据自己走一遍并说明降级原因——
  降级的是谁来做，不是做不做。
- **产物落盘目录由调用方决定**：被调 skill 的脚本都接受可选输出目录，缺省落在自己的自忽略点目录
  （`.tdd/`、`.review-changes/`）；被 `execute` 调用时统一落进 `.execute/`。
- 这套结构没有单独的声明文件：开发链就是 `skills/workflow/` 下那四个，
  一个 skill 能不能被别的 skill 调用，由 `SKILL.md` 里的「调用契约」章节体现。

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
    workflow/<skill-id>/
      SKILL.md
      references/
      scripts/
    development/<skill-id>/
    support/<skill-id>/
  commands/
  hooks/
  collections/
```

## 目录职责

- `.claude-plugin/`：Claude Code 插件与市场清单。
- `.codex-plugin/`：Codex 插件清单。
- `.agents/plugins/`：Codex 仓库级 marketplace 清单。
- `mcp/ssh-mcp.json`：保留的 SSH MCP 手动配置，不随两平台插件自动加载。
- `skills/`：两平台共用的完整 Skill，**按使用场景**分 `workflow/`、`development/`、`support/`
  三个目录，各自的分类判据、成员清单与边界见
  [`skills/workflow/README.md`](skills/workflow/README.md)、
  [`skills/development/README.md`](skills/development/README.md)、
  [`skills/support/README.md`](skills/support/README.md)。
- `commands/`：存放自定义 command。
- `hooks/`：存放 hook 定义或说明。
- `collections/`：手动记录资源组合关系。

## 新增资源

1. 在对应的根目录 `<type>/<resource-id>/` 下创建资源目录。
   Skill 要先定场景，放进 `skills/workflow|development|support/<skill-id>/`——
   **换分类就是移动目录**，没有别处需要同步。
2. 添加资源主体文件；Skill 的主体文件是 `SKILL.md`，辅助资料放 `references/`，
   脚本放 `scripts/`，Codex 侧的界面描述放 `agents/openai.yaml`。
   资源目录内不再单独写 `README.md` 或 `metadata.yaml`，说明以主体文件为唯一来源。
3. `SKILL.md` 的 frontmatter 写清 `name`（与目录名一致）和 `description`
   （决定模型认不认得出该用它）。若它会被别的 skill 调用，
   正文还要写明调用契约（传入 / 取回 / 不做什么）。
   `description` 统一用「动词描述能力」模版（Action + Object）：
   动词开头、紧跟宾语、一句话说清做什么、句号收尾，
   不用介词或时间状语开场（对 / 把 / 用 / 在…时 / 从 / 通过），
   也不加「开发链第 X 棒」一类标签前缀。
   `agents/openai.yaml` 的 `short_description` 同样遵守这条模版。
4. 如果资源属于某个组合，更新对应的 `collections/*.yaml`。
5. 如果 Skill 要随插件发布：
   - 更新 `.claude-plugin/plugin.json` 的 `skills` 数组（路径含场景目录，
     如 `./skills/development/tdd`）；
   - 确认 `.codex-plugin/plugin.json` 的 `skills` 指向根目录 `skills/`
     （它按目录扫描，新增 skill 无需改这一项）；
   - 同步递增 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`
     与 `.codex-plugin/plugin.json` 的版本。

## 当前非目标

- 不自动改写用户机器上的 Claude Code / Codex 已安装副本。
- 不做 CLI。
- 不做 schema 校验。
- 不做自动打包、发布或安装流程。
- 不做跨平台格式转换。
