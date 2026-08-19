# skills/development/

## 这个目录装什么

**服务于软件开发本身的能力**：产出的东西最终会变成代码、代码的依据（概念 / 规格 / 设计 / 任务），
或者对代码的判断（审查、调研），落点是**仓库**。

判断标准：

1. **对象是代码或代码的依据**——不是 agent 自己的工程，也不是"帮人想清楚一件与代码无关的事"。
2. **单一职责、可被复用**：不绑定某一条链上的某一棒，谁需要谁调。
3. 大多数还满足：**在 `SKILL.md` 里声明了「调用契约」**（传入 / 取回 / 不做什么），
   判据住在自己这里，不被调用方复制；只产内容、不判定放行，缺前置就回 `BLOCKED`。

第 3 条不是硬门槛——不参与开发链、也不被别人调的工具型 skill（如 `codebase-analyzer`）
同样属于这里，标为 `standalone`，因为它的对象仍然是代码。

## 当前成员

按开发链上被调用的先后排：

| skill | 被谁调 | 职责 |
|---|---|---|
| `refine-idea` | `idea` 阶段 1 | 通过协作对话把没想透的想法打磨成边界清晰的概念 |
| `write-spec` | `plan` 阶段 1 | 把已清晰的需求写成可验证的行为规格（Requirement + MUST + WHEN→THEN） |
| `make-design` | `plan` 阶段 3 | 把行为规格转化成可追溯的技术设计，重大决策附候选方案与 trade-off |
| `split-task` | `task` 阶段 1 | 把技术设计拆成可独立验收、带依赖与验证方式的任务清单 |
| `setup-worktree` | `execute` 阶段 1 | 基于确定基线建立并验证隔离的 git worktree |
| `tdd` | `execute` 阶段 2 | 用红绿循环落地一段行为改动，并把命令与输出落盘 |
| `review-changes` | `execute` 阶段 3 | 对已写完的改动做独立审查，输出带 `file:line` 的分级 findings |
| `finish-branch` | `execute` 阶段 4 | 收尾：清理调试代码、跑最终测试，再由用户拍板合并 / 保留 / 开 PR / 丢弃 |
| `git-commit-push` | 用户直呼 | 解冲突，或把已完成的改动拆成原子提交并在确认后推送 |
| `codebase-analyzer` | 用户直呼（standalone） | 对陌生项目做全面调研，产出说明它做什么、怎么实现的报告 |

`refine-idea` 自己也是调用方：阶段 2 调 `../support/grilling`，传"只展开概念层"。

## 和 `../workflow/`、`../support/` 的边界

- **vs `workflow/`**：那边是链上的一棒，只编排、不定判据；这边定判据、不判放行。
  一个 skill 如果既写判据又能被别人调，它就在这里。
- **vs `support/`**：分界在**对象**，不在难度。改代码、审代码、写代码的依据 → 这里；
  对象是人（访谈、追问、问卷）或 agent 自身工程（配置、skill 测试）→ `support/`。
  典型对照：`review-changes` 审的是代码，在这里；`test-skill` 测的是 skill，在那边。

## 新增时

放进 `skills/development/<skill-id>/`，主体文件 `SKILL.md`，辅助资料放 `references/`，
脚本放 `scripts/`，Codex 侧界面描述放 `agents/openai.yaml`。会被别的 skill 调用的，
正文必须写明调用契约。**换分类就是移动目录**，没有别处需要同步分类信息
（发布路径除外：`.claude-plugin/plugin.json` 的 `skills` 数组含场景目录）。
