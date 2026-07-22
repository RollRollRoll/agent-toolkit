# execute-task 吸收 subagent-driven-development 三脚本机制设计文档

日期：2026-07-08

## 背景

对照上游 obra/superpowers `subagent-driven-development` 的 `scripts/`（`sdd-workspace` / `task-brief` /
`review-package`，本地插件缓存 6.1.1 与 GitHub main 一致）做差距分析，发现三个缺口：

- **简报靠手抄**：`handoff-templates.md` 第〇节让主 agent 从 tasks.md 手工摘出任务全文，而简报被定义为
  "需求的唯一来源、精确值逐字照用"——手抄恰恰在最要害处引入失真风险（上下文压缩后凭记忆抄、
  转述改写、漏条目）。靠纪律约束 LLM 的环节最易劣化，脚本化把「逐字」从纪律变成机械保证
  （与 2026-07-07 review-diff 脚本化的动机一脉相承）。
- **diff 上下文不足**：`review-diff.sh` 用 `git diff` 默认 `-U3`，而 review 派发模板的纪律是
  "diff 的上下文行就是改动后的文件，别再单独读改动文件、别爬代码库"——3 行上下文立不住这条纪律，
  review subagent 要么违纪爬库、要么盲审。上游用 `-U10`。
- **阶段 3 无输入准备**：`acceptance.md` 整体五轴 review 没有任何 diff 交接机制（全文无 "diff"），
  review subagent 只能自己爬库推导"本次改了什么"；此时任务已全部 commit、工作区干净，
  `review-diff.sh`（只做工作区 diff）完全失效。上游对 whole-branch 终审同样走
  `review-package MERGE_BASE HEAD` 的包机制。

2026-07-07 设计文档否决 BASE..HEAD 只针对**任务级** review（执行 subagent 不 commit，工作区 diff 即改动），
阶段 3 场景当时未讨论，本次补上，不构成翻案。

## 决策（经用户拍板）

1. **脚本形态 A（上游同构）**：`workspace.sh` 作为 `.execute-task/` 目录逻辑的单一事实来源，
   其余三个脚本经 `dirname "$0"` 调用它——与上游实战验证过的形态一致，防三处目录约定漂移。
2. **验证策略**：本次仅做脚本级验证（临时 git 仓库）；test-skill 全编排复测**延后**为独立后续任务
   （已知风险见「延后项」）。

### 脚本层（scripts/ 最终 4 个文件）

- **`workspace.sh`**（新增，≈上游 sdd-workspace）：无参数；建 `<repo-root>/.execute-task/` +
  写只含 `*` 的自忽略 `.gitignore`，打印目录绝对路径。幂等。
- **`task-brief.sh`**（新增，≈上游 task-brief + 两处适配）：
  - 接口 `task-brief.sh <tasks文件> <任务编号>`，输出 `.execute-task/task-N-brief.md`，路径打印到 stdout。
  - awk 抽取 `### Task N:` 标题段（split-task 模板格式天然匹配上游正则），沿用 code-fence 保护
    与 Task 1 / Task 10 区分。
  - 适配 1（尾部截断）：遇到**非 Task 的一、二级标题**（`^# ` / `^## `，如「依赖与并行视图」）也终止抽取——
    上游只在下一个 Task 标题终止，照抄会让最后一个任务把文档尾部全带上（任务标题固定为三级 `### Task N:`）。
  - 适配 2（空结果报错）：任务号不存在时报错并以非零退出，防主 agent 拿空简报派发。
- **`review-diff.sh`**（改造，接口不变）：`git diff` 加 `-U10`；内嵌目录逻辑改调 `workspace.sh`；
  轮次命名、空 diff 警告、单参数接口保持。
- **`acceptance-diff.sh`**（新增，≈上游 review-package 的 BASE..HEAD 形态）：
  - 接口 `acceptance-diff.sh <BASE>`，HEAD 固定当前；输出 `.execute-task/acceptance-R<N>.diff`
    （轮次递增，沿用 review-diff 惯例），路径打印到 stdout。
  - 内容三段：`git log --oneline BASE..HEAD` + `git diff --stat BASE..HEAD` + `git diff -U10 BASE..HEAD`。
  - BASE 校验失败即报错退出。

### 机制层（3 处流程变更）

- **简报生成 = 脚本基底 + 判断力追加**：主 agent 先跑 `task-brief.sh` 得任务全文基底（精确值机械保真），
  再用编辑工具往**同一文件**追加相关 design/spec 片段（这半截需要判断力，脚本管不了）。
- **ledger 记起点 commit**：`orchestration.md` 第五节账本增加一项——阶段 1 开工时记录起点 commit
  （`git rev-parse HEAD`）。它是阶段 3 BASE 的可靠来源：execute-task 不一定开分支
  （worktree 可选、也可能直接在 main 上跑），动态 `git merge-base` 不普适；ledger 是既有机制，
  加一行成本最低且所有场景成立。
- **阶段 3 输入准备 + fix 循环**：
  - 派五轴 review 前：跑 `acceptance-diff.sh <ledger起点>` 生成整体包，派发传包路径。
  - 阶段 3 fix 采用 **commit-then-review**：fix 完由主 agent 先 commit，再重跑 `acceptance-diff.sh`
    （R 递增，HEAD 已前进故新包已含 fix），复审读一个新包。与任务级 review-then-commit **有意不同**：
    任务级"不过不 commit"是因为 commit 是闸门记号；阶段 3 面对的对象本来就是已 commit 的分支，
    闸门记号是"整体验收通过"状态本身，fix commit 只是普通代码演进。一个文件闭环，
    不搞"旧包 + 工作区 diff"双文件复审。

## 改动文件

- 新增：`scripts/workspace.sh`、`scripts/task-brief.sh`、`scripts/acceptance-diff.sh`
- 修改：`scripts/review-diff.sh`（-U10 + 调 workspace.sh）
- `references/handoff-templates.md`：第〇节简报步骤改脚本化（跑脚本 + 追加片段）；
  新增第四节「整体验收 review 派发模板」——包路径 + 引用 acceptance.md 五轴（不复制定义，防两处维护）+
  只读纪律 + 回执格式，并注明阶段 3 fix 派发复用任务级 fix 模板、简报位换成 design/spec 路径；
  原第四节自查顺延为第五节，自查项补"简报用脚本生成的？阶段 3 传包了？"
- `references/orchestration.md`：第四节简报生成措辞改脚本化；第五节 ledger 增加起点 commit 记录
- `references/acceptance.md`：第二节增加输入准备（跑脚本、传包路径）与 fix-commit-复审循环
- `README.md`：目录说明补三个新脚本；chmod 提示改 `chmod +x scripts/*.sh`
- `SKILL.md`：经核对无脚本单点引用，机制概览（"三份交接文件传路径"、闸门二）措辞与新机制兼容，**无需改动**
- `metadata.yaml`：`updated_at` 同步为本次维护日期

## 验证（脚本级，临时 git 仓库逐项验预期输出）

- `task-brief.sh`：抽中间任务正确；抽**最后一个任务**不带 `## 依赖与并行视图` 尾巴；
  code fence 内的假 `### Task` 标题不误触发；找 Task 1 不误匹配 Task 10；任务号不存在报错退出。
- `review-diff.sh`：`-U10` 生效（上下文行数可数）；轮次递增与空 diff 警告不回归。
- `acceptance-diff.sh`：三段内容齐全；BASE 非法报错；轮次递增。
- `workspace.sh`：目录 / `.gitignore` 幂等创建；四脚本落点目录一致。

## 发布

按项目发布惯例：内容修改 + skill 内新增脚本文件（同 825b826 先例，不新增 skill 资源目录），
`metadata.yaml` 的 `updated_at` 同步，validate 校验通过后直接 main 提交、push 本地 bare origin；
是否触发双清单版本递增，实现时按 f5d5f0c / 825b826 先例判断（825b826 未递增）。

## 延后项

- **test-skill 全编排复测**：作为独立后续任务另行安排。已知风险——momentum 类失败
  （主 agent 惯性手抄简报而不跑脚本）在本次发布时未经全编排验证，
  该类失败单发子代理测不出（见项目记忆 skill-test-momentum-failures）。
