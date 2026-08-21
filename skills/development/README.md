# skills/development/

## 这个目录装什么

**服务于软件开发本身的能力**：产出的东西最终会变成代码、代码的依据（概念 / 规格 / 设计 / 任务），
或者对代码的判断（审查、调研），落点是**仓库**。

判断标准：

1. **对象是代码或代码的依据**——不是 agent 自己的工程，也不是"帮人想清楚一件与代码无关的事"。
2. **单一职责、可被复用**：不绑定固定的编排顺序，谁需要谁调。
3. 大多数还满足：**在 `SKILL.md` 里声明了「调用契约」**（传入 / 取回 / 不做什么），
   判据住在自己这里，不被调用方复制；只产内容、不判定放行，缺前置就回 `BLOCKED`。

第 3 条不是硬门槛——不被别人调的工具型 skill（如 `codebase-analyzer`、`research`）
同样属于这里，标为 `standalone`，因为它的对象仍然是代码或写代码要依据的事实。

## 当前成员

按一段开发从想法到收尾的自然顺序排；**顺序只是阅读次序，不是调用约束**——谁需要谁调。

| skill | 典型触发场景 | 职责 |
|---|---|---|
| `setup-env` | 第一次在某个仓库用这套 skill 之前 | 配好 issue tracker、triage 标签与领域文档布局，写进 `docs/agents/` 与 `CLAUDE.md` |
| `triage` | issue / 外部 PR 堆着，要判它们各自该走向哪 | 让它们走过 triage 角色状态机：分类、验证、必要时拷问，落成 agent brief 或 `.out-of-scope/` 记录 |
| `wayfinder` | 一块工作大到一次会话装不下，路还裹在雾里 | 把它绘成 issue tracker 上的决策工单地图，一次解一张直到路清晰 |
| `grill-demand` | 有个想法要从头聊透，聊完直接交给 `to-spec` 出 spec | 组合 `grilling` 与 `domain-modeling`，按覆盖清单把问题与范围、行为、技术决策逐层钉死，边聊边落 ADR 与术语表 |
| `to-spec` | 一场讨论已经把要做什么聊清楚了，要直接固化成 spec | 不访谈，把当前对话综合成 spec（含 seam 决策）发布到 issue tracker 并打 `ready-for-agent` |
| `improve-codebase-architecture` | 想系统地找出代码库里值得深化的地方 | 扫出深化机会做成可视化 HTML 报告，再就选中的那个拷问到底 |
| `codebase-design` | 要设计或改进某个模块的接口，判 seam 该放哪、能不能深化 | 提供深模块设计词汇与判据：接口深浅、seam 位置、深化路径、多版接口对比 |
| `domain-modeling` | 术语在打架，或要把定下来的说法与决策记下来 | 打磨项目领域语言，术语当场写进 `CONTEXT.md`，难逆且反直觉的决策留成 ADR |
| `split-task` | 技术方案已定，要拆成能逐个验收的任务 | 把技术设计拆成可独立验收、带依赖与验证方式的任务清单 |
| `to-tickets` | 计划 / spec 定了，要把它变成 tracker 上带阻塞边的工单 | 拆成曳光弹式纵向切片，每张声明阻塞边，按依赖顺序发到 tracker 并打 `ready-for-agent` |
| `prototype` | 某个设计问题想不清楚，要用一次性代码验一验 | 逻辑分支做可分享的单 HTML 演示，界面分支在一条路由上出几个根本不同的变体 |
| `setup-worktree` | 动手前要隔离工作区，或多条开发线并行 | 基于确定基线建立并验证隔离的 git worktree |
| `implement` | 手上已有 spec 或工单，要直接把它做出来 | 照 spec / 工单实现：尽量用 `tdd` 在约定 seam 上做，收尾跑 `code-review`，再提交到当前分支 |
| `tdd` | 要用测试先行的方式落地一段行为改动 | 红 → 绿循环的参照：什么算好测试、seam 定在哪、反模式、循环规则 |
| `diagnosing-bugs` | 有个难缠的 bug 或性能回退要定位 | 先造出能变红的紧回路，再复现、最小化、排假设、埋点，修完留回归测试 |
| `review-changes` | 一段改动写完了，收尾 / 合并前要独立审一遍 | 对已写完的改动做独立审查，输出带 `file:line` 的分级 findings |
| `code-review` | 要审一段改动守不守仓库规范、做的是不是 issue / spec 要的东西 | 双轴审查：标准轴（成文规范 + Fowler 坏味道基线）与规格轴各派并行 subagent，结果并排不合并 |
| `finish-branch` | 开发完了，分支 / worktree 该怎么收口 | 收尾：清理调试代码、跑最终测试，再由用户拍板合并 / 保留 / 开 PR / 丢弃 |
| `git-commit-push` | 要解冲突，或把已完成的改动拆成原子提交并推送 | 解冲突，或把已完成的改动拆成原子提交并在确认后推送 |
| `codebase-analyzer` | 接手一个陌生项目，要先全局搞懂它 | 对陌生项目做全面调研，产出说明它做什么、怎么实现的报告 |
| `research` | 编码前要把某个技术事实核准，并留下可复查的依据 | 派后台 agent 查一手来源，把带逐项引用的结论落成仓库里的单个 Markdown |
| `wizard` | 有些步骤只有人能做：开服务、拿密钥、点第三方控制台 | 生成一个交互式 bash 向导，逐阶段带人走完，并把捕获到的值写进 `.env` / GitHub secret |

`grill-demand` 自己也是调用方：加载 `../support/grilling` 与 `domain-modeling`，判据住在被调 skill 里。

## 和 `../support/` 的边界

- **vs `support/`**：分界在**对象**，不在难度。改代码、审代码、写代码的依据 → 这里；
  对象是人（访谈、追问、问卷）或 agent 自身工程（配置、skill 测试）→ `support/`。
  典型对照：`review-changes` 审的是代码，在这里；`test-skill` 测的是 skill，在那边。

## 新增时

放进 `skills/development/<skill-id>/`，主体文件 `SKILL.md`，辅助资料放 `references/`，
脚本放 `scripts/`，Codex 侧界面描述放 `agents/openai.yaml`。会被别的 skill 调用的，
正文必须写明调用契约。**换分类就是移动目录**，没有别处需要同步分类信息
（发布路径除外：`.claude-plugin/plugin.json` 的 `skills` 数组含场景目录）。
