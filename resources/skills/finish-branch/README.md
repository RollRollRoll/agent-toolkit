# Finish Branch

## 用途

一段开发实现完成后，给当前分支 / worktree 收尾：先只读预检状态，再清理本次开发遗留的调试代码、跑最终测试，
然后给出合并 / 本地保留 / 创建 PR / 丢弃选项。提交、合并、推送、
删分支与移除工作树都必须由用户对具体动作明确授权。

agent-toolkit 的执行阶段支撑 skill，通常由 execute-task 执行完后调用，也可单独复用。只管"收尾决策 + 清理"，
建立工作区交 setup-worktree。

## 触发场景

- "收尾 / 把这个分支收掉 / 开发完了怎么处理 / 合并还是留着"
- execute-task 整体验收通过后的收尾。
- 不适用：开发没完 / 测试没过；建立工作区（那是 setup-worktree）。

## 安全边界

- 先做只读状态预检；入场已有未提交或未跟踪改动时停止，不自动清理、提交、stash 或丢弃。
- 调试残留清理后才运行最终测试；后续任何代码修改都要重跑。若清理发生在 execute-task 整体验收后，还要回阶段 3 重审。
- 合并、push、创建 PR、删除分支和移除 worktree 分别取得明确确认。
- 用户选择"本地保留"时只报告状态，不做隐含清理。

## 使用方式

将本目录下的 `SKILL.md` 复制到目标平台的 skill 目录
（Claude Code：`.claude/skills/finish-branch/`；Codex：`.agents/skills/finish-branch/`）即可直接使用。

## 目录说明

- `SKILL.md`：skill 主体（平台原生格式，含 frontmatter）。
