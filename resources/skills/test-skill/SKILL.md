---
name: test-skill
description: 当用户想测试或复盘某个 skill 的实际执行效果时使用——如“测一下这个 skill”“看看 agent 是否按 skill 执行”“生成 skill 覆盖率或溯源报告”。在隔离沙箱中发起一次 headless 盲测，逐步骤溯源并产出中文复盘报告。不要用于编写新 skill、调试业务代码、代码审查，或复盘当前会话已经发生的执行。
---

# Test Skill — skill 盲测复盘

## 任务

在隔离沙箱中驱动一次多轮 headless 会话。被测进程只看到自然的用户任务，不知道自己正在被测试。运行结束后，把每个语义步骤与目标 `SKILL.md` 的指令逐项对齐，产出可复核的中文报告。

使用 `scripts/run-headless.py` 执行所有 headless 轮次。不要自行拼接 `claude -p` 命令；运行器负责跨平台超时、会话 ID、逐轮状态、JSONL、stderr、参数传递和唯一报告路径。

## 流程

```text
阶段 0  定位与 CLI 预检
阶段 1  创建隔离目录并清单化指令
阶段 2  铺设 fixture 与注入目标 skill
阶段 3  生成剧本并取得成本确认
阶段 4  驱动盲测会话
阶段 5  重建时间线并双侧判定
阶段 6  写入持久报告
```

### 阶段 0：定位与 CLI 预检

1. 定位目标 `SKILL.md`。支持仓库 id、文件路径和已安装 skill 名；存在多个候选时请用户指认，不要猜测。
2. 记下三个绝对路径：本 skill 目录、发起测试时的项目目录、会话 scratchpad。后续每次工具调用都直接使用绝对路径；不要依赖 shell 变量、当前目录或上一次 Bash 调用的状态。
3. 只做可执行文件与版本预检，不发起模型调用：

```bash
python3 <本-skill-绝对路径>/scripts/run-headless.py doctor --claude claude
```

预检失败即停。Claude Code 官方说明 `--help` 不保证列出全部参数，因此 runner 只把未列出的参数记入诊断，
不据此误判“不支持”；真正运行仍会带齐隔离参数，旧 CLI 解析失败时直接停止，不降级成宽松权限。

### 阶段 1：创建隔离目录并清单化指令

4. 在 scratchpad 下规划两个尚不存在的同级目录：测试沙箱 `<运行名>/` 与编排目录 `<运行名>-run/`。持久报告目录固定为发起测试项目下的 `skill-test-reports/<被测-id>/`，不得放进目标 skill 原目录。
5. 初始化运行。下面的路径均替换为绝对路径；默认只开放目标 skill 与沙箱项目内的文件工具，按场景做最小化增删：

```bash
python3 <本-skill-绝对路径>/scripts/run-headless.py init \
  --sandbox <沙箱绝对路径> \
  --run-dir <编排目录绝对路径> \
  --report-dir <发起测试项目绝对路径>/skill-test-reports/<被测-id> \
  --skill-name <被测-id> \
  --tools "Skill,Read,Write,Edit,Glob,Grep" \
  --allowed-tools "Skill(<被测-id>),Read(/**),Write(/**),Edit(/**)" \
  --timeout 600 --max-turns 10
```

`init` 必须先成功，它会创建沙箱和编排目录并写入 `run-config.json`。随后在沙箱执行 `git init`。
被测场景确实需要 Bash 时才把它加入 `--tools`，并显式列出逐条只读命令规则；禁止 `Bash`、
`Bash(*)`、`Bash(git:*)` 这类宽规则。此时 runner 会强制启用 Claude Code OS sandbox、限制读取编排/报告目录并禁止 unsandboxed fallback；平台缺少 sandbox 能力就 fail closed。初始化仓库由编排者在真实 headless 调用前完成，不需要把该权限交给被测进程。

6. 通读目标 `SKILL.md` 全文。把可独立判定的行为要求拆为 R1..Rn，把纯背景和示例拆为 B1..Bm；frontmatter 中“不适用”限制也属于指令。将清单写入编排目录 `checklist.md`，每条记录原文、章节和适用条件。

### 阶段 2：铺设 fixture 与注入目标 skill

7. 只在沙箱中铺设场景 fixture。fixture 和文件名不得透露测试意图。
8. 把目标 skill 的完整副本注入 `沙箱/.claude/skills/<被测-id>/`。沙箱 `.claude/` 中只允许出现这个受控副本和确有必要的空项目配置；不得复制原项目的 settings、插件或 MCP 配置。
9. 编排产物只能放在同级编排目录，不能放进沙箱。被测进程的 cwd 始终是沙箱。

### 阶段 3：生成剧本并取得成本确认

10. 按 [persona-template.md](references/persona-template.md) 生成 `编排目录/persona.md`。保留现有隐藏痛点模型，不额外扩展人设维度。
11. 向用户呈现场景、剧本要点、预计轮数，以及 `run-config.json` 中的实际工具边界和成本量级。取得明确确认后才执行 `start`；成本确认门不可跳过。
12. 将首轮自然语言任务写入 `编排目录/turn-001.txt`。被测进程收到的任何 prompt 都不得包含“测试、评估、复盘、检查你”等措辞；自然地点名目标 skill 是允许的。

### 阶段 4：驱动盲测会话

13. 首轮仅执行：

```bash
python3 <本-skill-绝对路径>/scripts/run-headless.py start \
  --run-dir <编排目录绝对路径> \
  --prompt-file <编排目录绝对路径>/turn-001.txt
```

运行器把 transcript、stderr、`session-id` 和逐轮字节范围写入编排目录，不写入沙箱。

14. 解析本轮新增 transcript。若输出在等待用户输入，按剧本生成回复，写入下一个 `turn-NNN.txt`，再执行：

```bash
python3 <本-skill-绝对路径>/scripts/run-headless.py resume \
  --run-dir <编排目录绝对路径> \
  --prompt-file <编排目录绝对路径>/turn-NNN.txt
```

运行器自行从 `session-id` 恢复会话，不要在 shell 中保存 `SID`。剧本未覆盖的问题可按人设即兴，但必须追记进 `persona.md` 附录。

15. 满足任一条件即停：被测进程收尾；达到 `max_turns`；单轮超时；CLI、权限或会话校验失败。失败后不得在同一运行目录继续或覆盖记录；保留样本进入分析。若确需重跑，创建全新的沙箱与编排目录，并重新取得成本确认。
16. 需要查看可靠状态时执行 `status --run-dir <编排目录绝对路径>`，以 `run-state.json` 为准，不从 shell 变量推断。

### 阶段 5：重建时间线并双侧判定

17. 先读 [judging-criteria.md](references/judging-criteria.md)，再解析编排目录的 `transcript-run.jsonl`。遇到未知事件类型或损坏行时记录并跳过，不得让整个分析中断。
18. 核对 transcript 中实际触发的 skill 名与来源是否为沙箱注入副本。若不是，或来源无法确认且会影响结论，把结果标为无效或存疑，不得伪装成有效盲测。
19. 双侧判定：每个语义步骤三选一——`依据 Rx`、`偏离 Rx`、`无依据`；每条指令四选一——`已遵守`、`被违反`、`被跳过`、`未触发`。
20. transcript 超过约 200k 字符时，按对话轮切分给子 agent；每段必须同时提供完整 checklist 和判定标准，最后统一口径。

### 阶段 6：写入持久报告

21. 按 [report-template.md](references/report-template.md) 写六节中文报告。先原子预留唯一文件名：

```bash
python3 <本-skill-绝对路径>/scripts/run-headless.py report-path \
  --run-dir <编排目录绝对路径>
```

把报告写入命令返回的路径；重复调用会返回同一路径。同日多次运行由时间与 `run_id` 区分，不得覆盖旧报告。

22. 报告中的原始证据路径必须指向编排目录的 `transcript-run.jsonl`、`stderr.log`、`run-state.json`、`checklist.md` 和 `persona.md`，不能指向沙箱。提醒用户 scratchpad 会被清理，如需长期留存应复制原始证据。

## Fail-closed 边界

- `--tools` 才限制内建工具可用性；`--allowedTools` 只免除权限提示，不是工具白名单。运行器同时使用精确 `--tools`、限定到沙箱项目的最小 `--allowedTools` 和 `--permission-mode dontAsk`，未预授权动作直接拒绝。Bash 默认不开放；启用时额外强制 OS sandbox，sandbox 不可用即失败。
- MCP 不受 `--tools` 限制。运行器固定使用 `--strict-mcp-config` 与空 `--mcp-config`。
- 运行器固定使用 `--setting-sources project`，以排除 user/local 设置并保留沙箱项目 skill。系统或组织托管策略仍可能生效，发现相关 hook、插件或权限影响时必须写入报告。
- 禁止 `--dangerously-skip-permissions`，禁止绕过 runner 直接运行 headless CLI，禁止为兼容旧 CLI 删除隔离参数。

## 红线

- **盲测**：被测进程的一切输入不得透露测试意图。
- **零侵入**：不得修改目标 skill 原目录；持久报告只能写入独立的 `skill-test-reports/`。
- **隔离**：checklist、persona、transcript、stderr、状态文件不得进入沙箱。
- **成本确认**：用户确认之前不得执行 `start` 或任何真实 headless 轮次。
