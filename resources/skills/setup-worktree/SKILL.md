---
name: setup-worktree
description: 当要在开始一段开发、或并行多个任务前，建立隔离的 git 工作区（worktree）以免污染当前工作区时使用——如"开个 worktree、隔离工作区、并行任务各自隔离"。通常由 execute-task 在执行前调用。先检测是否已在 worktree，再优先平台原生工具，最后 fallback git worktree。不要用于：不需要隔离的小改动、收尾/合并/清理（那是 finish-branch）、非 git 仓库。
---

# Setup Worktree — 工作区隔离 Skill

## 你的任务

在开始一段开发、或并行多个任务前，**建立一个隔离的 git 工作区（worktree）**，让这段工作在
独立目录、独立分支上进行，不污染当前工作区、也便于多条开发线并行。

这是 agent-toolkit 的**执行阶段支撑 skill**，通常由 execute-task 在执行前调用，也可被任何需要
隔离工作区的场景单独复用。它只负责"建立隔离"——**清理与收尾交 finish-branch**（职责分离）。

> 一句话：要动手改代码、又不想弄乱当前工作区时，先在这里开一个干净、隔离的 worktree。

## 何时用 / 何时不用

**适用**：

- 开始一段开发，想把它隔离到干净工作区（不与当前未提交改动混在一起）。
- execute-task 要并行执行多个任务，每个任务需要各自隔离、互不踩文件。
- 想同时维护多条开发线（多个 worktree）。

**不适用**：

- 改动很小、不需要隔离 —— 直接在当前工作区做即可，别为隔离而隔离。
- 要做的是收尾 / 合并 / 删除 worktree —— 那是 finish-branch。
- 不在 git 仓库里 —— worktree 是 git 能力，先确认是 git 仓库。

## 核心流程（检测 → 平台原生 → fallback）

1. **检测当前状态**：
   - **是否已在一个 worktree / 合适的隔离环境里？** 是 → **不重复建**，直接用（避免 worktree 套 worktree）。
   - 是否在 git 仓库？否 → 告知不适用，停。
   - 当前有无未提交改动？有 → 提示用户（新 worktree 不会带走未提交改动）。
2. **优先平台原生 worktree 工具**：
   - **Claude Code**：用 `EnterWorktree`（平台原生、自动管理路径与清理）。
   - 其他平台：用其原生 worktree 能力。
3. **fallback `git worktree`**：
   - 平台无原生能力 → `git worktree add <路径> -b <分支名>` 手动建。
   - 记下 **worktree 路径与分支名**，供后续工作与（finish-branch 的）清理。

> 检验：建完后，你是不是在一个独立目录 + 独立分支上、且当前工作区没被动过？是 → 隔离成立。

## 注意事项

- **检测优先**：已在 worktree 就别再嵌套建——先查，再决定建不建。
- **平台原生优先**：有原生工具就用它（自动管理更省心），`git worktree` 是兜底。
- **命名可追溯**：分支 / worktree 路径用关联任务 / 功能的名字，便于后续辨认与清理。
- **不在这里清理**：worktree 用完的清理 / 合并交 **finish-branch** 或调用方——本 skill 只管"建立"。

## 反例（不要这样做）

❌ 不检测就建 —— 在已有 worktree 里又套一个 worktree。
❌ 跳过平台原生工具，直接上 `git worktree` —— 放弃了平台的自动管理。
❌ 在这里做合并 / 删除 worktree / 清理 —— 越界到 finish-branch。
❌ 在非 git 仓库里硬建 worktree。
❌ 给小改动也强行开 worktree —— 不需要隔离就别隔离（YAGNI）。

## 相关

- 通常由 **execute-task**（阶段 1 调度规划）在需要隔离 / 并行时调用。
- 收尾、合并、清理 worktree 见 **finish-branch**。
