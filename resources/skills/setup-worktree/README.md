# Setup Worktree

## 用途

在开始一段开发、或并行多个任务前，建立隔离的 git 工作区（worktree）：先确认工作区干净并锁定
expected base，再选择能保证该基线的创建方式，最后验证新工作树的 `HEAD`。若平台原生工具的基线
语义不明确，则使用显式指定 commit 的 `git worktree add`，避免任务从错误版本开工。

Claude Code 的 `worktree.baseRef` 默认 `fresh`（从 `origin` 默认分支创建），`head` 才从本地
`HEAD` 创建；不能把存在 `EnterWorktree` 等同于基线正确，也不能为此擅自修改用户设置。

Codex App 的托管 Worktree 从用户选定分支的 `HEAD` 创建，默认是 detached HEAD，并可通过
Handoff 在 Local 与 Worktree 间移动任务；Codex CLI / IDE 不复用这套 UI 语义，需要时显式执行
`git worktree add`。无论平台都以创建后的真实 `HEAD == expected base` 为最终判据。

agent-toolkit 的执行阶段支撑 skill，通常由 execute-task 调用，也可单独复用。只管"建立隔离"，
清理与收尾交 finish-branch。

## 触发场景

- "开个 worktree / 隔离一下工作区 / 并行任务各自隔离"
- execute-task 执行前需要隔离工作区。
- 不适用：小改动不需隔离；收尾 / 合并 / 清理（那是 finish-branch）；非 git 仓库。

## 安全边界

- 有未提交或未跟踪改动时停止，不自动 stash、提交或丢弃。
- execute-task 未另行指定时，以调用处的本地 `HEAD` 作为 expected base。
- 创建后必须验证 `HEAD == expected base`；不匹配就停止。
- 工作树移除由 finish-branch 处理，并在执行前取得用户明确确认。

## 使用方式

将本目录下的 `SKILL.md` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/setup-worktree/`；Codex：`.agents/skills/setup-worktree/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
