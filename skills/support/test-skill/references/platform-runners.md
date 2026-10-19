# Platform runner choice and isolation boundaries

One blind test uses only one platform. When the user explicitly names Claude Code or Codex, follow that. When they do not, decide from the current host, where the target skill is installed, and which CLI is executable; ask only if you still cannot tell.
If a platform's preflight or run fails, keep the evidence and stop. Do not silently switch to the other platform.

## Claude Code

Runner: `scripts/run-headless.py`.

### Preflight and init

```bash
python3 <skill dir>/scripts/run-headless.py doctor --claude claude

python3 <skill dir>/scripts/run-headless.py init \
  --sandbox <sandbox absolute path> \
  --run-dir <orchestration dir absolute path> \
  --report-dir <project absolute path>/skill-test-reports/<target-id> \
  --skill-name <target-id> \
  --tools "Skill,Read,Write,Edit,Glob,Grep" \
  --allowed-tools "Skill(<target-id>),Read(/**),Write(/**),Edit(/**)" \
  --timeout 600 --max-turns 10
```

After init succeeds, run `git init` in the sandbox, then copy the full target skill to `sandbox/.claude/skills/<target-id>/`.

Add Bash to `--tools` only when the scenario under test really needs it, and list explicit per-command read-only rules. Broad rules such as `Bash`, `Bash(*)`, and `Bash(git:*)` are forbidden.

### Driving and report

```bash
python3 <skill dir>/scripts/run-headless.py start --run-dir <orchestration dir> --prompt-file <first-turn file>
python3 <skill dir>/scripts/run-headless.py resume --run-dir <orchestration dir> --prompt-file <next-turn file>
python3 <skill dir>/scripts/run-headless.py report-path --run-dir <orchestration dir>
```

### Fail-closed

- `--tools` restricts built-in tools; `--allowedTools` only skips permission prompts. Do not confuse the two.
- Always use `--permission-mode dontAsk`, so actions that were not pre-authorized are refused outright.
- Isolate MCP with `--strict-mcp-config` and an empty config, and keep only the controlled project layer as a settings source.
- When Bash is enabled, force the Claude Code OS sandbox and forbid the unsandboxed fallback.
- `--dangerously-skip-permissions` is forbidden.

## Codex

Runner: `scripts/run-codex-headless.py`.

### Preflight and init

```bash
python3 <skill dir>/scripts/run-codex-headless.py doctor --codex codex

python3 <skill dir>/scripts/run-codex-headless.py init \
  --sandbox <sandbox absolute path> \
  --run-dir <orchestration dir absolute path> \
  --report-dir <project absolute path>/skill-test-reports/<target-id> \
  --skill-name <target-id> \
  --sandbox-mode workspace-write \
  --timeout 600 --max-turns 10
```

For read-only scenarios use `--sandbox-mode read-only` instead. `danger-full-access` is forbidden. After init succeeds, run `git init` in the sandbox,
then copy the full target skill to `sandbox/.agents/skills/<target-id>/`. The first natural-language task explicitly writes `$<target-id>`.

### Driving and report

```bash
python3 <skill dir>/scripts/run-codex-headless.py start --run-dir <orchestration dir> --prompt-file <first-turn file>
python3 <skill dir>/scripts/run-codex-headless.py resume --run-dir <orchestration dir> --prompt-file <next-turn file>
python3 <skill dir>/scripts/run-codex-headless.py report-path --run-dir <orchestration dir>
```

### Fail-closed

- The runner allows only the `read-only` or `workspace-write` sandbox and fixes `approval_policy=never`. Actions outside the sandbox fail; they do not go to interactive approval.
- The runner uses an isolated HOME to hide user-level `.agents/skills`, while explicitly keeping the original `CODEX_HOME` only for CLI identity.
- Always use `--ignore-user-config`, `--ignore-rules`, `--strict-config`, and turn off web search. Do not copy `.codex/`,
  hooks, rules, plugins, or MCP config into the sandbox.
- Codex has no allowlist equivalent to Claude Code's `--tools/--allowedTools`. The report must state truthfully that the sandbox only constrains file, command, and network boundaries, and must not claim the run was allowlisted precisely by tool name.
- System or organization managed config may still apply. When you find extra skills, hooks, MCP, or permissions affecting the run, mark the evidence gap.
- `--dangerously-bypass-approvals-and-sandbox` is forbidden.
