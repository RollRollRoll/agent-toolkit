# execute-task 用脚本生成 review diff 设计文档

日期：2026-07-07

## 背景

对照另一份"处理实现者四态回执"的通用设计做比对时发现：execute-task 已有等价的四态处理逻辑
（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED，含 BLOCKED 升级阶梯），但生成待审 diff 的
步骤此前是主 agent 手写 `git diff > .execute-task/task-N-review-R1.diff`，轮次编号靠人工递增，
容易记错或复用旧文件。

对方设计里 `scripts/review-package BASE HEAD` 的思路（脚本生成、打印路径）值得借鉴，但其"BASE
commit 到 HEAD 的 diff、禁用 HEAD~1"这条前提不适用于 execute-task——execute-task 的执行 subagent
从不 commit，diff 始终是工作区未提交改动，不存在多 commit 被 `HEAD~1` 漏掉的风险。

## 决策

新增 `scripts/review-diff.sh`，只做一件事：给定任务编号，在 `.execute-task/` 下按轮次自动命名
（`task-N-review-R1.diff`、`R2`…，扫描已存在文件递增，不需人工记编号）、跑 `git diff` 写入、
把写入路径打印到 stdout；空 diff 时打印警告到 stderr（提示确认执行 subagent 是否真有改动）。
`.execute-task/.gitignore`（内容 `*`）由脚本首次运行时创建，延续原有的"自忽略、不提交"约定。

不引入 BASE/HEAD 参数或多 commit 支持——execute-task 当前"执行 subagent 不 commit"的模型没有变，
脚本只是把已有的手写步骤自动化，不改变机制本身。

## 改动文件

- 新增：`scripts/review-diff.sh`（已在临时 git 仓库验证：轮次递增、路径打印、空 diff 警告均正确）。
- `references/handoff-templates.md`：〇·派发前准备交接文件，步骤 4 改为调用脚本。
- `references/orchestration.md`：四·派发与 handoff，diff 文件生成改为调用脚本。
- `README.md`：目录说明 + 使用方式，补充 `scripts/` 的复制与可执行权限提示。

## 发布

内容修改，不新增 skill 资源，不强制触发 `.claude-plugin/plugin.json` 版本递增；`metadata.yaml`
的 `updated_at` 应同步为本次维护日期。
