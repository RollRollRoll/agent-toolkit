# Git Commit & Push

## 用途

在提交并推送代码前审查候选改动，将不同实现逻辑拆成可运行、可审查、可回滚的原子提交，生成清晰的
提交信息，并在用户确认分支、提交批次和远端后执行 commit 与 push。

## 触发场景

- “提交代码并 push”
- “把这些改动分批 commit 后推送”
- “检查一下改动，整理好提交到远端”
- 不适用：实现或测试尚未完成、需要解决冲突、合并 / rebase、改写历史或创建 PR。

## 安全边界

- 敏感信息与无用生成物不得进入提交，并提示用户加入 `.gitignore`。
- 一个提交只包含一个完整逻辑变更；复杂提交使用正文说明原因、决策和影响。
- 提交前确认当前分支，检查换行符、文件权限和完整 staged diff。
- 冲突与 non-fast-forward 只报告，不替用户 merge、rebase、pull 或强推。
- 多个 remote 时让用户选择 push / pull 目标；不默认操作全部远端。
- 已推送提交用新的修正提交处理，不随意改写历史。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/git-commit-push/`；
Codex：`.agents/skills/git-commit-push/`）即可使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `agents/openai.yaml`：Codex 的展示名称、简短描述和默认提示词。
