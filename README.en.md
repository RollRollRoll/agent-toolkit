# agent-toolkit

[中文](README.md) | English

A personal repository of agent tooling, used to manage the `skill` resources I create.

It is mainly a personal knowledge base. The focus is on keeping resources clear, independent,
and maintainable.
Claude Code is published through `.claude-plugin/`, and Codex through `.codex-plugin/` and
`.agents/plugins/`. Both platforms load the same set of skills directly from the root `skills/`
directory.

Skill files (`SKILL.md`, `references/`, `agents/openai.yaml`) are written in English. Skills that
explicitly require Chinese output (such as the `codebase-analyzer` and `test-skill` reports,
`re-explain`, and `create-questionnaire`) still produce Chinese. This README has a
[Chinese version](README.md) and an English version.

## Skill overview

Each skill is a single-responsibility unit. Whoever needs it calls it; there is no fixed
orchestration chain.
The tables below are grouped by **use case**. Skills marked **human only** in the "Trigger" column
are never invoked by the model (the frontmatter has `disable-model-invocation: true`); they run
only when you type `/<name>`. Skills marked "model-invocable" are chosen by the model based on
their `description`, and other skills may also call them as capability units.

### Project setup and planning

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `setup-env` | **human only** | Before using these skills in a repo for the first time | Configures the issue tracker, triage label vocabulary, and domain doc layout, and writes them into `docs/agents/` and `CLAUDE.md` |
| `triage` | **human only** | Issues and external PRs are piling up and each needs a decision on where it goes | Moves them through a state machine of triage roles: categorize, verify, grill if needed, then write an agent brief or an `.out-of-scope/` record |
| `wayfinder` | **human only** | A piece of work is too big for one session and the path is still unclear | Maps it as decision tickets on the issue tracker and resolves them one at a time until the path is clear |
| `grill-demand` | **human only** | You have an idea to talk through from scratch and want a spec at the end | Settles problem and scope, behavior, and technical decisions layer by layer against a coverage list, writing ADRs and the glossary along the way |
| `to-spec` | **human only** | A discussion has already made clear what to build | Skips the interview, synthesizes the current conversation into a spec (including seam decisions), publishes it to the issue tracker, and labels it `ready-for-agent` |
| `to-tickets` | **human only** | A plan or spec is settled and needs to become tickets on the tracker | Splits it into tracer-bullet vertical slices, declares the blocking edges of each, publishes them to the tracker in dependency order, and labels them `ready-for-agent` |

### Design and exploration

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `codebase-design` | model-invocable | You need to design or improve a module's interface, or decide where a seam goes | Provides vocabulary and criteria for deep-module design: interface depth, seam placement, deepening paths, comparing several interface versions |
| `domain-modeling` | model-invocable | Terms conflict, or settled wording and decisions need to be recorded | Sharpens the project's domain language, writes terms into `GLOSSARY.md` on the spot, and records hard-to-reverse, counterintuitive decisions as ADRs |
| `improve-codebase-architecture` | **human only** | You want to systematically find places in the codebase worth deepening | Scans for deepening opportunities, presents them as a visual HTML report, then grills through the one you pick |
| `prototype` | model-invocable | A design question is unclear and you want to test it with throwaway code | For logic questions, builds a shareable single-file HTML demo; for UI questions, builds several fundamentally different variants on one route |
| `codebase-analyzer` | model-invocable | You are taking over an unfamiliar project and need to understand it as a whole first | Investigates it thoroughly and produces a structured Chinese report on what it does and how it is implemented |
| `research` | model-invocable | Before coding, you need to confirm a technical fact and keep evidence that can be rechecked | Sends a background agent to check primary sources and writes the findings, each with citations, into a single Markdown file in the repo |

### Implementation

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `setup-worktree` | model-invocable | You need an isolated workspace before starting, or are running several lines of development in parallel | Creates and verifies an isolated git worktree from an explicit base commit |
| `implement` | **human only** | You already have a spec or tickets and want to build them directly | Implements the spec or tickets: uses `tdd` at the agreed seams where possible, runs `code-review` at the end, then commits to the current branch |
| `implement-spec` | **human only** | The spec has been split into linked tickets and you want all of them done in one run | Schedules subagents in separate worktrees in parallel by blocking order (each implements with `tdd`), merges them one by one into an integration branch, and reviews the whole; opens a PR when the tracker closes work through PRs |
| `tdd` | model-invocable | You want to land a behavior change test-first | Reference for the red-green loop: what a good test is, where to put seams, anti-patterns, loop rules |
| `diagnosing-bugs` | model-invocable | You need to track down a hard bug or performance regression | Builds a tight loop that can go red first, then reproduces, minimizes, tests hypotheses, and instruments; leaves a regression test after the fix |
| `wizard` | model-invocable | Some steps only a human can do: provisioning services, getting keys, clicking through third-party dashboards | Generates an interactive bash wizard that walks the human through each phase, and writes captured values into `.env` or GitHub secrets |

### Review and wrap-up

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `code-review` | model-invocable | You need to check whether a change follows the standards and does what the issue or spec asks | Two-axis review: the standards axis (written standards plus a Fowler code smell baseline) and the spec axis each get parallel subagents; results are shown side by side, not merged |
| `finish-branch` | model-invocable | Development is done and the branch or worktree needs wrapping up | Cleans up debugging code, runs final tests, then lets the user decide to merge, keep, open a PR, or discard |
| `pr` | model-invocable | You need to write a PR body | Explains the change with the smallest visual, shows before/after evidence, and judges whether it is a one-way or two-way door (can it be walked back) and how wide its impact is |
| `git-commit-push` | model-invocable | You need to resolve conflicts, or split finished changes into atomic commits and push them | Resolves conflicts semantically; or checks for sensitive data and unexpected diffs, splits changes into atomic commits, and pushes after confirmation |

### Thinking something through

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `grilling` | model-invocable | A plan, decision, or idea needs to be stress-tested | Asks persistent, in-depth questions until the vague parts surface |
| `grill-me` | **human only** | You want your own plan to be grilled | Manual entry point for `grilling`, with one extra setting: "no pruning" (technical branches get questioned too) |
| `create-questionnaire` | **human only** | There are questions you cannot answer yourself and need to ask someone who knows | Turns those questions into a Markdown questionnaire for that person to fill in |
| `notify-setup` | human / agent | First-time setup or switching Telegram bots | Gives you the wizard command; in your terminal it validates the token, detects the chat_id, and writes the config |
| `notify-test` | human / agent | You want to check the Telegram notification setup | Sends a test notification and reports success or the failure reason |
| `re-explain` | **human only** | You did not understand the previous explanation | Adds context and explains it again in simpler, clearer Chinese |
| `teach` | **human only** | You want to learn a new skill or concept | Treats the current directory as a stateful teaching workspace and produces self-contained HTML lessons and reference docs across sessions |

### Maintaining the agent itself

| skill | Trigger | When to use | What it does |
|---|---|---|---|
| `writing-for-agents` | model-invocable | You need to write or edit a skill, `AGENTS.md`, or `CLAUDE.md` | Reference for writing docs that agents read: context pointers, the two kinds of burden, information hierarchy, completion criteria, steering words, pruning |
| `test-skill` | model-invocable | You want to know how a skill actually runs | Starts a headless blind test in an isolated sandbox and produces a Chinese retrospective report traceable step by step |
| `retro` | **human only** | A coding session has ended and you want to find improvements to the work environment and rules | Reads the session transcript, checks navigation, automated checks, coding standards, instructions, tool efficiency, and information access, and makes recommendations by severity; imported unchanged from upstream |
| `agent-config-sync` | model-invocable | Configuration across several machines or the two CLIs needs to be aligned | Extracts existing configuration into a single declaration, then uses it to safely sync user-level Codex and Claude Code configuration |
| `handoff` | **human only** | The current session is full and another agent needs to continue | Compacts the conversation into a handoff document saved in the system temp directory for the new agent to pick up |

## How skills call each other

The natural order for a piece of development (**reading order only, not a calling constraint**):

```text
grill-demand → to-spec → to-tickets → implement → finish-branch
     │                                     │
     └─ grilling · domain-modeling         └─ tdd · code-review
```

Existing call points:

| Caller | Call point | Called skill |
|---|---|---|
| `grill-me` | Thin human entry point | `grilling` |
| `grill-demand` | Upstream interview for `to-spec` | `grilling` + `domain-modeling` |
| `implement` | Each behavior change | `tdd` |
| `implement` | Final review | `code-review` |
| `implement-spec` | Each implementation subagent completing a ticket | `tdd` |
| `implement-spec` | Overall review after all tickets are integrated | `code-review` |
| `finish-branch` | Writing the body when creating a PR | `pr` |
| `retro` | Checking the writing rules at the start of the retrospective | `writing-for-agents` |

Calling conventions:

- **Calling hands over ownership of the criteria**: the caller does not restate the called skill's
  rules; for details, read that skill.
- **Gates belong to the caller**: the called skill only produces content and hands it back. The
  caller decides whether it passed and whether to continue. When a prerequisite is missing, the
  called skill returns **BLOCKED** instead of doing the upstream work itself.
- **Calling is not the same as spawning a subagent**: by default the skill is loaded and run in
  the caller's own context. When a fresh context is needed, the caller dispatches it explicitly
  and sets its level.
- **The criteria stay the same when the called skill is unavailable**: the caller runs through the
  same criteria itself and states why it fell back.
- **The caller decides where output goes**: the called skill's scripts all accept an optional
  output directory, and default to the skill's own self-ignored dot directory (such as `.tdd/`).
- Whether a skill can be called by other skills is shown by the "calling contract" section in its
  `SKILL.md`; there is no separate declaration file.

## Installation (Claude Code)

Run in Claude Code:

```text
/plugin marketplace add RollRollRoll/agent-toolkit
/plugin install agent-toolkit@agent-toolkit
```

The whole toolkit installs as a single plugin, `agent-toolkit`. To enable parts as needed:

- Plugin level: the `/plugin` interactive UI, or `claude plugin enable|disable agent-toolkit`.
- Skill level: add a deny rule in `/permissions`, such as `Skill(codebase-analyzer)`.

## Installation (Codex)

Run in the Codex CLI:

```text
codex plugin marketplace add RollRollRoll/agent-toolkit
codex plugin add agent-toolkit@agent-toolkit
```

You can also install it from the added `agent-toolkit` marketplace through `/plugins` in the Codex
CLI or the Plugins screen in the Codex App. After installing or updating, start a new task so Codex
reloads the skills.

## Agent notifications (Telegram)

With the plugin installed, Claude Code and Codex CLI send a Telegram message titled `[Agent] project · short session ID` on these events.

| Event | Claude Code | Codex CLI |
|---|---|---|
| Turn complete | ✅ | merged into "turn ended, waiting for input" |
| Waiting for input | ✅ | same as above |
| Permission needed | ✅ | ✅ |
| Error | ✅ | not supported |

Configuration: run the wizard in your own terminal with `python3 <plugin dir>/notify/bin/notify-setup.py` (or ask the `notify-setup` skill for the command). It validates the token, detects the chat_id, writes the config file with permission 600, and sends a test message. You can also configure it by hand (environment variables override the file):

- `AGENT_NOTIFY_TELEGRAM_TOKEN`, `AGENT_NOTIFY_TELEGRAM_CHAT_ID`, `AGENT_NOTIFY_PRIVACY=1` (title and event type only)
- or `~/.config/agent-notify/config.json` (`chmod 600` recommended):

```json
{"telegram": {"token": "123:ABC", "chat_id": "42"}, "privacy": false,
 "events": {"turn_complete": true, "waiting_input": true, "permission": true, "error": true}}
```

- Codex: trust the plugin hooks once in `/hooks`. Claude Code needs no extra step.
- Send a test message with the `notify-test` skill (or `python3 notify/bin/notify-test.py`).
- One-way only; it never changes agent execution or approvals. Failed sends are logged to `~/.local/state/agent-notify/notify.log` and not retried later.
- Requires Python ≥ 3.9 on macOS or Linux.

## Directory structure

```text
agent-toolkit/
  .claude-plugin/
    plugin.json
    marketplace.json
  .codex-plugin/
    plugin.json
  .agents/plugins/
    marketplace.json
  skills/
    development/<skill-id>/
      SKILL.md
      references/
      scripts/
    support/<skill-id>/
```

- `.claude-plugin/`: Claude Code plugin and marketplace manifests.
- `.codex-plugin/`: Codex plugin manifest.
- `.agents/plugins/`: Codex repo-level marketplace manifest.
- `skills/`: the complete skills shared by both platforms; see "Skill overview" above for members
  and responsibilities.

## Adding a skill

1. Create the directory `skills/development|support/<skill-id>/`. The main file is `SKILL.md`;
   supporting material goes in `references/`, scripts in `scripts/`, and the Codex UI description
   in `agents/openai.yaml`. Resource directories do not get their own `README.md` or
   `metadata.yaml`; the main file is the single source of documentation.
2. In the `SKILL.md` frontmatter, set `name` (matching the directory name) and `description`
   (which decides whether the model recognizes when to use it). Add
   `disable-model-invocation: true` to entry points meant only for humans.
   If other skills will call it, the body must also state the calling contract (what goes in,
   what comes back, what it does not do).
3. Write `description` in English, using the "verb describes the capability" template
   (Action + Object): start with a verb followed by its object, say what it does in one sentence,
   and end with a period. Do not open with a preposition or time clause (such as When / For / By /
   Using), and do not add a category-label prefix.
   The `short_description` in `agents/openai.yaml` is also written in English and follows the same
   template. Skills ported from upstream are the exception: their `description` and
   `short_description` may keep upstream's wording verbatim, so later syncs diff cleanly.
4. When publishing with the plugin:
   - Update the `skills` array in `.claude-plugin/plugin.json` (paths include the directory name,
     such as `./skills/development/tdd`);
   - Confirm that `skills` in `.codex-plugin/plugin.json` points to the root `skills/`
     (it scans by directory, so a new skill does not require changing it);
   - Bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
     and `.codex-plugin/plugin.json` together.
5. Add a row to "Skill overview" in both `README.md` and `README.en.md`: when to use it and what it
   does.

## Current non-goals

- Do not automatically rewrite the installed Claude Code or Codex copies on the user's machine.
- No CLI.
- No schema validation.
- No automated packaging, publishing, or installation flow.
- No cross-platform format conversion.
