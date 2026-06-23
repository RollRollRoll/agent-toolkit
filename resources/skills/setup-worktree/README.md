# Setup Worktree

## 用途

在开始一段开发、或并行多个任务前，建立隔离的 git 工作区（worktree）：先检测是否已在 worktree，
再优先平台原生 worktree 工具，最后 fallback `git worktree`，让工作在独立目录 + 独立分支上进行，
不污染当前工作区。

agent-toolkit 的执行阶段支撑 skill，通常由 execute-task 调用，也可单独复用。只管"建立隔离"，
清理与收尾交 finish-branch。

## 触发场景

- "开个 worktree / 隔离一下工作区 / 并行任务各自隔离"
- execute-task 执行前需要隔离工作区。
- 不适用：小改动不需隔离；收尾 / 合并 / 清理（那是 finish-branch）；非 git 仓库。

## 使用方式

将本目录下的 `SKILL.md` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/setup-worktree/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
