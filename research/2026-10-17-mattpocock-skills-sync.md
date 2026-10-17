# mattpocock/skills 同步比对记录（第二次）

比对日期：2026-10-17。

结论：这次上游变化较多，**有 12 个已移植技能需要补同步**，多数是行为修正和命令修复，不涉及本地定制。另有三项设计决定需要确认：是否跟进 `CONTEXT.md` → `GLOSSARY.md` 改名、是否引入已转正的 `pr`、`implement-spec` 是否改为集成分支目标。

## 依据与范围

- 本地基线：`317c50f`，2026-10。上次比对记录见 [2026-09-23 报告](./2026-09-23-mattpocock-skills-sync.md)，其上游基线为 `c55ee46`（2026-09-18）。
- 上游快照：[49dd158](https://github.com/mattpocock/skills/commit/49dd158d1076134a641b33efb035946536778336)，2026-10-09。
- 增量范围：`c55ee46..49dd158`，约 70 个提交、118 个文件。其中 `docs/` 下的人读文档页大多是文风重写（"unslop"），本地没有对应文档页，不纳入比对。
- 本次是静态内容与提交历史比对，没有实际运行技能。

复核命令（在上游仓库中运行）：

```bash
git diff -M --stat c55ee46..49dd158 -- skills/
```

## 一、上游结构变化

| 变化 | 本地现状 | 判断 |
| --- | --- | --- |
| `implement-spec`、`pr`、`retro` 从 `in-progress` 转正到 `engineering` | 已有 `implement-spec`、`retro`；没有 `pr` | 见第二、三节 |
| 删除 `resolving-merge-conflicts`（文档页保留为归档） | 由 `git-commit-push` 覆盖冲突处理 | 无须处理，名称映射表移除该行 |
| `CONTEXT.md`/`CONTEXT-MAP.md` 改名为 `GLOSSARY.md`/`GLOSSARY-MAP.md`，`CONTEXT-FORMAT.md` 同步改名 | 本地 16 个文件仍用 `CONTEXT.md`，包括刚写的 `docs/agents/domain.md` 和 `AGENTS.md` | 需要决定，见第三节 |
| 新增实验技能 `chief-of-staff` | 无 | 暂不引入，见第四节 |
| 新增 `SCOPE.md` 与 `.out-of-scope/` 拒绝记录 | 无 | 作为设计参考，见第五节 |

`retro` 本地与上游正文逐字一致（`diff` 无输出），转正只是挪目录，无须改动。

来源：[转正提交 a7d038f](https://github.com/mattpocock/skills/commit/a7d038f)、[24f41cc](https://github.com/mattpocock/skills/commit/24f41cc)、[删除 daa01d8](https://github.com/mattpocock/skills/commit/daa01d8)、[改名 d80fa0f](https://github.com/mattpocock/skills/commit/d80fa0f)。

## 二、需要补同步的已有技能

按影响排序。"本地位置"均已核对，确认本地缺少对应内容。

### P1：行为或命令有误，建议尽快同步

**1. `implement-spec`**（[153fc1b](https://github.com/mattpocock/skills/commit/153fc1b)、[a31f3f6](https://github.com/mattpocock/skills/commit/a31f3f6)）

本地 `8b5eb0d` 曾"严格对齐上游原文"，但上游转正时改写了流程：

- 目标从"一个 PR"改为"在单一**集成分支**上实现整份 spec，按 tracker 的关闭方式关闭每张工单"。
- 新增 tracker 指针：tracker 未配置时让用户运行 setup。
- 第 3 步：先建集成分支；只有 tracker 通过 PR 关闭工单或用户要求时，才在**第一次合并之后**开草稿 PR。原流程在没有提交时就开 PR，GitHub 会拒绝。
- 第 4 步：每个实现子 agent 先确认 worktree 基于集成分支，否则重置；用 Skill 工具调 `tdd`；汇报前先合入集成分支最新提交。
- 第 7、8 步：用 Skill 工具调 `code-review`；没有 PR 时按 tracker 方式关闭工单并报告集成分支。
- `description` 与 `openai.yaml` 改为"实现 /to-spec 与 /to-tickets 的结果"。

**2. `setup-env` 的 tracker 模板**（[5b7cade](https://github.com/mattpocock/skills/commit/5b7cade)、[e0efb6e](https://github.com/mattpocock/skills/commit/e0efb6e)、[cffab50](https://github.com/mattpocock/skills/commit/cffab50)）

- `SKILL.md`：B 节运行过且 tracker 是 GitHub/GitLab 时，用 `gh label create` / `glab label create` 创建缺少的标签。本地目前只写配置文件，不建标签。
- `references/issue-tracker-github.md`：
  - 读 issue 改为 `gh issue view <n> --json number,title,body,labels,comments`（本地第 8、40 行仍是含糊的 `--comments` + jq）。
  - 列外部 PR 改用 REST `pulls` 端点和 `author_association` 字段（本地第 26 行用的 `gh pr list --json authorAssociation`，`gh` 不提供这个字段，命令必定失败）。同时由白名单改为排除 `OWNER`/`MEMBER`/`COLLABORATOR`，原白名单会漏掉 `FIRST_TIMER` 作者。
  - 新增"设为子 issue"操作：`gh issue create --parent`、`gh issue edit --add-sub-issue`（gh 2.94+），旧版用 `gh api` sub_issues 端点；wayfinder 子工单改为引用这条。
- `references/issue-tracker-gitlab.md`：`glab issue list -F json` 改为 `-O json`（本地第 11、60 行），前沿查询的 links 端点写明 `<child-iid>`。
- `references/triage-labels.md`："右侧标签列"改为按列名指代。

**3. `wizard/scripts/template.sh`**（[868c4cf](https://github.com/mattpocock/skills/commit/868c4cf)、[49dd158](https://github.com/mattpocock/skills/commit/49dd158)）

一组模板缺陷修复，本地模板只做了注释汉化，逻辑与旧上游一致：

- `.env` 新建时权限为 `0600`，写入时保持原权限并能穿过符号链接（原来 `mv` 会替换链接、丢权限）。
- 值统一用单引号写入并正确转义；读回时还原单引号和普通双引号值，含转义的双引号值放弃复用并重新询问。
- `ask` 改用 `read -e`（支持 Readline 编辑），提示符颜色码用 `\001..\002` 包裹；`ask`/`ask_secret` 遇 EOF 且无输入时返回失败，不再静默写空值。
- 所有 stage 包进 `run_wizard()`，末行 `run_wizard "$@"; exit`，避免运行中编辑脚本导致解析错乱。
- `_clear`、`open_url` 的失败分支修正；删掉未使用的 `RED`。

建议按上游新版逻辑重写本地模板，保留中文注释。

### P2：规则补强，建议同步

**4. `implement`**（[6d6a5b9](https://github.com/mattpocock/skills/commit/6d6a5b9)、[e48341a](https://github.com/mattpocock/skills/commit/e48341a)）

- 用户传入工单引用时，先从 tracker 取回并说出标题；引用有歧义就问。
- "使用 `tdd`/`code-review`"改为"用 Skill 工具调用"，避免 agent 只按名字凭记忆执行。

**5. `to-tickets`**（[cffab50](https://github.com/mattpocock/skills/commit/cffab50)、[9e2abf8](https://github.com/mattpocock/skills/commit/9e2abf8)）

- 来源是已有 issue 时，把每张工单设为它的子 issue（调用 tracker 文档中的操作）。
- 原生阻塞关系只用 blocking，不再写"blocking / sub-issue"并列。
- 模板中阻塞边已用原生关系设置时，省略 `Blocked by` 小节。

本地第 94 行"不要关闭或修改任何父 issue"与上游同样保留；挂子 issue 是在子工单一侧建立关系，两者不冲突。依赖第 2 项的子 issue 操作。

**6. `wayfinder`**（[8295b8e](https://github.com/mattpocock/skills/commit/8295b8e)）

- 地图和工单只带 `wayfinder:` 标签，不打 `ready-for-agent` 等 triage 标签。
- 第二遍接线时同时写交叉引用，必须用真实 id：占位的 `#<n>` 会自动链到无关 issue。
- research 分支推送但不开 PR，它不会被合并。
- 推进地图第 3 步：按 `wayfinder:<type>` 标签决定工单类型，正文不写类型。

**7. `code-review`**（[3da8c01](https://github.com/mattpocock/skills/commit/3da8c01)）

- 标准来源改为"搜索仓库中所有描述代码写法的文件；`CODING_STANDARDS.md`、`CONTRIBUTING.md` 存在时必须列入"。本地是举例式写法，可能漏找。
- 两个子 agent 同时、**前台**派出，再汇总结果。避免后台运行后主流程提前结束。
- tracker 提示从"`docs/agents/issue-tracker.md` 不在"改为"tracker 未提供"。本地还要求"停下来"，属于本地加严，可保留，只调整判断条件。

**8. `diagnosing-bugs`**（[f3fc563](https://github.com/mattpocock/skills/commit/f3fc563)）

修复阶段第 2 步：如果靠修改代码或 fixture 制造红灯，先和原始副本 `diff`，确认改动确实生效，再相信这次失败。

**9. `tdd`**（[3f59913](https://github.com/mattpocock/skills/commit/3f59913)）

提出每个 seam 时附一行说明：它能发现什么、发现不了什么。本地第 30 行附近补一句即可。

### P3：小修正，顺手同步

| 技能 | 上游改动 | 来源 |
| --- | --- | --- |
| `grilling` | 每个问题的措辞要让用户回答"是"即表示接受推荐答案 | [95249b0](https://github.com/mattpocock/skills/commit/95249b0) |
| `handoff` | 临时目录解析顺序写明：`$TMPDIR`，否则 `/tmp`；Windows 用 `%TEMP%` | [4f4e943](https://github.com/mattpocock/skills/commit/4f4e943) |
| `teach` | 工作区路径从运行 `/teach` 的目录解析，只有格式文件链接从技能目录解析；测验正确答案的位置要轮换 | [ad5400b](https://github.com/mattpocock/skills/commit/ad5400b) |
| `codebase-design`、`domain-modeling` 等 | 只有 GLOSSARY 改名，跟随第三节决定 | [d80fa0f](https://github.com/mattpocock/skills/commit/d80fa0f) |

`re-explain`（对应 `wait-what`）、`triage`、`improve-codebase-architecture` 的上游改动也只有改名。

## 三、需要确认的设计决定

### A. 是否跟进 `CONTEXT.md` → `GLOSSARY.md` 改名

上游提交没有写改名理由，CHANGELOG 只说明这是破坏性变更：技能今后只找 `GLOSSARY.md`，旧文件需要 `git mv`。

- 跟进的好处：与上游一致，以后同步省去逐处换名；`GLOSSARY` 也更准确地表达"只放术语"，不易与 agent 上下文文件混淆。
- 成本：改 16 个文件（含 `context-format.md` 改名、`AGENTS.md`、`docs/agents/domain.md`、README）；已经按旧名使用本工具集的其他仓库需要迁移。本仓库还没有实际的 `CONTEXT.md`，迁移成本只在文本层面。

建议：跟进改名，同时在 `setup-env/references/domain.md` 加一句兼容规则：只找到旧名 `CONTEXT.md` 时照常读取，并提示可以改名。这比上游的硬切换更稳妥。

### B. 是否引入 `pr`

上次报告把它列为实验候选，现在已转正，并被 `ask-matt` 写进主流程：agent 写 PR 正文时自动调用。内容是三段模板：Summary（选最小的可视化：伪代码、调用树、组件树、文件树、Mermaid、diff）、Evidence（前后对比，截图优先，其次测试或输出）、Merge Danger（单向门还是双向门，影响范围）。

本地 `finish-branch` 和 `implement-spec` 都会创建 PR，但没有正文格式规范，引入有实际价值。

建议：作为模型可触发技能引入 `skills/development/pr/`。移植时：

- "单向门/双向门"改写为直白表达，如"能否低成本回滚"；
- 保留 `metadata.credits` 和 `CREDITS.md` 对 Humanlayer `show-me` 的署名；
- 在 `finish-branch` 创建 PR 的步骤里用 Skill 工具引用它。

### C. `implement-spec` 是否改为集成分支目标

第二节第 1 项若照上游同步，会改变本地现有的"交付一个 PR"约定，`openai.yaml` 的短描述也要改。本地 `AGENTS.md` 配置的 tracker 是 GitHub Issues，PR 关闭工单仍是常见路径，按上游新逻辑仍会开 PR，只是时机推后。建议照上游同步。

## 四、其他上游新增或变化

| 项目 | 建议 |
| --- | --- |
| `chief-of-staff`（实验） | 暂不引入。长期会话里协调子 agent 和定时任务，并持续改进 agent 工作环境。上游 10 月初仍在频繁调整，且与本地 `retro` 的"改进环境"职责有重叠，等转正再评估 |
| `ask-matt` 路由更新 | 仍不引入。若以后做本地路由技能，可参考它的新主流程：`to-tickets` 之后可选 `implement` 逐张或 `implement-spec` 整体，写 PR 时用 `pr`，最后用 `retro` 收尾 |
| `claude-handoff` 修正（摘要先存临时文件再传给 `claude --bg`，避免 shell 展开） | 本地未引入该技能，无须处理 |
| `in-progress/README.md` | 只是移除已转正条目 |

## 五、可参考的上游设计原则

上游新增 `SCOPE.md` 和 `.out-of-scope/`，记录明确拒绝的方向。其中几条与本地设计相关：

- **不为子 agent 递归加防护**：限制嵌套深度是运行环境的职责，写在单个技能里只覆盖该技能，还要花 token。本地技能目前没有此类防护，保持即可。
- **grilling 不走原生提问工具**：用纯文本提问，避免结构化选项把访谈推向选择题。本地 `grilling` 符合；`codebase-analyzer` 第 182 行允许使用 AskUserQuestion，它不是访谈技能，不受影响。
- **`retro` 总是加载 `writing-for-agents`**：判断 no-op 指令和技能质量需要这份标准，不能等到写入前才加载。本地 `retro` 与上游一致。
- **新技能门槛**：能由现有技能组合出的行为，不新增技能。本地引入 `pr` 前也应按此检验：它提供的是独立的正文格式规范，无法由现有技能组合得到，可以通过。

来源：[SCOPE.md](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/SCOPE.md)、[.out-of-scope/](https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/.out-of-scope)。

## 六、更新后的名称映射

在上次映射表基础上：移除 `resolving-merge-conflicts`（上游已删）；如引入 `pr`，增加 `pr` → `pr`；如跟进改名，`context-format.md` → `glossary-format.md`。

## 后续维护

- 下次比对以上游 `49dd158` 为基线。
- 同步落地时，按本地 README 约定同时更新中文正文、辅助资源、`openai.yaml`、Claude 插件登记、技能一览和版本号。
- 落地情况（分支 `sync/mattpocock-2026-10`，版本 1.1.0）：三项设计决定均按建议执行，第二节全部同步。
  - 改名：16 个文件 `CONTEXT.md` → `GLOSSARY.md`，`context-format.md` → `glossary-format.md`；`domain.md`、`setup-env`、`glossary-format.md` 三处加入旧名兼容规则。
  - `pr`：新增 `skills/development/pr/`（含 `CREDITS.md` 与 `metadata.credits`），`finish-branch` 创建 PR 时调用。
  - 本仓库自己的 `docs/agents/issue-tracker.md` 与 `triage-labels.md` 同步了模板修正。
  - 验证：插件登记与 32 个技能目录一致，调用策略与 `openai.yaml` 对应，本地 Markdown 链接无断链，`claude plugin validate .` 通过；wizard 模板通过 `bash -n` 和 `.env` 读写冒烟测试。
