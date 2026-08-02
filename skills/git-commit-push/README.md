# Git Commit & Push

## 用途

解决已经进行中的 merge / rebase / cherry-pick 冲突，或在提交并推送代码前审查候选改动。冲突处理会追溯
双方原始意图、逐 hunk 做语义合并并验证；普通提交会把不同实现逻辑拆成可运行、可审查、可回滚的原子提交。
所有 continue、commit 与 push 都在用户确认范围和影响后执行。

## 触发场景

- “提交代码并 push”
- “把这些改动分批 commit 后推送”
- “检查一下改动，整理好提交到远端”
- “解决当前 merge / rebase / cherry-pick 冲突并继续”
- 不适用：实现或测试尚未完成、要发起新的 merge / rebase、改写已发布历史或创建 PR。

## 安全边界

- 敏感信息与无用生成物不得进入提交，并提示用户加入 `.gitignore`。
- 一个提交只包含一个完整逻辑变更；复杂提交使用正文说明原因、决策和影响。
- 提交前确认当前分支，检查换行符、文件权限和完整 staged diff。
- 冲突解决以提交、PR、issue 和代码历史中的原始意图为依据；不靠整文件选择 ours / theirs 消除标记。
- 只处理已经开始的冲突操作；不自动发起、中止或跳过 merge / rebase / cherry-pick。
- 每批冲突在执行 continue 前展示解决摘要、取舍和验证结果并取得确认。
- non-fast-forward 和 rebase 后需要强推的情况只报告，不自动 pull 或强推。
- 多个 remote 时让用户选择 push / pull 目标；不默认操作全部远端。
- 已推送提交用新的修正提交处理，不随意改写历史。

## 使用方式

将本目录复制到目标平台的 skill 目录（Claude Code：`.claude/skills/git-commit-push/`；
Codex：`.agents/skills/git-commit-push/`）即可使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
- `references/conflict-resolution.md`：进行中 merge / rebase / cherry-pick 的语义冲突解决流程。
- `agents/openai.yaml`：Codex 的展示名称、简短描述和默认提示词。
- `LICENSE.upstream`：冲突解决流程参考来源的 MIT 许可证。

## 参考来源

冲突处理流程改编自 [mattpocock/skills 的 `resolving-merge-conflicts`](https://github.com/mattpocock/skills/tree/main/skills/engineering/resolving-merge-conflicts)，并按本仓库的授权与高风险操作边界整合到提交流程中。
