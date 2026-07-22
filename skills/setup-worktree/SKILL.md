---
name: setup-worktree
description: 当要在开始一段开发、或并行多个任务前，建立隔离的 git 工作区（worktree）以免污染当前工作区时使用——如"开个 worktree、隔离工作区、并行任务各自隔离"。通常由 execute-task 在执行前调用。先锁定 expected base，再选择能保证该基线的创建方式，并在创建后验证 HEAD。不要用于：不需要隔离的小改动、收尾/合并/清理（那是 finish-branch）、非 git 仓库。
---

# Setup Worktree — 工作区隔离 Skill

## 你的任务

在开始一段开发、或并行多个任务前，**建立一个隔离的 git 工作区（worktree）**，让这段工作在
独立目录、隔离 checkout（需要时再建立独立分支）上进行，不污染当前工作区、也便于多条开发线并行。

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

## 核心流程（检测 → 锁定基线 → 创建 → 验证）

1. **检测当前状态**：
   - 是否在 git 仓库？否 → 告知不适用，停。
   - **是否已在一个合适的隔离环境里？** 是 → 不重复建；仍需核对当前 `HEAD` 是否就是调用方要求的基线。
   - 当前有无未提交改动（含未跟踪文件）？有 → **停止创建并让用户先处理**。不得自动 stash、提交、丢弃，也不得假设新 worktree 会携带这些改动。
2. **锁定 expected base**：
   - 调用方明确给出基线时，以调用方给出的 commit 为准。
   - 未给出时，用 `git rev-parse HEAD` 记录当前本地 `HEAD` 的完整 commit ID；execute-task 默认使用这个本地 `HEAD`，不要自行改成远端默认分支。
   - 并行任务必须各自记录 expected base；同一批任务若要求同源，所有 worktree 使用同一个 commit ID。
3. **按平台选择能保证 expected base 的创建方式**：
   - 只有在平台原生工具**能保证从 expected base 创建**时才使用它；无法确认语义时，统一退回显式命令：`git worktree add -b <分支名> <路径> <expected-base>`。
   - **Claude Code**：保留 `worktree.baseRef` 语义。默认值 `fresh` 从 `origin` 默认分支创建，`head` 才从本地 `HEAD` 创建；该设置同时影响 `--worktree`、`EnterWorktree` 和 subagent isolation。expected base 是本地 `HEAD` 时，不能把默认 `fresh` 当成等价语义，也不得擅自修改用户设置。
   - **Codex App**：托管 Worktree 从新任务里选定分支的 `HEAD` 创建，默认处于 detached HEAD；创建前让用户在 composer 选择 `Worktree` 与起始分支，或在已有任务中使用 Handoff。只有选定分支的 `HEAD` 等于 expected base 时才使用该路径；创建后再用真实 commit ID 核验，不因 UI 显示的分支名跳过验证。需要长期分支时，验证后再使用 “Create branch here”，不要把默认 detached HEAD 误报成独立分支。
   - **Codex CLI / IDE**：不假设存在 Codex App 的托管 Worktree/Handoff；需要隔离时使用显式 `git worktree add`。Codex App 的 `.worktreeinclude` 只用于复制 Git 已忽略且确实需要的本地文件，不得借它搬运普通未提交改动，也不得未经用户同意加入凭据文件。
   - 记下 **平台、worktree 路径、HEAD 状态（detached 或分支名）与 expected base**，供后续验证和 finish-branch 清理。
4. **创建后验证，未通过不得开工**：
   - 在新 worktree 中执行 `git rev-parse HEAD`，结果必须与 expected base 的 commit ID 完全一致。
   - 确认新 worktree 状态干净，原工作区没有被改动；Codex App 托管 Worktree 还要记录是否为 detached HEAD。
   - 若 HEAD 不匹配：**停止，不做代码修改，也不要用 rebase / reset 静默修正**；报告实际值与期望值，由用户决定后续处理。

> 检验：新 worktree 是否处于独立目录，`HEAD == expected base`，HEAD 状态已明确，新旧工作区都保持干净？全部满足才算隔离成立。

## 注意事项

- **检测优先**：已在 worktree 就别再嵌套建——先查，再决定建不建。
- **基线语义优先**：平台原生与手工命令只是实现手段；是否准确落在 expected base 才是选择依据。
- **平台分支不混用**：Claude Code 的 `EnterWorktree/worktree.baseRef`、Codex App 的 Worktree/Handoff、Codex CLI 的显式 Git 命令分别处理，不用一个平台的参数解释另一个平台。
- **命名可追溯**：分支 / worktree 路径用关联任务 / 功能的名字，便于后续辨认与清理。
- **不搬运脏改动**：不自动 stash、提交或复制当前工作区的未提交改动。
- **不在这里清理**：worktree 用完的移除 / 合并交 **finish-branch** 或调用方；移除工作树前必须取得用户明确确认。

## 反例（不要这样做）

❌ 不检测就建 —— 在已有 worktree 里又套一个 worktree。
❌ 看到 `EnterWorktree` 就直接调用，却没有确认它会从哪个 commit 创建。
❌ 在 Codex App 中只看起始分支名称，不核对托管 Worktree 的真实 `HEAD`。
❌ 把 Codex App 默认 detached HEAD 描述成已经创建了独立分支。
❌ 当前工作区有未提交改动时自动 stash / 提交，然后继续创建。
❌ 创建后不核对 `HEAD`，让任务在错误基线上开工。
❌ 在这里做合并 / 删除 worktree / 清理 —— 越界到 finish-branch。
❌ 在非 git 仓库里硬建 worktree。
❌ 给小改动也强行开 worktree —— 不需要隔离就别隔离（YAGNI）。

## 相关

- 通常由 **execute-task**（阶段 1 调度规划）在需要隔离 / 并行时调用。
- 收尾、合并、清理 worktree 见 **finish-branch**。
