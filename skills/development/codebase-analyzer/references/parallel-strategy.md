# Parallel investigation strategy for large projects

> Covers when to enable parallelism, how to split tasks, how to give subagents context, and how to aggregate results.

---

## When to enable parallelism

If **any** of the following holds, switch to the "overview first → then go deep in parallel" mode:

- More than 10 top-level modules / services
- More than 500 source files
- A monorepo whose packages are relatively independent
- Writing the report in one go would exceed a single output, or would lose the big picture
- The user explicitly says "the project is large, do it in phases"

When none of these holds, use a single agent investigating sequentially; for small and medium projects that is usually more coherent and faster.

---

## Phased output pacing

> **Applies only to large projects in the standard investigation / deep report tiers.** If the user wants only a "quick overview" of a large project, produce the quick overview (one-sentence definition + directory map + one core flow) directly; do not enter the phased pacing below.

For large projects in the standard / deep tiers, whether or not parallelism is enabled, output to the user in phases at the pace below; do not hold everything back for one big output:

```text
Phase 1: give the "global overview + directory map" first
        ↓ the user can adjust direction / name priority modules here
Phase 2: go deep module by module (can be parallel)
        ↓ sync with the user every few modules
Phase 3: aggregate + connect the end-to-end flows
        ↓
Phase 4: wrap up with unclear parts / assumptions / technical debt
```

**Key point**: after phase 1 output, **pause on your own initiative** and tell the user your next plan, giving them a chance to reorder, name focus areas, or exclude some modules.

**Final output destination**: what you sync to the user during phases 2-4 is **progress + summaries** (global overview, directory map, "module / chapter X is ready"); **do not paste each draft to the terminal**. Once the complete report is aggregated,
let the user pick terminal / file / both per SKILL.md "Step 6: Ask for the output destination". If they pick "file", write the full text to disk and leave only the path + one-page overview in the terminal. This keeps the sense of progress from phasing without flooding the terminal with the full text when "file" is chosen.

---

## Splitting principles

### 1. Split along "high-cohesion boundaries", not by "even line counts"

Good split units:

- An independent service / sub-application
- An independent subdirectory with a clearly separate responsibility (e.g. `auth/`, `billing/`, `worker/`)
- One package in a monorepo (`packages/foo`)
- An independent "pipeline" (data collection / training / inference / evaluation)

Bad splits:

- Dividing `src/` evenly into 5 parts alphabetically for 5 agents: coupling across slices leaves each agent seeing only a fragment.
- One agent each for "controllers", "services", and "repositories": the same business domain gets chopped up, and nobody sees a complete flow.

### 2. Have one agent follow a flow investigation all the way through

**Never** split an end-to-end flow across several agents. Have a single agent trace the complete chain, even across many directories. Otherwise nobody has the complete mental model.

### 3. "Shared foundation" investigation can be its own agent

Low-level modules (e.g. `common/` `utils/` `infra/` `core/`) are worth a dedicated agent, because other modules reference them heavily; mapping them first makes the other modules' reports more accurate.

---

## Task brief template (prompt for subagents)

If the current environment provides a "subagent / multi-agent" tool,
use it to send each module out as a separate read-only investigation task (Claude Code uses `Agent` + `subagent_type=Explore`;
Codex uses a read-only `explorer` or equivalent agent thread; other environments use their own equivalent). **If the current environment has no such tool, skip this section, investigate sequentially with a single agent,
and state "未启用并行" (parallelism not enabled) in the report.** The brief template:

```text
You are a project investigation assistant. Investigate the module below and return a **structured brief in Chinese**. Do not write the full report yourself (the main agent will aggregate).

[Target]
- Project root: {{absolute path}}
- Module path for this task: {{module path}}
- The module's role in the project (known so far): {{e.g. "user authentication service"}}

[Answer these]
1. Module responsibility (one sentence)
2. Entry points / externally exposed interfaces (with file paths)
3. Dependencies:
   - Upstream: who calls this module?
   - Downstream: which other modules or external systems does this module call?
4. Main internal subcomponents / key files (no more than 8, one-sentence responsibility each)
5. Core data structures / key algorithms (if any, with paths and key snippets of up to 10-20 lines)
6. Config items (only environment variable name, purpose, whether required, and where loaded; no real values or sensitive defaults)
7. Test status (where the tests are, how to run them)
8. Unclear / anomalous points (**required**: leaving it empty means the investigation was not careful)

[Constraints]
- Read-only; do not try to run the project
- Do not open real `.env`, `secrets.*`, `credentials.*`, package-manager auth files, private keys, or cloud credential files, and do not run `env` / `printenv`; check only example config, config code, file names, and tracking status
- Do not output tokens, passwords, keys, or other credential values in the brief, code snippets, or intermediate messages
- Conclusions must give file paths; do not guess from names
- Where unsure, write "未确认" (not confirmed) explicitly; do not guess
- Keep the brief to about 600 Chinese characters, key paths first
```

When dispatching several parallel subagents, **send all Agent calls in the same message**; otherwise they do not actually run in parallel.

---

## What to do when aggregating

After the subagents return, **do not** mechanically stitch their briefs together. Instead:

1. **Unify terms**: different agents may use different words (service / module / package); unify them to one set of terms in the report.
2. **Resolve conflicts**: agent A says "auth is in X", agent B says "auth is in Y". Check it yourself; do not leave the contradiction to the reader.
3. **Reorder**: the subagents' investigation order ≠ the report's chapter order.
   Reorganize by the chapters of the chosen tier's template (for large projects usually [template-standard.md](template-standard.md) or [template-deep.md](template-deep.md)).
4. **Add the end-to-end flows**: during aggregation, the main agent picks 1-2 flows and traces them from start to finish itself. This is the part that can least be outsourced.
5. **Merge the "unclear" lists**: put each subagent's unconfirmed items into the report's "未搞清楚" (unclear) chapter, marked with the module they came from.

---

## Variant: parallel by extension item (for Claude Code / Codex plugin and extension projects)

> The parallelism above splits by "business module". When the project is a Claude Code / Codex plugin with many skills / commands / hooks / subagents / custom agents,
> split by "extension item" instead. Corresponds to type g in [project-type-checklists.md](project-type-checklists.md).

### When to enable
- Deep report tier + matches type g (Claude Code / Codex plugin or extension) + many items (interpreting them all at once would fill the context).

### How to split
- **One item per split**: one subagent for each skill / command / hook / subagent.
- **In batches**: no more than 5-6 per batch; send all Agent calls of the batch in the same message for them to actually run in parallel.

### Output required from subagents
- A **profile brief** per item (following the type g "per-item profile template": what it is + trigger condition / input, output + side effects / internal key logic with `path:line` / dependencies and collaboration).
- In Chinese, structured, about 400 Chinese characters, with a required "unclear / anomalous" item.

### Main agent's responsibilities
- Aggregate all profiles, unify terms, resolve conflicts.
- **Draw the overall assembly diagram yourself**: it needs the global view, so do not outsource it to subagents.

### Fallback
- When the current environment has no subagent tool, fall back to interpreting items one by one sequentially, and note "未启用并行" (parallelism not enabled) in the report.

---

## Variant: parallel drafting by report chapter (deep-tier speedup)

> The two kinds of parallelism above parallelize "collection" (by module / by extension item). This variant parallelizes **"writing" in the deep tier**: descriptive chapters are handed to subagents to draft in parallel, the chapters that hold the report together are written by the main agent itself, and phased streaming output is layered on top.
> The goal is to cut wall-clock time **and** give a sense of progress **at the same time**.

### When to enable

Enable only when all of these hold:
- Output depth = **deep tier** (not the standard / quick tiers: their reports are short, so parallelism does not pay off);
- The current environment has a subagent tool;
- The project is **large enough** (use the thresholds from "When to enable parallelism" at the start of this file: more than 10 top-level modules / more than 500 source files / writing it in one go would exceed a single output).

Otherwise fall back to the main agent writing serially (see "Fallback" at the end).

### Chapter division

The deep tier's "one-page overview + 10 chapters" fall into two groups by "whether a global view is needed":

**🔒 Written by the main agent itself** (they hold the report together; splitting them loses information):
- One-page overview (including the ASCII architecture diagram): needs the global view
- Chapter 5, representative end-to-end flows: traced fully by the main agent, not split across agents
- Chapter 9, overall assessment / highlights: based on facts from the other chapters, so it must be written last
- Chapter 10, unclear parts: collects the blind spots reported by each subagent

**🔓 Drafted by subagents in parallel** (descriptive, based on local evidence):
- Chapter 1 positioning and features, chapter 2 overall architecture, chapter 3 tech stack, chapter 4 code structure, chapter 6 configuration and running, chapter 7 engineering quality, chapter 8 type profiles / scenario table

> **Exception for chapter 8**: when chapter 8 matches type g and there are many extension items (which triggers the previous section, "Variant: parallel by extension item"), the main agent handles chapter 8 directly through that path (dispatch profile subagents + draw the assembly diagram itself);
> **do not wrap another chapter-drafter around it**, to avoid nesting two parallel mechanisms. Either way, **the main agent always draws the type g assembly diagram itself**.

### Orchestration timeline

```text
① Collect evidence (large projects reuse "parallel collection by module"; medium projects: the main agent collects itself)
        ↓
② The main agent immediately outputs "first version of the one-page overview + directory map" → pauses on its own initiative
        ↓
③ In parallel (the core of the speedup):
   ├─ Main agent: traces the chapter 5 end-to-end flows itself
   └─ Subagents: draft the 7 🔓 chapters in parallel
        ↓
④ Chapters come back one after another → the main agent aggregates chapter by chapter, unifies terms, resolves conflicts, cross-checks chapters
   After each batch completes → push to the user
        ↓
⑤ The main agent wraps up: writes chapters 9 and 10, corrects the overview's architecture diagram
        ↓
⑥ Self-check → ask for the output destination
```

The **speedup** comes from drafting 7 chapters in parallel + overlapping the main agent's end-to-end tracing with subagent drafting; the **sense of progress** comes from putting out the overview first + pushing chapters as they become ready. Drafter dispatch follows "no more than 5-6 per batch,
sent in the same message to actually run in parallel", so the 7 chapters can go in two batches.

### Output required from subagents (chapter-drafter brief template)

The key difference from the two earlier briefs: **it returns a finished chapter, not a brief**.

```text
You are a project investigation assistant. Draft [Chapter X: {{chapter title}}] of the investigation report,
and return the finished chapter directly as Chinese Markdown (the main agent will aggregate; do not write other chapters).

[Project root] {{absolute path}}
[Evidence summary (for navigation, not the whole truth)]
  - One-sentence definition / tech stack notes
  - Directory map + list of top-level modules (with paths)
  - Entry point locations, key points of the dependency list
[Chapter skeleton] {{the subheading structure of this chapter, taken from template-deep.md}}

[Output requirements]
  - Fill the chapter skeleton's subheadings one by one and produce a finished chapter (not a brief)
  - Where the evidence summary falls short, go back to the source to verify and go deeper; do not just rewrite the summary
  - Every claim carries `path:line`; do not guess from names / the README
  - Do not open real `.env` or suspected credential files; for config write only variable name, purpose, whether required, and where loaded; never output real values or sensitive defaults
  - Keep "不适用（原因）" (not applicable, with reason) and "未搞清楚（原因）" (not figured out, with reason) apart
  - Write in Chinese; length matches the chosen depth tier
[Required] This chapter's "未搞清楚" (unclear) list (sent to the main agent for chapter 10)
```

**Send one shared evidence summary to all drafters** (so each does not rediscover the project structure); each drafter does its own source verification. The hard constraint that every claim carries `path:line` means they cannot just rewrite the summary.

### Main agent's aggregation responsibilities

Follow the 5 points in "What to do when aggregating" above, plus:
- **Cross-chapter consistency check**: module names / responsibilities in chapter 2 (architecture) must match chapter 4 (code structure) and chapter 8 (type analysis); chapter 3 (tech stack) must not contradict chapter 6 (configuration). Check while reading each chapter; resolve conflicts by going back to the source yourself, do not leave them to the reader.
- **Merge each chapter's "unclear" list** → chapter 10. **The main agent traces the end-to-end flows (chapter 5) itself**; do not outsource them.

### Streaming pace

Follow "Phased output pacing" above: overview + directory map first → **pause on your own initiative** so the user can adjust focus / exclude chapters → sync after each batch of chapters → aggregate the complete version last → self-check → ask for the output destination.

### Fallback

- No subagent tool / project on the small side → the main agent writes serially but still **keeps streaming** (overview first + push as you write), and the report notes "未启用章节并行" (chapter parallelism not enabled).
- A chapter's drafter fails or the quality is clearly insufficient → the main agent writes that chapter itself.

---

## Anti-patterns (do not do this)

- Splitting the project's `src/` evenly into 5 parts for 5 agents: the cuts land on high-coupling points.
- Starting to write the report right after dispatching all subagents: filling in from imagination without waiting for them to return.
- Splitting an end-to-end flow between two agents, one tracing the first half and one the second: information is lost at the seam.
- Copying subagents' briefs straight into the report: inconsistent style, inconsistent terms, conflicts.
- Dispatching 20 agents at once for 20 modules: context management gets out of control. Keep batches to no more than 5-6, dispatched in turns.
