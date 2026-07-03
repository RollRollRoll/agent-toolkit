# headless 驱动技术假设实测记录

- 日期：2026-07-02
- 环境：claude CLI 2.1.198（Claude Code），Linux/WSL2
- 依据：设计文档第 8 节的 4 条假设；实验沙箱为会话 scratchpad 下 `assumption-probe/`
- 结论总览：**4 条全部 PASS**，计划中的命令模板终稿无需修正

## 假设 1：stream-json 是否需要 `--verbose` —— PASS（必须带）

```bash
claude -p "只回答数字：1+1=?" --output-format stream-json --verbose --model haiku   # 退出码 0
claude -p "只回答数字：2+2=?" --output-format stream-json --model haiku             # 退出码 1
```

- 不带 `--verbose` 直接报错：`Error: When using --print, --output-format=stream-json requires --verbose`，无任何输出。
- 带 `--verbose` 输出完整事件流，实测事件序列：多个 `system`（init 与 hooks 等）→ `assistant` → `rate_limit_event` → `result`。
- **影响**：命令模板必须含 `--verbose`（计划初稿已含）。

## 假设 2：`--resume` headless 多轮续跑 —— PASS

```bash
SID=$(python3 -c "...first event with session_id...")   # 首轮取 session_id
claude -p --resume "$SID" "我上一条消息问的算术题是什么？" --output-format stream-json --verbose --model haiku
```

- 第二轮正确回答"1+1=?"，上下文延续成立。
- **第二轮 session_id 与首轮相同**（`144b4906-…` 不变）→ 驱动循环全程沿用首轮 session_id，无需逐轮重取。
- **影响**：无需启用退路（`--session-id` 固定 / 方案 A）。

## 假设 3：沙箱项目级 skill 加载与同名遮蔽 —— PASS

- 沙箱 `.claude/skills/probe-echo/SKILL.md`（指令：回复第一行输出【PROBE-OK】），headless 显式点名调用 → 输出含【PROBE-OK】：**项目级 skill 在 headless 下被加载执行**。
- 沙箱注入与已安装插件同名的 `write-spec` 探针副本（指令：回复第一行输出【LOCAL-WIN】），显式点名调用 → 输出含【LOCAL-WIN】：**项目级版本胜出，遮蔽插件版**。
- **影响**：注入被测 skill 直接用原名，无需 `<id>-under-test` 副本名；测试任务 prompt 点名原名即可。

## 假设 4：thinking 块可获得性 —— PASS

- 默认模型（会话模型）跑推理型 prompt，assistant 事件 content 块集合为 `['text', 'thinking']`。
- **影响**：溯源分析可使用 thinking 辅助意图判断；judging-criteria 不需要收紧意图推断的置信度表述（但"判定依据不足标存疑"的通用规则保留）。

## 附加观察

- 事件流中带 `session_id` 的事件很多（system/assistant/result 均有），取"第一个带 session_id 的事件"即可，无需依赖特定 subtype。
- 事件流含 `rate_limit_event`，解析器应忽略未知事件类型而不是报错。
- 每次 Bash 调用后 shell cwd 会被重置，驱动循环的每条命令都要显式 `cd` 沙箱。

## 命令模板终稿（Task 2 SKILL.md 逐字采用）

```bash
# 首轮（cwd = 测试沙箱）
timeout 600 claude -p "$FIRST_PROMPT" \
  --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Bash(git:*)" \
  >> transcript-run.jsonl 2>> stderr.log

# session_id 提取（首轮后执行一次，全程沿用）
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
