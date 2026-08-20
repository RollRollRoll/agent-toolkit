---
name: setup-env
description: 给这个仓库配置这套 skill 所假定的环境：issue tracker 与领域文档布局。第一次使用其他 skill 之前跑一次。
disable-model-invocation: true
---

# Setup Env

把这套 skill 所假定的**按仓库配置**搭起来：

- **Issue tracker**：issue 住在哪（默认 GitHub；本地 markdown 也开箱支持）
- **领域文档**：`CONTEXT.md` 和 ADR 住在哪，以及读它们的消费规则

**这是一个 prompt 驱动的 skill，不是一个确定性脚本。** 先探索、把发现摆出来、和用户确认，然后再写。

## 流程

### 1. 探索

看一眼当前仓库，搞清它的起始状态。**有什么读什么，不要假设**：

- `git remote -v` 和 `.git/config`：这是个 GitHub 仓库吗？哪一个？
- 仓库根的 `AGENTS.md` 和 `CLAUDE.md`：哪个存在？里面是不是已经有 `## Agent skills` 一节了？
- 仓库根的 `CONTEXT.md` 和 `CONTEXT-MAP.md`
- `docs/adr/` 以及任何 `src/*/docs/adr/` 目录
- `docs/agents/`：这个 skill 之前的产出是不是已经在了？
- `.scratch/`：说明这个仓库已经在用本地 markdown 的 issue 约定了
- **monorepo 信号**：`pnpm-workspace.yaml`、`package.json` 里的 `workspaces` 字段，
  或者一个填了内容、各自带 `src/` 的 `packages/*`。
  **这些只在真正的大型多包仓库里才有**；没有就是单上下文，**绝大多数仓库都是这种**。

### 2. 把发现摆出来并提问

**总结有什么、缺什么。** 然后按顺序过下面几节。**一节，一个回答，再下一节。**

**每一节都先给出推荐答案**，让用户一个字就能接受它。**只有在这个选择确实会分叉时才给一句解释**；
探索已经把它定死的那一节（比如没有 monorepo 时的 B 节）**直接跳过**。

**A 节：Issue tracker。**

> 解释：这里说的 "issue tracker" 就是这个仓库的 issue 住的地方。`wayfinder`、`code-review`
> 这些 skill 要从它读、往它写。它们需要知道是该调 `gh issue create`、
> 该在 `.scratch/` 下写个 markdown 文件，还是走你描述的别的流程。
> **挑你实际用来跟踪这个仓库工作的地方。**

**默认姿态**：这套 skill 是照着 GitHub 设计的。`git remote` 指向 GitHub 就提议 GitHub；
指向 GitLab（`gitlab.com` 或自建 host）就提议 GitLab。否则（或者用户另有偏好）给出这些选项：

- **GitHub**：issue 住在仓库的 GitHub Issues（用 `gh` CLI）
- **GitLab**：issue 住在仓库的 GitLab Issues（用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI）
- **本地 markdown**：issue 以文件形式住在本仓库的 `.scratch/<feature>/` 下
  （适合单人项目或没有远端的仓库）
- **其他**（Jira、Linear 等）：请用户用一段话描述这套流程，skill 会把它作为自由文本记下来

把选择记进 `docs/agents/issue-tracker.md`。

**B 节：领域文档。** 默认**单上下文**（仓库根一份 `CONTEXT.md` + `docs/adr/`）。
**这适合绝大多数仓库，不用问就这么写。**

**只有当探索发现了 monorepo 信号时**，才提供**多上下文**方案
（根目录一份 `CONTEXT-MAP.md` 指向各上下文自己的 `CONTEXT.md`）。那时再确认他们要哪种布局。

### 3. 确认并让他改

把草稿拿给用户看：

- 要加进 `CLAUDE.md` / `AGENTS.md`（选哪个见第 4 步）的那段 `## Agent skills` 块
- `docs/agents/issue-tracker.md` 与 `docs/agents/domain.md` 的内容

**让他先改，再写。**

### 4. 写

**挑要改的那个文件**：

- `CLAUDE.md` 存在 → 改它。
- 否则 `AGENTS.md` 存在 → 改它。
- **两个都不存在 → 问用户建哪一个，不要替他挑。**

**`CLAUDE.md` 已经存在时绝不去建 `AGENTS.md`**（反过来同理）；**永远改那个已经在的**。

如果选中的文件里**已经有** `## Agent skills` 块，**就地更新它的内容**，不要追加出一个重复的。
**不要覆盖用户对周围小节的修改。**

那段块：

```markdown
## Agent skills

### Issue tracker

[一句话说明 issue 跟踪在哪]。见 `docs/agents/issue-tracker.md`。

### Domain docs

[一句话说明布局："single-context" 还是 "multi-context"]。见 `docs/agents/domain.md`。
```

然后用这个 skill 目录下的种子模板作为起点，写出那些文档文件：

- [references/issue-tracker-github.md](references/issue-tracker-github.md)：GitHub issue tracker
- [references/issue-tracker-gitlab.md](references/issue-tracker-gitlab.md)：GitLab issue tracker
- [references/issue-tracker-local.md](references/issue-tracker-local.md)：本地 markdown issue tracker
- [references/domain.md](references/domain.md)：领域文档的消费规则 + 布局

选了"其他" issue tracker 时，**照用户的描述从零写** `docs/agents/issue-tracker.md`。

### 5. 收尾

告诉用户配置完成了，以及**现在有哪些 skill 会从这些文件里读**。
提一句他随时可以直接改 `docs/agents/*.md`；
**只有想换 issue tracker 或者想从头再来时，才需要重跑这个 skill。**
