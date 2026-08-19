# agent-toolkit

个人 agent 工具资源仓库，用于管理自己创建的 `skill`、`mcp`、
`command` 和 `hook`。

以个人知识库为主，重点是让资源清晰、独立、可维护。
Claude Code 通过 `.claude-plugin/` 发布，Codex 通过 `.codex-plugin/` 和
`.agents/plugins/` 发布；两平台直接加载根目录 `skills/` 下的同一套 Skill，
不随插件自动加载 SSH MCP。

SSH MCP 配置仍保留在 `mcp/ssh-mcp.json`，仅供手动配置时使用。该文件不在
Claude Code 和 Codex 的插件默认发现位置，也未被插件清单引用。

## 架构：workflow 层 + composable 层

Skill 分两层，职责与调用方向固定：

- **workflow 层（Layered Workflow Orchestration）**：`idea → plan → task → execute` 这条开发链。
  每一棒**只做编排、闸门与用户确认**，把具体能力交给 composable 层，**自己不定义能力判据**。
  产物交给下一棒，过门后不自动往下。
- **composable 层（Composable Skills Architecture）**：单一职责、可被任何调用方复用的能力单元。
  每个都在 `SKILL.md` 里声明**调用契约**（传入 / 取回 / 不做什么），判据住在自己这里，不被调用方复制。
  它们**只产内容、不判定放行**——review 门禁归 workflow 层。
- **层外独立工具**：不参与这条链的工具型 skill（代码库调研、Skill 盲测、配置同步等），标为 `standalone`。

```text
workflow    idea  →  plan  →  task  →  execute
              │        │        │         │
              │        │        │         └─ setup-worktree · tdd · review-changes · finish-branch
              │        │        └─ split-task
              │        └─ write-spec · make-design
composable    └─ refine-idea ─→ grilling ←─ grill-me（standalone，人类专用入口）
```

各棒的调用点：

| workflow | 调用点 | composable skill | 传入 | 取回 |
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

跨层约定：

- **调用即交出判据定义权**：调用方不重述被调 skill 的规则，需要细节就去读那个 skill。
- **门禁归 workflow 层**：composable skill 产出内容并交回，"过没过、要不要往下"由 workflow 层判定；
  它们对缺前置的处理是回 **BLOCKED**，不是自己补上游的活。
- **调用不等于派 subagent**：默认在调用方自己的上下文里加载执行；需要 fresh 上下文时
  （如 `review-changes` 的独立性要求）由调用方显式派发并定档。
- **被调 skill 不可用时闸门判据不变**：由调用方按同一套判据自己走一遍并说明降级原因——
  降级的是谁来做，不是做不做。
- **产物落盘目录由调用方决定**：composable skill 的脚本都接受可选输出目录，缺省落在自己的自忽略点目录
  （`.tdd/`、`.review-changes/`）；被 `execute` 调用时统一落进 `.execute/`。
- 架构层次不在 `metadata.yaml` 里标注：workflow 层就是 `skills/workflow/` 下那四个，
  composable 能力单元由 `SKILL.md` 里的「调用契约」章节体现。

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
- `skills/`：两平台共用的完整 Skill，**按使用场景**分三个目录——`workflow/`（开发链四棒）、
  `development/`（服务软件开发的能力：概念、规格、设计、拆任务、TDD、审查、工作区与提交、
  代码库调研）、`support/`（面向人的访谈与调研、agent 自身工程与通用小工具）；辅助资料、
  脚本和测试均放在对应 Skill 目录内。目录归属与 `metadata.yaml` 的 `category` 字段一一对应。

  > 目录分的是**场景**，架构分层是另一个正交维度：workflow 层就是 `workflow/` 那四个；
  > 其余 skill 是不是 composable 能力单元，看它的 `SKILL.md` 里有没有「调用契约」章节。
- `commands/`：存放自定义 command。
- `hooks/`：存放 hook 定义或说明。
- `collections/`：手动记录资源组合关系。

## 新增资源

1. 在对应的根目录 `<type>/<resource-id>/` 下创建资源目录。
   Skill 要先定场景，放进 `skills/workflow|development|support/<skill-id>/`。
2. 添加资源主体文件和 `metadata.yaml`；Skill 的主体文件是 `SKILL.md`，
   辅助资料放 `references/`，脚本放 `scripts/`。资源目录内不再单独写 `README.md`，
   说明以主体文件为唯一来源。
3. Skill 的 `metadata.yaml` 用 `category: workflow | development | support` 标注场景，
   **必须与它所在的目录一致**——换分类等于换目录，两处一起改。
   若它是 composable 能力单元（会被别的 skill 调用），还要在 `SKILL.md` 里写明调用契约
   （传入 / 取回 / 不做什么）。
4. 如果资源属于某个组合，更新对应的 `collections/*.yaml`。
5. 手动维护 `metadata.yaml` 的 `updated_at`。
6. 如果 Skill 要随插件发布：
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
