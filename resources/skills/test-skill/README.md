# test-skill

在隔离沙箱中发起一次 headless 盲测，把被测 agent 的语义步骤逐一溯源到目标 skill 指令，并产出中文复盘报告。

它不属于 refine-idea → write-spec → make-design → split-task → execute-task 主链，而是横向质检工序。

## 输入与输出

- **输入**：目标 skill（仓库 id、`SKILL.md` 路径或已安装名称）与可选场景。
- **运行证据**：位于 scratchpad 的同级编排目录，包括 checklist、persona、逐轮 prompt、JSONL、stderr、会话 ID 与状态文件。
- **持久输出**：发起测试项目下 `skill-test-reports/<被测-id>/test-report-<时间>-<run-id>.md`。报告不写入目标 skill 原目录，也不会覆盖同日报告。

一次测试是完整的多轮 agent 会话，默认最多 10 轮。真实 headless 运行前必须向用户展示场景、工具边界和成本并取得确认。

## 执行边界

- `scripts/run-headless.py` 是唯一 headless 入口，使用 Python 标准库实现跨平台超时与可靠参数传递。
- `--tools` 限制内建工具，`--allowedTools` 仅做限定到沙箱项目的精确预授权；`dontAsk` 拒绝其他动作。Bash 默认关闭，启用时必须逐条声明只读命令、强制 OS sandbox 并禁止 unsandboxed fallback，禁止宽泛 `git:*`。
- MCP 使用 strict + 空配置隔离；设置来源只保留受控沙箱的 project 层。
- runner 不依赖可能不完整的 `claude --help` 误判能力；真实调用始终带齐隔离参数，CLI 不支持时 fail closed，不降级，不使用 `--dangerously-skip-permissions`。
- 单轮失败后保留现场并停止；需要重跑时使用全新的沙箱和编排目录。

## 文件导览

- `SKILL.md`：六阶段盲测流程与 fail-closed 红线。
- `scripts/run-headless.py`：目录初始化、CLI 预检、首轮/续轮、超时、状态和唯一报告路径。
- `scripts/tests/test_run_headless.py`：使用 fake CLI 的无真实模型回归测试。
- `references/judging-criteria.md`：步骤判定和指令状态的唯一口径。
- `references/report-template.md`：六节复盘报告模板。
- `references/persona-template.md`：模拟用户剧本模板。
- `docs/`：早期设计与假设验证记录；其中命令样例仅作历史证据，现行执行契约以 `SKILL.md` 和 runner 为准。
