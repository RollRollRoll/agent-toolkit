# 平台 Runner 选择与隔离边界

一次盲测只使用一个平台。用户明确指定 Claude Code 或 Codex 时服从；未指定时，以当前宿主、目标 Skill 的安装来源和可执行 CLI 判断，仍无法确定才询问。某平台预检或运行失败后保留证据并停止，不静默切换另一平台。

## Claude Code

Runner：`scripts/run-headless.py`。

### 预检与初始化

```bash
python3 <skill目录>/scripts/run-headless.py doctor --claude claude

python3 <skill目录>/scripts/run-headless.py init \
  --sandbox <沙箱绝对路径> \
  --run-dir <编排目录绝对路径> \
  --report-dir <项目绝对路径>/skill-test-reports/<被测-id> \
  --skill-name <被测-id> \
  --tools "Skill,Read,Write,Edit,Glob,Grep" \
  --allowed-tools "Skill(<被测-id>),Read(/**),Write(/**),Edit(/**)" \
  --timeout 600 --max-turns 10
```

初始化成功后在沙箱执行 `git init`，再把目标 Skill 完整复制到 `沙箱/.claude/skills/<被测-id>/`。

被测场景确实需要 Bash 时才把它加入 `--tools`，并显式列出逐条只读命令规则；禁止 `Bash`、`Bash(*)`、`Bash(git:*)` 等宽规则。

### 驱动与报告

```bash
python3 <skill目录>/scripts/run-headless.py start --run-dir <编排目录> --prompt-file <首轮文件>
python3 <skill目录>/scripts/run-headless.py resume --run-dir <编排目录> --prompt-file <续轮文件>
python3 <skill目录>/scripts/run-headless.py report-path --run-dir <编排目录>
```

### Fail-closed

- `--tools` 限制内建工具，`--allowedTools` 只免除权限提示；两者不可混为一谈。
- 固定使用 `--permission-mode dontAsk`，未预授权动作直接拒绝。
- MCP 用 `--strict-mcp-config` 与空配置隔离，设置源只保留受控 project 层。
- Bash 开启时强制 Claude Code OS sandbox，禁止 unsandboxed fallback。
- 禁止 `--dangerously-skip-permissions`。

## Codex

Runner：`scripts/run-codex-headless.py`。

### 预检与初始化

```bash
python3 <skill目录>/scripts/run-codex-headless.py doctor --codex codex

python3 <skill目录>/scripts/run-codex-headless.py init \
  --sandbox <沙箱绝对路径> \
  --run-dir <编排目录绝对路径> \
  --report-dir <项目绝对路径>/skill-test-reports/<被测-id> \
  --skill-name <被测-id> \
  --sandbox-mode workspace-write \
  --timeout 600 --max-turns 10
```

只读场景改用 `--sandbox-mode read-only`。禁止 `danger-full-access`。初始化成功后在沙箱执行 `git init`，再把目标 Skill 完整复制到 `沙箱/.agents/skills/<被测-id>/`；首轮自然语言任务显式写 `$<被测-id>`。

### 驱动与报告

```bash
python3 <skill目录>/scripts/run-codex-headless.py start --run-dir <编排目录> --prompt-file <首轮文件>
python3 <skill目录>/scripts/run-codex-headless.py resume --run-dir <编排目录> --prompt-file <续轮文件>
python3 <skill目录>/scripts/run-codex-headless.py report-path --run-dir <编排目录>
```

### Fail-closed

- runner 只允许 `read-only` 或 `workspace-write` sandbox，并固定 `approval_policy=never`；越出 sandbox 的动作失败，不进入交互审批。
- runner 使用隔离 HOME 隐藏用户级 `.agents/skills`，同时显式保留原 `CODEX_HOME` 只供 CLI 身份使用。
- 固定使用 `--ignore-user-config`、`--ignore-rules`、`--strict-config` 并关闭 web search；沙箱内不得复制 `.codex/`、hooks、rules、插件或 MCP 配置。
- Codex 没有 Claude Code 的 `--tools/--allowedTools` 等价白名单。报告必须如实记录 sandbox 只能约束文件、命令和网络边界，不能伪称已按工具名精确白名单化。
- 系统或组织托管配置仍可能生效；发现额外 Skill、hook、MCP 或权限影响时标注证据缺口。
- 禁止 `--dangerously-bypass-approvals-and-sandbox`。
