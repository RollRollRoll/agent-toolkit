# 从 execute-task 拆出 setup-worktree / finish-branch 设计文档

日期：2026-06-22

## 背景与目标

execute-task（执行 skill）落地后，对照 superpowers 执行阶段，发现两块覆盖不全：

- **using-git-worktrees**：只部分覆盖——execute-task 把 worktree 当"并行子任务隔离的可选手段"，
  缺 superpowers 的「执行前建立隔离工作区」起手式 + 「检测是否已在 worktree → 平台原生工具 → fallback git worktree」降级链。
- **finishing-a-development-branch**：基本覆盖（合并/PR/留分支 + 清理 + gate），缺「丢弃」选项与「repo/worktree 状态检测」。

本次（用户拍板）：**补齐这两块 gap，并把它们从 execute-task 中拆成两个独立可复用 skill**，execute-task 改为引用。

## 关键决策（本次确认，均用户拍板）

1. **拆成独立 skill**：把 worktree、finishing 从 execute-task 内部拆出，成为工具集内的独立 skill；execute-task 引用它们。
   - 理由：这两块是通用执行纪律，独立后可被链外其他场景复用（呼应 superpowers 把它们作为独立 skill 的结构）。
2. **命名本项目风格**：`setup-worktree` + `finish-branch`（动宾、简洁，与 refine-idea / write-spec / make-design /
   split-task / execute-task 一致），不沿用 superpowers 的长名。
3. **自包含边界调和**：拆出的是 **agent-toolkit 工具集内部的 skill**（非外部 superpowers）。"自包含"的边界从
   "execute-task 单 skill 自包含"调整为"**整个工具集自包含、内部模块化**"——execute-task 引用工具集内的
   setup-worktree / finish-branch，如同 make-design 软依赖 codebase-analyzer。整体仍可独立分发、零外部插件依赖。
4. **轻量结构**：两个新 skill 是聚焦工具型小 skill，用轻量结构（你的任务 / 何时用 / 核心流程 / 注意事项与 gate /
   反例），**不套** 招牌机制⭐ + 阶段 0-4 + references（那是大流程 skill 的结构，套上去笨重；superpowers 这两个也是单 SKILL.md）。

## 链结构更新

主链仍是五工序：`refine-idea → write-spec → make-design → split-task → execute-task`。

**支撑 skill**（不在主链上，被主链 skill 调用 / 复用）：

- `codebase-analyzer` —— 调研支撑（make-design / split-task 软依赖）
- `setup-worktree` —— 隔离支撑（execute-task 阶段 1 调用）
- `finish-branch` —— 收尾支撑（execute-task 阶段 4 调用）

## 新 skill 一：setup-worktree

**定位**：执行阶段支撑 skill——建立隔离工作区，供执行 / 并行使用。

**核心流程**：

1. **检测**当前是否已在 worktree / 合适的隔离环境——已在则不重复建（避免嵌套）。
2. **优先平台原生 worktree 工具**（Claude Code 用 `EnterWorktree`；其他平台用其原生能力）。
3. **fallback `git worktree add`**——平台无原生能力时降级。

**两种用途**：

- 整次开发隔离（起手式，本次补的 gap）：开始一段开发前把它隔离到干净工作区，不污染当前工作区。
- 并行子任务各自隔离（execute-task 原有用途）：多个并行任务各一个 worktree 防冲突。

**注意事项**：检测优先（不嵌套重复建）；平台原生优先、git worktree 兜底；worktree 的清理交 finish-branch 或调用方。

**结构**：轻量（你的任务 / 何时用 / 核心流程 / 注意事项 / 反例），单 SKILL.md，无 references。

## 新 skill 二：finish-branch

**定位**：执行阶段支撑 skill——开发完成且测试通过后的收尾。

**核心流程**：

1. **验证测试全绿**——不绿不收尾（收尾前必须确认测试通过）。
2. **检测 repo / worktree 状态**——当前分支、是否在 worktree、有无未提交改动（本次补的 gap）。
3. **给出收尾选项**：合并到主干 / 本地保留 / 创建 PR / **丢弃**（丢弃是本次补的 gap）。
4. **清理**：worktree / 临时分支 / 遗留调试代码。

**危险操作 gate**：合并 / PR / push / 丢弃都是破坏性或对外操作，**必须用户明确确认，不自动做**（呼应 CLAUDE.md）。

**结构**：轻量（你的任务 / 何时用 / 核心流程 / 注意事项与 gate / 反例），单 SKILL.md，无 references。

## execute-task 改造（移内置细节、改引用）

- **阶段 1 调度规划**：「定并行与隔离」改为"需要隔离工作区时，调用 `setup-worktree`"。
- **阶段 2**：提到"可 worktree 隔离"处，指向 `setup-worktree`。
- **阶段 4 收尾**：改为"调用 `finish-branch` 做收尾"，移除内置的选项与清理细节。
- **产物与收尾节**：收尾逻辑指向 `finish-branch`。
- **核心原则 9（自包含）**：表述微调——不依赖**外部**插件；隔离 / 收尾**复用工具集内**的 setup-worktree / finish-branch。
- **references**：`orchestration.md` 三·worktree 隔离 → 精简为指向 setup-worktree；`acceptance.md` 五·收尾 → 精简为指向 finish-branch。
- **保留**：危险操作 gate 的原则、反例里"不自动合并/PR/push"仍保留（具体收尾流程移到 finish-branch）。

## 与 superpowers 的对应

| superpowers | agent-toolkit |
|---|---|
| using-git-worktrees | setup-worktree（自包含、命名本地化、补检测降级链） |
| finishing-a-development-branch | finish-branch（自包含、命名本地化、补丢弃 + 状态检测） |

差异：本项目自包含（不依赖外部插件）、命名遵循本项目动宾风格、由 execute-task 作为工具集内 skill 引用。

## 文件结构

```text
skills/setup-worktree/
  SKILL.md  README.md  metadata.yaml
skills/finish-branch/
  SKILL.md  README.md  metadata.yaml
```

execute-task 改造：`SKILL.md`、`references/orchestration.md`、`references/acceptance.md`。

## 发布

按 `docs/conventions.md` 新增资源流程：

- 新建 `setup-worktree/`、`finish-branch/` 下 SKILL.md / README.md / metadata.yaml。
- 两个 `metadata.yaml`：type=skill，status=draft，created_at/updated_at=2026-06-22。
- `.claude-plugin/plugin.json` 的 `skills` 数组加入 `./skills/setup-worktree`、`./skills/finish-branch`。
- **双清单版本同步**：`plugin.json` 与 `marketplace.json` 版本 `0.6.0` → `0.7.0`。
- 用 `claude plugin validate . --strict` 校验。
