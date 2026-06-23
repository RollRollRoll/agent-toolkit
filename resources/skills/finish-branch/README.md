# Finish Branch

## 用途

一段开发完成且测试通过后，给当前分支 / worktree 收尾：先验证测试全绿，再检测 repo/worktree 状态，
然后给出合并 / 本地保留 / 创建 PR / 丢弃选项，破坏性与对外操作交用户拍板，最后清理 worktree / 临时分支。

agent-toolkit 的执行阶段支撑 skill，通常由 execute-task 执行完后调用，也可单独复用。只管"收尾决策 + 清理"，
建立工作区交 setup-worktree。

## 触发场景

- "收尾 / 把这个分支收掉 / 开发完了怎么处理 / 合并还是留着"
- execute-task 整体验收通过后的收尾。
- 不适用：开发没完 / 测试没过；建立工作区（那是 setup-worktree）。

## 使用方式

将本目录下的 `SKILL.md` 复制到目标平台的 skill 目录
（如 Claude Code 的 `.claude/skills/finish-branch/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
