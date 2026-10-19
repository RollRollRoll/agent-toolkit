---
name: test-skill
description: Blind-test a target skill in an isolated sandbox, collect evidence through headless runs, and produce a step-by-step traceable retrospective report in Chinese.
---

# Test Skill: blind-test retrospective for a skill

## Goal

Drive one multi-turn headless session in an isolated sandbox. The process under test sees only a natural user task and does not know it is being tested. After the run, align each semantic step with the instructions in the target `SKILL.md`, item by item, and produce a verifiable report. Write the report in Chinese.

First choose the Claude Code or Codex runner according to [platform-runners.md](references/platform-runners.md),
then use that same runner for every turn of this blind test. Do not assemble `claude -p` or `codex exec` yourself; the runner handles timeouts, session IDs, per-turn state, JSONL, stderr, argument passing, and the unique report path.

## Process

```text
Phase 0  Locate and preflight the CLI
Phase 1  Create isolated directories and inventory the instructions
Phase 2  Lay down fixtures and inject the target skill
Phase 3  Write the script and get cost confirmation
Phase 4  Drive the blind-test session
Phase 5  Rebuild the timeline and judge both sides
Phase 6  Write the persistent report
```

### Phase 0 · Locate and preflight the CLI

1. Locate the target `SKILL.md`. Accept a repo id, a file path, or an installed skill name. If there are multiple candidates, ask the user to pick one; do not guess.
2. Record three absolute paths: this skill's directory, the project directory the test was started from, and the session scratchpad. Use absolute paths directly in every later tool call; do not rely on shell variables, the current directory, or state from a previous Bash call.
3. Read [platform-runners.md](references/platform-runners.md) in full and choose the runner for the platform the user specified. If the user did not specify one,
   decide from the current host and where the target is installed; ask only if you still cannot tell. Run only that platform's `doctor` preflight, and make no model calls. If the preflight fails, stop. Do not switch to the other platform, and do not drop isolation flags to run in a degraded mode.

### Phase 1 · Create isolated directories and inventory the instructions

4. Under the scratchpad, plan two sibling directories that do not exist yet: the test sandbox `<run-name>/` and the orchestration directory `<run-name>-run/`.
   The persistent report directory is always `skill-test-reports/<target-id>/` under the project the test was started from. Never put it inside the target skill's own directory.
5. Initialize the run with the matching command from [platform-runners.md](references/platform-runners.md). Use absolute paths everywhere,
   and pick the minimum permissions or sandbox setting the scenario needs. `init` must succeed first; it creates the sandbox and orchestration directory and writes `run-config.json` with `platform` or the platform config.
   Then the orchestrator runs `git init` in the sandbox; initializing the repo does not need to be handed to the process under test.
6. Read the target `SKILL.md` in full. Split independently judgeable behavior requirements into R1..Rn, and pure background and examples into B1..Bm. "Do not use for" limits in the frontmatter are also instructions.
   Write the inventory to `checklist.md` in the orchestration directory, recording each item's original text, section, and applicability condition.

### Phase 2 · Lay down fixtures and inject the target skill

7. Lay down scenario fixtures only in the sandbox. Fixtures and file names must not reveal the testing intent.
8. Inject a full copy of the target skill for the platform: Claude Code uses `sandbox/.claude/skills/<target-id>/`,
   Codex uses `sandbox/.agents/skills/<target-id>/`. The platform directory may contain only this controlled copy and any empty project config that is strictly necessary; do not copy the original project's settings, plugins, hooks,
   rules, or MCP config. For Codex, the first natural-language task explicitly uses `$<target-id>`; for Claude Code, name the target skill naturally.
9. Orchestration artifacts go only in the sibling orchestration directory, never in the sandbox. The cwd of the process under test is always the sandbox.

### Phase 3 · Write the script and get cost confirmation

10. Generate `orchestration-dir/persona.md` following [persona-template.md](references/persona-template.md). Keep the existing hidden-pain-point model; do not add more persona dimensions.
11. Present to the user the scenario, the key points of the script, the expected number of turns, and the actual tool boundaries and cost range from `run-config.json`. Run `start` only after explicit confirmation; the cost confirmation gate cannot be skipped.
12. Write the first natural-language task to `orchestration-dir/turn-001.txt`. No prompt the process under test receives may contain wording such as "test, evaluate, retrospective, check you" (测试、评估、复盘、检查你); naming the target skill naturally is allowed.

### Phase 4 · Drive the blind-test session

13. For the first turn, run only the runner chosen for this run: `start --run-dir <orchestration-dir absolute path> --prompt-file <orchestration-dir absolute path>/turn-001.txt`.
    See [platform-runners.md](references/platform-runners.md) for the full command.

    The runner writes the transcript, stderr, `session-id`, and per-turn byte ranges to the orchestration directory, not the sandbox.

14. Parse the transcript added in this turn. If the output is waiting for user input, write a reply according to the script into the next `turn-NNN.txt`,
    then run `resume --run-dir <orchestration-dir absolute path> --prompt-file <orchestration-dir absolute path>/turn-NNN.txt` with the same runner.

    The runner resumes the session from `session-id` itself; do not keep a `SID` in the shell.
    You may improvise in persona for questions the script does not cover, but you must append them to the appendix of `persona.md`.

15. Stop when any of these happens: the process under test wraps up; `max_turns` is reached; a single turn times out; a CLI, permission, or session check fails. After a failure, do not continue in or overwrite records in the same run directory; keep the sample for analysis. If a rerun is truly needed,
    create a brand-new sandbox and orchestration directory and get cost confirmation again.
16. When you need reliable state, run `status --run-dir <orchestration-dir absolute path>`. Treat `run-state.json` as authoritative; do not infer state from shell variables.

### Phase 5 · Rebuild the timeline and judge both sides

17. Read [judging-criteria.md](references/judging-criteria.md) first, then parse `transcript-run.jsonl` in the orchestration directory.
    When you hit an unknown event type or a corrupt line, record it and skip it; do not let it abort the whole analysis.
18. Check that the skill name and source actually triggered in the transcript are the copy injected into the sandbox. If not, or if the source cannot be confirmed and that would affect the conclusion, mark the result invalid or doubtful; do not pass it off as a valid blind test.
19. Judge both sides: each semantic step gets one of three labels, `依据 Rx` (based on Rx), `偏离 Rx` (deviates from Rx), or `无依据` (no basis); each instruction gets one of four labels, `已遵守` (followed), `被违反` (violated), `被跳过` (skipped), or `未触发` (not triggered). Use the Chinese labels in the report.
20. If the transcript is longer than about 200k characters, split it by conversation turn across subagents. Give every chunk the full checklist and the judging criteria, then reconcile the results into one consistent standard at the end.

### Phase 6 · Write the persistent report

21. Write the six-section report in Chinese following [report-template.md](references/report-template.md).
    First run `report-path --run-dir <orchestration-dir absolute path>` with the same runner to atomically reserve a unique file name.

    Write the report to the path the command returns; calling it again returns the same path. Multiple runs on the same day are distinguished by time and `run_id`; never overwrite an old report.

22. Raw evidence paths in the report must point to `transcript-run.jsonl`, `stderr.log`, `run-state.json`,
    `checklist.md`, and `persona.md` in the orchestration directory, not the sandbox. Remind the user that the scratchpad gets cleaned up and they should copy the raw evidence if they need to keep it long term.

## Fail-closed boundaries

- The two platforms have different permission models. Follow the matching boundaries in [platform-runners.md](references/platform-runners.md) in full.
  Do not apply Claude Code's tool allowlist semantics to Codex, and do not apply Codex sandbox semantics to Claude Code.
- `--dangerously-skip-permissions` and `--dangerously-bypass-approvals-and-sandbox` are forbidden.
  Running a headless CLI directly without the runner is forbidden, and so is dropping isolation flags for compatibility with an old CLI.
- System or organization managed policies may still apply. If you find hooks, plugins, MCP, skills, or permissions from them affecting the run, record it in the report. If the actual load source cannot be confirmed and that would affect the conclusion, mark the result invalid or doubtful.

## Red lines

- **Blind**: no input to the process under test may reveal the testing intent.
- **Zero intrusion**: do not modify the target skill's own directory; the persistent report may only be written to the separate `skill-test-reports/`.
- **Isolation**: the checklist, persona, transcript, stderr, and state files must not enter the sandbox.
- **Cost confirmation**: do not run `start` or any real headless turn before the user confirms.
