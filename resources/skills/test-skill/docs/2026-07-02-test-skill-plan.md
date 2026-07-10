# test-skill 实现计划

> **历史记录（2026-07-10 标注）**：本文是已经执行过的初版计划，其中命令模板、权限边界与报告路径不再适用。现行契约以 `../SKILL.md` 与 `../scripts/run-headless.py` 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 agent-toolkit 新增 `test-skill`——对任意 skill 发起 headless 盲测跑，事后逐步骤溯源并产出中文复盘报告。

**Architecture:** 编排者（执行 test-skill 的 agent）解析目标 SKILL.md 为编号指令清单，在沙箱中用 `claude -p` headless 进程盲测目标 skill（多轮 `--resume` 驱动 + 剧本扮演用户），stream-json 落盘后做步骤/指令双侧判定，按模板产出报告。交付物全部是文档（SKILL.md + references 模板），无程序代码。

**Tech Stack:** Claude Code headless CLI（`claude -p`、`--output-format stream-json`、`--resume`）、Bash、python3（仅解析 jsonl 用的单行命令）。

**设计依据:** `resources/skills/test-skill/docs/2026-07-02-test-skill-design.md`（下称"设计文档"）。执行每个任务前先读它。

## Global Constraints

- 所有产出文档、指令、报告一律中文。
- SKILL.md frontmatter description 只写"何时触发/何时不用"，不写工作流程（仓库既有惯例）。
- 遵循 `docs/conventions.md`：目录名 = metadata id = `test-skill`；metadata.yaml 字段齐全；新资源 status 从 `draft` 起步。
- 零侵入：任何任务不得修改被测 skill 本身。
- 禁止 `--dangerously-skip-permissions`；headless 权限固定为 `--permission-mode acceptEdits` + `--allowedTools` 白名单。
- 盲测红线：对被测 headless 进程的任何输入（含 fixture 文件内容）不得出现"测试/评估/复盘/检查你"等透露测试意图的表述。
- 提交信息风格：`类型(test-skill): 中文描述`；直接提交 main（仓库惯例，无 push）。每次 `git commit` 前按用户全局规范请求确认；若用户在执行开始时明确给予本计划范围的批量授权，则逐任务直接提交。
- 实验/测试跑的沙箱一律放会话 scratchpad，不入库。

---

## File Structure

```text
resources/skills/test-skill/
  SKILL.md                                  # Task 2：skill 主体（六阶段流程指令）
  README.md                                 # Task 4：仓库内说明
  metadata.yaml                             # Task 4：资源元数据
  references/
    judging-criteria.md                     # Task 3：溯源判定标准（唯一判定口径）
    report-template.md                      # Task 3：复盘报告六节模板
    persona-template.md                     # Task 3：模拟用户剧本模板
  docs/
    2026-07-02-test-skill-design.md         # 已有（设计文档）
    2026-07-02-test-skill-plan.md           # 本计划
    2026-07-02-assumption-test-notes.md     # Task 1：技术假设实测结论
resources/skills/refine-idea/docs/
  test-report-2026-07-02.md                 # Task 6：真实冒烟产出的复盘报告
.claude-plugin/plugin.json                  # Task 7：发布时增补 skills 数组并递增版本
.claude-plugin/marketplace.json             # Task 7：双清单版本同步
```

---

### Task 1: 实测 4 条技术假设（设计文档第 8 节）

**Files:**
- Create: `resources/skills/test-skill/docs/2026-07-02-assumption-test-notes.md`
- 实验沙箱: `<scratchpad>/assumption-probe/`（不入库）

**Interfaces:**
- Consumes: 设计文档第 8 节的 4 条假设及其退路。
- Produces: 每条假设的 PASS/FAIL 结论 + 修正后的**命令模板终稿**（Task 2 的 SKILL.md 必须逐字采用该终稿）。

- [ ] **Step 1: 建实验沙箱**

```bash
PROBE=/tmp/claude-0/-root-workspace-agent-toolkit/7b6b141d-f707-4db4-8640-a2255f33f3eb/scratchpad/assumption-probe
mkdir -p "$PROBE" && cd "$PROBE" && git init
```

预期：空 git 仓库建立。

- [ ] **Step 2: 假设 1——stream-json 是否需要 --verbose**

```bash
cd "$PROBE"
timeout 180 claude -p "只回答数字：1+1=?" --output-format stream-json --verbose --model haiku > v1.jsonl 2> v1.err
timeout 180 claude -p "只回答数字：2+2=?" --output-format stream-json --model haiku > v0.jsonl 2> v0.err
python3 -c "
import json
for f in ['v1.jsonl','v0.jsonl']:
    types=set()
    for line in open(f):
        line=line.strip()
        if line: types.add(json.loads(line).get('type'))
    print(f, sorted(types))
"
```

检查点：哪个参数组合输出了逐轮 `assistant`/`user` 消息事件（而不是只有 `result`）。若两者行为一致则 `--verbose` 可省；记录结论。

- [ ] **Step 3: 假设 4——thinking 块可获得性（用会话默认模型）**

```bash
cd "$PROBE"
timeout 300 claude -p "先想清楚再答：一个农夫要带狼、羊、白菜过河，船每次只能带一样，怎么过？" --output-format stream-json --verbose > v4.jsonl 2> v4.err
python3 -c "
import json
blocks=set()
for line in open('v4.jsonl'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d.get('type')=='assistant':
        for c in d.get('message',{}).get('content',[]):
            blocks.add(c.get('type'))
print(sorted(blocks))
"
```

检查点：输出块集合是否含 `thinking`。无 thinking → 按设计文档假设 4 退路，Task 3 判定标准中收紧意图推断的置信度表述。

- [ ] **Step 4: 假设 2——headless 多轮 --resume**

```bash
cd "$PROBE"
SID=$(python3 -c "
import json
for line in open('v1.jsonl'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d.get('session_id'): print(d['session_id']); break
")
echo "SID=$SID"
timeout 180 claude -p --resume "$SID" "我上一条消息问的算术题是什么？" --output-format stream-json --verbose --model haiku > v2.jsonl 2> v2.err
grep -o "1+1" v2.jsonl | head -1
python3 -c "
import json
for line in open('v2.jsonl'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d.get('session_id'): print('round2 session_id:', d['session_id']); break
"
```

检查点：① 第二轮回答提到 1+1（上下文延续成立）；② 第二轮 session_id 与首轮是否相同——**记录后续每轮应使用哪个 id**（沿用原 id 还是逐轮取新 id）。FAIL → 依次尝试 `--session-id` 固定会话；仍不行则记录"退回设计文档方案 A"，并停下向用户报告（这是设计层变更，不得静默切换）。

- [ ] **Step 5: 假设 3——沙箱项目级 skill 的加载与同名遮蔽**

```bash
mkdir -p "$PROBE/.claude/skills/probe-echo"
cat > "$PROBE/.claude/skills/probe-echo/SKILL.md" <<'EOF'
---
name: probe-echo
description: 当用户要求使用 probe-echo 时使用
---

# probe-echo

收到任何输入，回复第一行必须是【PROBE-OK】，第二行复述用户输入。
EOF
cd "$PROBE"
timeout 180 claude -p "使用 probe-echo skill：你好" --output-format stream-json --verbose --model haiku > v3.jsonl 2> v3.err
grep -c "PROBE-OK" v3.jsonl

mkdir -p "$PROBE/.claude/skills/write-spec"
cat > "$PROBE/.claude/skills/write-spec/SKILL.md" <<'EOF'
---
name: write-spec
description: 当用户要求使用 write-spec 时使用
---

# write-spec（探针副本）

收到任何输入，回复第一行必须是【LOCAL-WIN】。
EOF
timeout 180 claude -p "使用 write-spec skill：随便回应一下" --output-format stream-json --verbose --model haiku > v5.jsonl 2> v5.err
grep -c "LOCAL-WIN" v5.jsonl
```

检查点：① `PROBE-OK` 出现 → 项目级 skill 在 headless 下被加载；② `LOCAL-WIN` 出现 → 项目级遮蔽已安装插件同名 skill。②失败 → 采用设计文档退路：注入时改用未占用名字的副本（如 `<id>-under-test`），测试任务 prompt 中点名副本名；把该退路写进 notes，Task 2 遵照执行。

- [ ] **Step 6: 写实测结论文档**

创建 `resources/skills/test-skill/docs/2026-07-02-assumption-test-notes.md`，内容含：每条假设的实测命令、原始输出关键行、PASS/FAIL、对后续任务的影响；末尾给出**命令模板终稿**（首轮 + 续轮 + session_id 提取，逐字，供 Task 2 复制）。终稿初始形态（按实测修正）：

```bash
# 首轮（cwd = 测试沙箱）
timeout 600 claude -p "$FIRST_PROMPT" \
  --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Bash(git:*)" \
  >> transcript-run.jsonl 2>> stderr.log

# session_id 提取
SID=$(python3 -c "
import json
for line in open('transcript-run.jsonl'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d.get('session_id'): print(d['session_id']); break
")

# 续轮
timeout 600 claude -p --resume "$SID" "$SIMULATED_USER_REPLY" \
  --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Bash(git:*)" \
  >> transcript-run.jsonl 2>> stderr.log
```

- [ ] **Step 7: 提交**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/test-skill/docs/2026-07-02-assumption-test-notes.md
git -C /root/workspace/agent-toolkit commit -m "docs(test-skill): 实测并记录 headless 驱动的 4 条技术假设"
```

---

### Task 2: 撰写 SKILL.md 主体

**Files:**
- Create: `resources/skills/test-skill/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的命令模板终稿（逐字采用）；设计文档第 4/5/6/7/9 节。
- Produces: 六阶段流程指令，其中三处引用 `references/judging-criteria.md`、`references/report-template.md`、`references/persona-template.md`（Task 3 按这三个确切文件名交付）。

- [ ] **Step 1: 写 frontmatter**

```markdown
---
name: test-skill
description: 当用户想测试/复盘某个 skill 的实际执行效果时使用——如"测一下这个 skill、复盘 skill 执行、看看 agent 是不是按 skill 写的做的、skill 覆盖率/溯源报告"。对目标 skill 发起一次 headless 盲测跑并产出逐步骤溯源的中文复盘报告。不要用于：写新 skill（用 writing-skills 类流程）、调试业务代码、code review、对"当前会话里已发生的执行"做复盘（本 skill 只做主动测试跑）。
---
```

- [ ] **Step 2: 写六阶段正文**

章节与每章硬性指令（正文按此展开成完整中文指令，含解释与示例；以下清单是验收锚点，每条都必须在正文中有对应指令）：

**阶段 0 预检与输入确认**
1. 确认 claude CLI 可用：`claude --version` 成功返回。
2. 解析目标 skill 三种输入形式：仓库 id（`resources/skills/<id>/SKILL.md`）/ SKILL.md 路径 / 已安装 skill 名（在插件缓存中定位）。定位失败即停并向用户列出找到的候选。
3. 用户未给测试场景时，编排者依据目标 skill 的 description 设计一个适用场景，连同剧本一起交用户确认。

**阶段 1 指令清单化**
4. 读 SKILL.md 全文，拆出编号指令 R1..Rn；一条指令 = 一个可独立判定遵守与否的行为要求。
5. 纯背景/动机段落记为背景条目（B1..Bm），不参与覆盖统计，供诊断引用。
6. frontmatter description 拆出的"何时不用"条目纳入指令清单。
7. 清单落盘沙箱 `checklist.md`（格式：编号、原文摘录、所在章节、适用条件）。

**阶段 2 沙箱搭建**
8. 沙箱建在会话 scratchpad 下独立目录，`git init`。
9. 按场景铺 fixture；fixture 内容不得出现测试意图表述（盲测红线）。
10. 注入被测 skill：复制目标 skill 当前版本到 `沙箱/.claude/skills/<注入名>/`；注入名按 Task 1 假设 3 结论（原名或 `<id>-under-test` 副本名）。

**阶段 3 剧本与开跑确认**
11. 按 `references/persona-template.md` 生成剧本，必含隐藏痛点与不透露边界。
12. 向用户呈现：场景、剧本要点、预计轮数与 token 成本预估，取得确认后才开跑（用户可跳过剧本细节审阅，不可跳过成本确认）。

**阶段 4 盲测驱动循环**
13. 首轮/续轮命令逐字采用 Task 1 终稿；cwd 必须是沙箱。
14. 首轮 prompt 用普通用户口吻显式点名被测 skill（注入名），不透露测试意图。
15. 每轮结束读 transcript 增量，判断上轮输出属于：等待用户输入 → 按剧本生成回复继续；收尾陈述 → 停止。
16. 剧本未覆盖的问题按人设即兴，即兴问答追记进剧本附录。
17. 停止条件三选一：收尾判定 / 轮数上限（默认 10，开跑确认时可调）/ 单轮 timeout 600 秒。
18. 被测进程报错或权限拒绝：不重试超过 1 次，记录现象，进入分析阶段（失败也是复盘素材）。

**阶段 5 溯源分析**
19. 解析 transcript 重建语义步骤时间线；判定口径唯一依据 `references/judging-criteria.md`。
20. 每步judgment三选一（依据 Rx / 偏离 Rx / 无依据）；每条指令四选一（已遵守 / 被违反 / 被跳过 / 未触发）。
21. transcript 超过 200k 字符时 spawn 子 agent 分段分析（按轮切分），编排者汇总并统一判定口径。
22. 被测 agent 未触发目标 skill：直接进入报告，作为触发失败发现。

**阶段 6 报告**
23. 按 `references/report-template.md` 产出中文报告。
24. 存放：目标 skill 属于本仓库 → `resources/skills/<被测id>/docs/test-report-YYYY-MM-DD.md`；否则 → 当前工作目录 `skill-test-reports/`。
25. 报告末尾提示：沙箱为会话级临时目录，原始 transcript 长期留存需自行拷贝。

**红线汇总节**（正文末尾集中重申）：盲测红线；禁止 `--dangerously-skip-permissions`；零侵入被测 skill；成本确认门不可跳过。

- [ ] **Step 3: 验收核对**

逐条核对上述 25 条锚点在正文中存在对应指令；命令模板与 Task 1 notes 终稿逐字一致；description 无工作流程内容。

- [ ] **Step 4: 提交**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/test-skill/SKILL.md
git -C /root/workspace/agent-toolkit commit -m "feat(test-skill): 新增 skill 盲测复盘主体流程"
```

---

### Task 3: 撰写 references 三文档

**Files:**
- Create: `resources/skills/test-skill/references/judging-criteria.md`
- Create: `resources/skills/test-skill/references/report-template.md`
- Create: `resources/skills/test-skill/references/persona-template.md`

**Interfaces:**
- Consumes: 设计文档第 5.4/6/9 节；Task 1 假设 4 结论（thinking 可得性影响判定置信度表述）。
- Produces: Task 2 SKILL.md 引用的三个确切文件；Task 5/6 执行时的判定与产出口径。

- [ ] **Step 1: judging-criteria.md**

必含内容：
- 语义步骤定义：一步 = 一次有意图的动作（提一个澄清问题 / 调一次工具 / 给一段结论）；thinking 块只辅助判断意图，不单独成步。
- 三类步骤判定的操作性定义，各配 1 个正例 + 1 个边界例（例如："agent 问了澄清问题但一次问了三个，目标 skill 要求一次一个 → 判`偏离 Rx`而非`依据 Rx`"）。
- 四类指令状态定义；重点写清"被跳过 vs 未触发"区分规则：场景满足指令的适用条件而 agent 未做 → 被跳过；场景根本未到达适用条件 → 未触发。
- 置信度规则：判定依据不足时标注"存疑"并附原文引用；thinking 不可得（按 Task 1 结论）时，意图推断类判定一律降为存疑。
- 汇总统计口径：遵守率 = 已遵守 /（已遵守+被违反+被跳过），未触发不计入分母。

- [ ] **Step 2: report-template.md**

六节模板（测试概要 / 步骤溯源表 / 指令覆盖统计 / 设计诊断 / 修改建议 / 附录），每节给出字段清单与一条示例行；修改建议节要求措辞落到"对 SKILL.md 第 X 节的具体编辑动作"。

- [ ] **Step 3: persona-template.md**

字段：身份背景 / 真实意图 / 隐藏痛点（首轮不说出）/ 常见问题答案素材 / 回答风格（简短度、含糊度）/ 不透露边界 / 即兴追记附录（空表头）。附一个 100 字内示例片段。

- [ ] **Step 4: 验收核对**

SKILL.md 三处引用路径与文件名逐字一致；三文档间术语一致（判定名称、状态名称与 SKILL.md 阶段 5 用词相同）。

- [ ] **Step 5: 提交**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/test-skill/references/
git -C /root/workspace/agent-toolkit commit -m "feat(test-skill): 新增判定标准、报告模板与剧本模板"
```

---

### Task 4: README + metadata + 仓库一致性

**Files:**
- Create: `resources/skills/test-skill/README.md`
- Create: `resources/skills/test-skill/metadata.yaml`

**Interfaces:**
- Consumes: `docs/conventions.md` 的 skill 资源约定与 metadata 字段表。
- Produces: 完整合规的资源目录，Task 7 发布的前提。

- [ ] **Step 1: README.md**

内容：一段话定位（盲测复盘，五工序链之外的横向质检工序）；输入/输出；一次测试是完整多轮 agent 会话的成本提示；目录内文件导览（SKILL.md、三个 references、docs 内设计/计划/假设实测记录）。

- [ ] **Step 2: metadata.yaml**

```yaml
id: test-skill
name: Test Skill
type: skill
description: 对目标 skill 发起 headless 盲测跑，逐步骤溯源并产出中文复盘报告
tags: [skill-quality, testing, replay]
status: draft
created_at: 2026-07-02
updated_at: 2026-07-02
```

- [ ] **Step 3: 一致性核对**

对照 `docs/conventions.md`：目录名 = id；必备文件齐全（README.md、SKILL.md、metadata.yaml）；README 与 metadata description 表意一致。

- [ ] **Step 4: 提交**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/test-skill/README.md resources/skills/test-skill/metadata.yaml
git -C /root/workspace/agent-toolkit commit -m "chore(test-skill): 补齐 README 与 metadata"
```

---

### Task 5: 玩具 skill 端到端跑 + 反事实判定一致性

**Files:**
- 全部产物在 scratchpad（玩具 skill、沙箱、报告），不入库
- Modify（仅当发现缺陷）: `resources/skills/test-skill/SKILL.md` 及 references

**Interfaces:**
- Consumes: Task 2-4 交付的完整 test-skill。
- Produces: 全流程可行性结论 + 判定一致性结论；对 SKILL.md/references 的修正提交。

- [ ] **Step 1: 造玩具 skill**

`<scratchpad>/probe-guarded/SKILL.md`：

```markdown
---
name: probe-guarded
description: 当用户要求用 probe-guarded 整理文件清单时使用
---

# probe-guarded

1. 开始任何操作前，必须先向用户提出至少一个澄清问题并等待回答。
2. 只允许在当前目录创建一个名为 inventory.md 的文件，不得创建其他文件。
3. inventory.md 第一行必须是【probe-guarded v1】。
4. 列出当前目录全部文件时必须使用无序列表。
5. 完成后必须向用户复述你创建了什么文件。
6. 全程使用中文。
```

剧本关键设定：模拟用户首轮就说"不要问我任何问题，直接做"——与指令 1 制造冲突，大概率产生"被违反"样本。

- [ ] **Step 2: 按 test-skill 全流程执行**

编排者严格按 `resources/skills/test-skill/SKILL.md` 从阶段 0 走到阶段 6（目标 skill 输入形式：SKILL.md 路径；报告落沙箱内 `skill-test-reports/`——验证第三方分支的存放规则）。

- [ ] **Step 3: 反事实核对**

人工读 transcript，对玩具 skill 6 条指令逐条得出人工判定，与报告判定对比。通过标准：6 条全部一致（特别是指令 1 的冲突判定）；不一致 → 定位是判定标准缺陷还是 SKILL.md 指令缺陷，修正后重跑本任务 Step 2-3。

- [ ] **Step 4: 提交修正（如有）**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/test-skill/
git -C /root/workspace/agent-toolkit commit -m "fix(test-skill): 玩具 skill 端到端跑暴露的流程/判定修正"
```

（无修正则本任务无提交。）

---

### Task 6: refine-idea 真实冒烟

**Files:**
- Create: `resources/skills/refine-idea/docs/test-report-2026-07-02.md`（test-skill 按存放规则自动落此处）
- Modify（仅当发现缺陷）: `resources/skills/test-skill/` 下文件

**Interfaces:**
- Consumes: Task 5 验证过的 test-skill 全流程。
- Produces: 首份真实复盘报告；test-skill 通过设计文档第 10 节全部验收。

- [ ] **Step 1: 设计场景与剧本**

场景：模拟用户说"我想要一个实验管理 dashboard"，隐藏痛点是"其实连一份实验清单都没有"（取自 refine-idea 自身文档中的典型偏差案例，正好检验其意图挖掘指令是否起作用）。剧本按 persona-template 生成，交用户确认成本后开跑。

- [ ] **Step 2: 全流程执行**

目标 skill 输入形式：仓库 id `refine-idea`。交互式多轮，预计 5-8 轮。

- [ ] **Step 3: 报告质量三查**

① 溯源表每步都有判定；② refine-idea 指令清单每条都有状态；③ 修改建议可直接落为对 refine-idea SKILL.md 的编辑动作。任何一查不过 → 修正 test-skill 后重跑。

- [ ] **Step 4: 提交**

```bash
git -C /root/workspace/agent-toolkit add resources/skills/refine-idea/docs/test-report-2026-07-02.md resources/skills/test-skill/
git -C /root/workspace/agent-toolkit commit -m "feat(test-skill): refine-idea 真实冒烟通过，产出首份复盘报告"
```

---

### Task 7: 发布（经用户确认后执行）

**Files:**
- Modify: `.claude-plugin/plugin.json`（skills 数组增补 test-skill 路径；version minor 递增）
- Modify: `.claude-plugin/marketplace.json`（版本与 plugin.json 同步）
- Modify: `resources/skills/test-skill/metadata.yaml`（status: draft → active；updated_at 更新为发布日）

**Interfaces:**
- Consumes: Task 6 验收通过的完整资源目录；仓库发布惯例（双清单版本同步）。
- Produces: 可通过插件市场安装的 test-skill。

- [ ] **Step 1: 更新双清单与 metadata**

按现有条目格式在 plugin.json skills 数组追加；两清单 version 同步递增 minor。

- [ ] **Step 2: 校验**

```bash
cd /root/workspace/agent-toolkit && claude plugin validate . --strict
```

预期：校验通过，无 error。

- [ ] **Step 3: 提交**

```bash
git -C /root/workspace/agent-toolkit add .claude-plugin/ resources/skills/test-skill/metadata.yaml
git -C /root/workspace/agent-toolkit commit -m "release(test-skill): 随插件发布 test-skill 并同步双清单版本"
```

---

## 计划自审记录

- **Spec 覆盖**：设计文档第 4 节（形态接口）→ Task 2/4；5.1-5.4（架构各件）→ Task 2 锚点 4-18；第 6 节（溯源）→ Task 2 锚点 19-22 + Task 3；第 7 节（错误边界）→ Task 2 锚点 1/17/18/22 + 红线节；第 8 节（技术假设）→ Task 1；第 9 节（报告）→ Task 2 锚点 23-25 + Task 3；第 10 节（验收）→ Task 5（反事实）/ Task 6（冒烟+三查）。无缺口。
- **占位符扫描**：无 TBD/待定；Task 2 以 25 条锚点 + Task 1 命令终稿约束正文展开，无"适当处理"类模糊步骤。
- **一致性**：references 三文件名在 Task 2 锚点与 Task 3 Files 中逐字一致；命令模板统一以 Task 1 终稿为准；判定术语（依据/偏离/无依据；已遵守/被违反/被跳过/未触发）全计划统一。
