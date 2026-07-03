---
name: test-skill
description: 当用户想测试/复盘某个 skill 的实际执行效果时使用——如"测一下这个 skill、复盘 skill 执行、看看 agent 是不是按 skill 写的做的、skill 覆盖率/溯源报告"。对目标 skill 发起一次 headless 盲测跑并产出逐步骤溯源的中文复盘报告。不要用于：写新 skill（用 writing-skills 类流程）、调试业务代码、code review、对"当前会话里已发生的执行"做复盘（本 skill 只做主动测试跑）。
---

# Test Skill — skill 盲测复盘

## 你的任务

对一个目标 skill 发起一次**盲测跑**：在隔离沙箱里用 headless `claude -p` 进程执行它（被测进程不知道自己在被测试），你按剧本扮演用户与它多轮对话；跑完后逐步骤溯源——agent 的每个动作依据 skill 哪条指令、哪些指令被违反或跳过——最终产出一份中文复盘报告，回答"这个 skill 写得好不好、哪里要改"。

你在整个流程中身兼四职：**编排者**（搭环境、驱动进程）、**模拟用户**（照剧本回答）、**分析者**（事后溯源）、**报告作者**。

## 为什么必须盲测

执行者若知道自己被检查，会比平时更严格地遵守 skill，测出来的是"监考下的表现"而非平时表现，复盘结论会系统性偏乐观。因此：**被测进程收到的一切输入（任务、每轮回复、fixture 文件内容）一律不得出现"测试 / 评估 / 复盘 / 检查你"等透露测试意图的表述。**

盲测不等于隐藏 skill 名——正常用户本来就会显式点名 skill（"用 refine-idea 帮我理一理……"），首轮任务就应自然地点名它。

## 流程总览

```text
阶段 0  预检与输入确认（CLI 可用？目标 skill 在哪？场景有了吗？）
阶段 1  指令清单化（SKILL.md → 编号指令 R1..Rn + 背景条目）
阶段 2  沙箱搭建（scratchpad 独立目录 + fixture + 注入被测 skill）
阶段 3  剧本与开跑确认（隐藏痛点剧本 + 成本确认门）
阶段 4  盲测驱动循环（claude -p 首轮 → 照剧本回复 → --resume 续轮 → 停止条件）
阶段 5  溯源分析（步骤时间线 ←对齐→ 指令清单，双侧判定）
阶段 6  复盘报告（六节中文报告，落到约定位置）
```

## 阶段 0：预检与输入确认

1. 运行 `claude --version` 确认 CLI 可用。失败即停，告知用户当前环境无法做 headless 测试。
2. 定位目标 skill 的 SKILL.md，支持三种输入形式：
   - **仓库 id**：`resources/skills/<id>/SKILL.md`；
   - **SKILL.md 路径**：直接使用；
   - **已安装 skill 名**：在插件缓存（如 `~/.claude/plugins/cache/`）中查找。
   定位失败时列出你找到的相近候选请用户指认，不要自行猜测。
3. 用户未提供测试场景时，依据目标 skill 的 description 设计一个典型适用场景；场景在阶段 3 连同剧本一起交用户确认。

## 阶段 1：指令清单化

4. 通读目标 SKILL.md 全文（含 frontmatter），拆出编号指令清单 R1..Rn。**一条指令 = 一个可独立判定"遵守与否"的行为要求**；一个章节常拆出多条。
5. 纯背景、动机阐述、举例段落不算指令，记为背景条目 B1..Bm——不参与覆盖统计，诊断环节引用。
6. frontmatter description 中"何时不用"的限定同样拆入指令清单（执行中依然可判定）。
7. 清单写入沙箱 `checklist.md`，每条包含：编号、原文摘录、所在章节、**适用条件**（什么情况下该条才适用——阶段 5 区分"被跳过"与"未触发"全靠它）。

## 阶段 2：沙箱搭建

8. 在会话 scratchpad 下创建独立目录并 `git init`，它就是被测进程的工作目录（cwd）。
9. 按场景铺设 fixture（被测 skill 需要的既有文档、代码等）。fixture 内容同样遵守盲测红线。
10. 注入被测 skill：把目标 skill 目录完整复制到 `沙箱/.claude/skills/<原名>/`。已实测（见 `docs/2026-07-02-assumption-test-notes.md`）：headless 下项目级 skill 会被加载，且同名时**项目级遮蔽已安装插件版**——直接用原名注入，保证测到的是你手里的版本而非已发布旧版。

## 阶段 3：剧本与开跑确认

11. 按 `references/persona-template.md` 生成模拟用户剧本，必含：身份背景、真实意图、**隐藏痛点**（首轮绝不说出，考验 skill 的意图挖掘指令）、常见问题答案素材、回答风格、不透露边界。
12. 向用户呈现：场景、剧本要点、预计轮数、成本量级（一次测试是完整多轮 agent 会话，token 消耗可观），**取得确认后才开跑**。用户可以跳过剧本细节审阅，但成本确认门不可跳过。

## 阶段 4：盲测驱动循环

13. 命令逐字使用以下模板（来自 `docs/2026-07-02-assumption-test-notes.md` 实测终稿），cwd 必须是沙箱；`--allowedTools` 白名单默认如下，按被测 skill 实际需要增补，并在报告概要中记录最终白名单：

```bash
# 首轮（cwd = 测试沙箱）
timeout 600 claude -p "$FIRST_PROMPT" \
  --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Bash(git:*)" \
  >> transcript-run.jsonl 2>> stderr.log

# session_id 提取（首轮后执行一次，全程沿用；--resume 不改变 session_id，已实测）
SID=$(python3 -c "
import json
for line in open('transcript-run.jsonl'):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    if d.get('session_id'): print(d['session_id']); break
")

# 续轮（每轮一次，沿用同一 SID）
timeout 600 claude -p --resume "$SID" "$SIMULATED_USER_REPLY" \
  --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Bash(git:*)" \
  >> transcript-run.jsonl 2>> stderr.log
```

14. 首轮 prompt = 普通用户口吻 + 显式点名被测 skill 原名 + 场景任务。例："用 refine-idea 帮我理一理：我想要一个实验管理 dashboard。"
15. 每轮结束后解析 transcript 新增部分，判断被测进程最后的输出属于哪类：
    - **在提问 / 等待用户输入** → 按剧本生成回复，发起续轮；
    - **收尾陈述**（总结产出、无待答问题）→ 停止循环。
16. 剧本未覆盖的问题按人设合理即兴，即兴问答**追记进剧本附录**——复盘时"用户说过什么"必须全部有据可查。
17. 停止条件（满足其一即停）：收尾判定；轮数上限（默认 10，可在开跑确认时调整）；单轮 `timeout 600` 秒。
18. 被测进程报错或权限拒绝：同一轮最多重试 1 次；仍失败则停止驱动，带着已有 transcript 进入阶段 5——失败样本也是复盘素材（权限拒绝反映该 skill 的隐含权限需求，写进报告）。

## 阶段 5：溯源分析

19. 解析 `transcript-run.jsonl`（逐行 JSON；遇到未知事件类型跳过而非报错），重建**语义步骤时间线**。判定口径唯一依据 `references/judging-criteria.md`，动手前先读它。
20. 双侧判定：每个步骤三选一——`依据 Rx` / `偏离 Rx` / `无依据`；每条指令四选一——`已遵守` / `被违反` / `被跳过` / `未触发`。
21. transcript 超过约 200k 字符时：按对话轮切分，spawn 子 agent 分段分析（每段都附上 `checklist.md` 与判定标准全文），你负责汇总并统一判定口径。
22. 若被测进程从未触发目标 skill：跳过步骤溯源，直接进阶段 6，报告主体改写"触发失败"发现——显式点名仍未触发，通常指向 description 措辞或加载配置问题。

## 阶段 6：复盘报告

23. 按 `references/report-template.md` 撰写中文报告，六节齐全（测试概要 / 步骤溯源表 / 指令覆盖统计 / 设计诊断 / 修改建议 / 附录）。
24. 存放规则：目标 skill 属于当前 git 仓库 → `resources/skills/<被测id>/docs/test-report-YYYY-MM-DD.md`；否则 → 当前工作目录 `skill-test-reports/`。
25. 报告末尾提醒：沙箱位于会话级临时目录，原始 transcript 如需长期留存请自行拷贝（附上沙箱路径）。

## 红线（任何阶段不得违反）

- **盲测红线**：被测进程的一切输入不得透露测试意图。
- **权限红线**：只用 `--permission-mode acceptEdits` + `--allowedTools` 白名单，禁止 `--dangerously-skip-permissions`。
- **零侵入**：不得修改被测 skill 原目录的任何文件。
- **成本确认门**（阶段 3 第 12 条）不可跳过。
