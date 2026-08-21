# 写 Agent Brief

**agent brief** 是一条结构化的评论，在一个 GitHub issue 或 PR 挪到 `ready-for-agent` 时发上去。
它是**那个 AFK agent 将要照着干活的权威规格**。原始正文和讨论是上下文，**agent brief 才是契约**。

brief 说的是 **agent 该做什么**，这句话覆盖两个面：issue 上是从零把改动做出来；
PR 上是**对着已有的那份 diff 还剩什么要做**——把它做完、补上缺口、处理评审意见。
两边原则一样，下面的 PR 例子展示差别在哪。

## 原则

### 经得起时间，胜过精确

这个 issue 可能在 `ready-for-agent` 上待好几天甚至几周，**这期间代码库会变**。
**把 brief 写成即使文件被改名、挪走、重构，它依然有用的样子。**

- **要**描述接口、类型和行为契约
- **要**点名 agent 该去找或该去改的具体类型、函数签名或配置形状
- **不要**引用文件路径：它们会过时
- **不要**引用行号
- **不要**假设当前的实现结构会保持不变

### 讲行为，不讲步骤

描述系统**该做什么**，而不是**怎么实现**。**agent 会自己重新探索代码库，自己做实现决策。**

- **好**：「`SkillConfig` 类型应该接受一个可选的 `schedule` 字段，类型是 `CronExpression`」
- **坏**：「打开 src/types/skill.ts，在第 42 行加一个 schedule 字段」
- **好**：「用户不带参数跑 `/triage` 时，应该看到一份需要处理的 issue 摘要」
- **坏**：「在主 handler 函数里加一个 switch」

### 完整的验收标准

**agent 需要知道自己什么时候算做完了。** 每一份 agent brief **都必须有具体、可测的验收标准**，
**每一条都能独立验证**。

- **好**：「跑 `gh issue list --label needs-triage` 会返回那些已经过初步分类的 issue」
- **坏**：「triage 应该正常工作」

### 明确的范围边界

**写清什么在范围之外。** 这能防止 agent 镀金，或者对相邻功能自己作假设。

## 模板

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** 一句话说明要发生什么

**Current behavior:**
描述现在会发生什么。bug 就是那个坏掉的行为；
enhancement 就是这个功能所依托的现状。

**Desired behavior:**
描述 agent 干完之后该发生什么。边界情况与错误条件要具体。

**Key interfaces:**
- `TypeName`：要改什么、为什么
- `functionName()` 的返回类型：现在返回什么 vs 应该返回什么
- 配置形状：需要哪些新的配置项

**Acceptance criteria:**
- [ ] 具体、可测的标准 1
- [ ] 具体、可测的标准 2
- [ ] 具体、可测的标准 3

**Out of scope:**
- 这个 issue 里**不**该改、不该碰的东西
- 看起来相关、其实是另一回事的相邻功能
```

## 例子

### 好的 agent brief（bug）

```markdown
## Agent Brief

**Category:** bug
**Summary:** skill description 截断时从词中间断开，产出坏掉的输出

**Current behavior:**
skill description 超过 1024 个字符时，会被正好在 1024 字符处截断，
完全不管词边界。于是产出的 description 会停在词的中间
（比如 "Use when the user wants to confi"）。

**Desired behavior:**
截断应该发生在 1024 字符之前的最后一个词边界上，
并追加 "..." 表示它被截断了。

**Key interfaces:**
- `SkillMetadata` 类型的 `description` 字段：类型不用改，
  但填充它的那段校验 / 处理逻辑需要尊重词边界
- 任何读 SKILL.md frontmatter 并抽出 description 的函数

**Acceptance criteria:**
- [ ] 1024 字符以内的 description 保持不变
- [ ] 超过 1024 字符的 description 在 1024 字符之前的最后一个词边界处截断
- [ ] 被截断的 description 以 "..." 结尾
- [ ] 含 "..." 在内的总长度不超过 1024 字符

**Out of scope:**
- 改 1024 这个上限本身
- 多行 description 支持
```

### 好的 agent brief（enhancement）

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 加上 `.out-of-scope/` 目录支持，用来记录被拒的功能请求

**Current behavior:**
一个功能请求被拒时，这个 issue 会带着 `wontfix` 标签和一条评论被关掉。
这个决定和它的理由**没有留下持久记录**。以后再来类似的请求，
维护者只能靠回忆，或者去翻当初那场讨论。

**Desired behavior:**
被拒的功能请求应该记进 `.out-of-scope/<concept>.md` 文件，
把决定、理由，以及所有请求过这个功能的 issue 链接都记下来。
triage 新 issue 时，这些文件应该被拿来比对。

**Key interfaces:**
- `.out-of-scope/` 里的 markdown 文件格式：每个文件有一个 `# Concept Name` 标题、
  一行 `**Decision:**`、一行 `**Reason:**`，以及一份带 issue 链接的 `**Prior requests:**` 列表
- triage 流程应该**早早**读完所有 `.out-of-scope/*.md`，
  并按概念相似度把进来的 issue 与它们比对

**Acceptance criteria:**
- [ ] 把一个功能关成 wontfix 时，会在 `.out-of-scope/` 里创建或更新一个文件
- [ ] 这个文件包含决定、理由，以及那个被关掉的 issue 的链接
- [ ] 已经存在匹配的 `.out-of-scope/` 文件时，新 issue 被追加进它的 "Prior requests" 列表，
      而不是另建一个重复文件
- [ ] triage 期间会检查已有的 `.out-of-scope/` 文件，并在新 issue 与之前某次拒绝对上时把它摆出来

**Out of scope:**
- 自动匹配（由人来确认这个匹配）
- 重开之前被拒的功能
- bug 报告（只有 enhancement 类的拒绝才进 `.out-of-scope/`）
```

### 好的 agent brief（PR）

PR 的情况下，"Current behavior" 描述的是**这份 diff 的状态**，
brief 要求 agent **把它做完或修好**，而不是从零开始建。

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 把贡献者给 `triage list` 加的 `--json` 输出 flag 做完

**Current behavior:**
这个 PR 加了一个 `--json` flag，把 issue 列表序列化成 JSON。
happy path 能用，diff 也符合本项目的命令结构。还剩两个缺口：
错误仍然按人读的文本打印（不是 JSON），而且这个新 flag 没有测试覆盖。

**Desired behavior:**
带上 `--json` 时，所有输出（包括错误）都是 stdout 上格式良好的 JSON，
命令的退出码不变。不带这个 flag 时，原有的人读输出原封不动。

**Key interfaces:**
- 这个命令的错误路径在 `--json` 下应该发出 `{ "error": string }`，而不是纯文本错误
- 复用这个 PR 已经加进去的那个序列化器，不要再引入第二个

**Acceptance criteria:**
- [ ] `triage list --json` 在成功和出错两种情况下都发出合法 JSON
- [ ] 退出码与非 JSON 的命令一致
- [ ] 有一个测试覆盖 `--json` 的成功输出和一个错误情形
- [ ] 默认（非 JSON）输出逐字节不变

**Out of scope:**
- 给别的命令加 `--json`
- 改这个 PR 已经定下来的成功 payload 的 JSON 形状
```

### 坏的 agent brief

```markdown
## Agent Brief

**Summary:** 修一下 triage 的 bug

**What to do:**
triage 那个东西坏了。看一下主文件，把它修了。
大概第 150 行那个函数有问题。

**Files to change:**
- src/triage/handler.ts（第 150 行）
- src/types.ts（第 42 行）
```

它坏在：

- 没有分类
- 描述含糊（「triage 那个东西坏了」）
- 引用了会过时的文件路径和行号
- 没有验收标准
- 没有范围边界
- 没说清现状行为与期望行为
