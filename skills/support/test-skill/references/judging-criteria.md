# Traceability judging criteria

This document is the only judging standard for test-skill Phase 5. Every test run and every analyst (including subagents that handle one chunk) uses it, so conclusions stay comparable.

The labels below go into the Chinese report verbatim. Each one has an English gloss the first time it appears; use only the Chinese label in the report.

## What a semantic step is

**One step = one intentional action by the agent under test**:

- asking one clarifying question (one message that asks three questions = three steps);
- calling one tool (one Read, one Write, one Bash each count as one step);
- giving one piece of conclusive output (presenting a plan, a summary, a description of a deliverable).

Thinking blocks are **not steps on their own**. Use them only to help judge the intent of nearby actions (for example, "why did it skip this section").

## Step-side judgment (pick one of three per step)

### `依据 Rx` (based on Rx)

The step corresponds to instruction Rx, and what the agent did matches what the instruction requires.

- Positive example: the skill requires "ask only one question at a time", and the agent sends a single question → `依据 Rx`.
- Edge case: the agent asks clarifying questions, but asks three in one message while the instruction requires one at a time → **not** `依据 Rx`; judge it `偏离 Rx`. The direction of the action is right, but the way it was carried out breaks the instruction.

### `偏离 Rx` (deviates from Rx)

The step clearly falls in the situation instruction Rx applies to, but what the agent did breaks or distorts it.

- Positive example: the skill requires "present the plan before starting work", and the agent goes straight to producing the deliverable → judge the "present first" instruction `偏离 Rx`.
- Edge case: the instruction requires "write the report into the docs/ directory", and the agent writes it to the repo root → `偏离 Rx` (it did the work, but in the wrong place), and on the instruction side that instruction is recorded as `被违反`.

### `无依据` (no basis)

The skill does not ask for this action; the agent acted on its own.

- Positive example: the skill does not mention git, and the agent runs `git status` on its own to check the environment → `无依据`.
- Note: `无依据` is not negative in itself. It may expose an instruction the skill is missing (the agent had to fill the gap), or it may just be normal general ability. The report's "design diagnosis" section decides which; here, just label it accurately.

## Instruction-side judgment (pick one of four per instruction)

- **`已遵守` (followed)**: there is at least one `依据 Rx` step, and no `偏离` step for the same instruction.
- **`被违反` (violated)**: there is a `偏离 Rx` step (even if it was followed the rest of the time; one violation counts as violated, and the details go in the notes column).
- **`被跳过` (skipped)**: the scenario meets the instruction's applicability condition (see the "applicability condition" column in checklist.md), but no corresponding action happens anywhere in the run.
- **`未触发` (not triggered)**: the scenario never reaches the instruction's applicability condition.
  - Distinguishing example: the instruction is "when the user brings requirements for several subsystems, first suggest splitting them", and the test scenario has only one requirement → `未触发` (not `被跳过`; the agent was right not to do it).

## Confidence rules

- Whenever you are unsure about a judgment, mark it **`存疑`** (doubtful) and attach a quote from the transcript (line number or turn). Do not force a judgment.
- When an intent inference relies on thinking content, note "based on thinking" (依据 thinking) in the notes column.
- For parts of the transcript where thinking is missing, downgrade every intent-inference judgment to `存疑`.

## Summary statistics

- **Compliance rate = 已遵守 ÷ (已遵守 + 被违反 + 被跳过)**. `未触发` is not counted in the denominator.
- List `存疑` judgments separately; do not merge them into any status count.
- Background items (B1..Bm) do not count in any statistic.
