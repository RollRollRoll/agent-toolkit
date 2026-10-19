---
name: codebase-analyzer
description: Investigate an unfamiliar project or codebase and explain its purpose, architecture, and implementation in a structured Chinese report.
---

# Codebase Analyzer: Project Investigation

## Goal

Investigate the software project the user names (or the one in the current working directory) and produce a **structured investigation report written in Chinese**. The target reader is
an engineer who "doesn't know the project but needs to build a complete mental model quickly". The report must answer two questions:

1. **What it does**: project positioning, core features, users, and value.
2. **How it is implemented**: architecture, tech stack, key paths, how it runs.

**Pick the report's level of detail from "Output depth" below**; do not apply the full template in every case.

## Output depth (pick a tier first, then investigate)

Different requests need different report depths. Pick the right tier before starting, so a request for a quick look does not get a long report.
**Read only the one output template that matches the tier** (the shared investigation-checklist / project-type-checklists are still read as needed):

- **Quick overview (light)**: half a screen to one screen: a one-sentence definition + tech stack + directory map + a short description of one core flow.
  Fits "take a quick look / brief intro / roughly what is it". Template: [template-quick.md](references/template-quick.md)
- **Standard investigation (default)**: builds a complete mental model without padding: 9 main sections; conditional sections that don't apply get one line.
  Template: [template-standard.md](references/template-standard.md)
- **Deep report (heavy)**: strictly and fully covers all 10 chapters + appendix, nothing skipped. Fits "full report / detailed investigation / comprehensive analysis / deliverable document".
  Template: [template-deep.md](references/template-deep.md)

**Tier rules**:

- The user explicitly wants a "full / detailed / comprehensive" report → deep report; says "quick / brief / roughly / skim" → quick overview.
- **When nothing is stated, default to standard investigation**: neither shallow nor overloaded.
- When unsure, produce the standard investigation first, and end with one sentence telling the user "需要更深可展开为深度报告，需要更轻可只看快速概览" (it can be expanded into a deep report, or cut down to the quick overview).

> Project size and output depth are **independent**: a large project can still get just a quick overview. The "Workflow" below is described for **standard investigation / deep report**;
> when quick overview is chosen, just do the step 1 collection + output per template-quick, and trim steps 2-3 as needed.

## Investigation principles

These four apply to every step, not to any single step:

1. **Conclusions need source-code evidence that can be checked**: tie every important conclusion to a **specific source path (with line number)** where possible,
   e.g. "this is the entry point" or "this path writes to the database" followed by `path:line`, so the user can jump to the source and verify.
   **Never assert a feature from the project name or README**: for a capability the README claims, find its implementation in the source before confirming it;
   if you cannot find it, treat it as "声称但未在源码验证" (claimed but not verified in source). A conclusion without evidence must say explicitly "不确定 / 未在源码确认" (uncertain / not confirmed in source).
2. **"Not applicable" ≠ "not figured out"**: a simple CLI with no authentication is "不适用（原因：本项目不涉及用户身份）" (not applicable, reason: the project has no user identity),
   not "didn't figure out where auth is". The first is a firm conclusion, the second is a blind spot; mixing them misleads the reader.
   Put all blind spots in the `未搞清楚的部分 / 假设 / 已知问题` section (unclear parts / assumptions / known issues: chapter 9 in the standard tier, chapter 10 in the deep tier; the quick tier has no such section, so one line "未搞清楚 X" is enough); do not fill unknowns with plausible guesses. When a conditional section doesn't apply, write one line
   "不适用（原因）" (not applicable, with reason); no need for forced subheadings and placeholder content.
3. **Top-down, not file-by-file**: grasp the big picture first (README / entry point / config / dependencies / directories), then go into the implementation.
   **Skipped by default and not scanned**: `.git`, `node_modules`, `.venv` / `venv`, `dist`, `build`, `out`, `target`,
   `coverage`, `__pycache__`, `.next` / `.nuxt` and other build output, plus code-generation directories (`generated/`, `*.pb.go`,
   `*_pb2.py`). Large lock / bundle files (`package-lock.json`, `yarn.lock`, `*.min.js`) are **not read by default**;
   look at the relevant entries only when you need to confirm a dependency version.
4. **Read sensitive config minimally; the report must not leak credentials**: by default **do not read the contents of real environment files or suspected credential files**:
   `.env`, `.env.*` (except `.env.example` / `.env.sample`), `secrets.*`, `credentials.*`, `.npmrc`,
   `.pypirc`, `.netrc`, `*.key`, `*.pem`, and cloud provider credential files; also do not run commands that dump the environment, such as `env` / `printenv`.
   When you need to judge whether something was committed by mistake, check only the file name, tracking status, and ignore rules. For config, read only example files and the config-loading code;
   even in an example file, if you hit what looks like a real token / password / key, stop expanding it and mark it sensitive. When reporting environment variables, write only
   **variable name, purpose, whether required, and where it is loaded**; do not copy values from the running environment. Write every credential default as `[已脱敏]` (redacted).
   This rule also applies to subagent briefs, intermediate progress, code snippets, and the final report written to disk.

## Workflow

### Step 0: Confirm the target and the output-depth tier

First confirm the directory path to investigate. If the user did not give one, default to the current working directory. If the current directory is empty or clearly not a code project,
stop and ask the user. Also **settle the tier** per "Output depth"; this decides which template file step 4 reads. If the user didn't say, default to **standard investigation**.

### Step 1: Top-down information gathering

Skim quickly in this order:

| Order | What to look at | What it tells you |
|---|---|---|
| ① | Root `ls`, `README*`, `docs/`, `CHANGELOG*` | What the project is, who it is for, how to use it |
| ② | Dependency manifests: `package.json` / `pyproject.toml` / `requirements*.txt` / `go.mod` / `pom.xml` / `Cargo.toml` / `build.gradle` / `composer.json` etc. | Language, framework, key third-party libraries |
| ③ | Config / deployment: `.env.example` / `.env.sample`, `config.example.*`, config-loading code, `Dockerfile*`, `docker-compose*`, `Makefile`, `.github/`, `k8s/`, `helm/`, `terraform/` | Variable names and where they load from, deployment method, CI/CD; skip the contents of real `.env` and suspected credential files |
| ④ | Program entry: `main.*`, `index.*`, `app.*`, `cmd/`, `bin/`, `manage.py`, framework-convention entry points (e.g. Spring's `@SpringBootApplication`, Next.js `pages/` `app/`) | Where execution starts |
| ⑤ | Top-level directory structure | Module breakdown |
| ⑥ | Data models: `models/`, `entities/`, `schema.*`, `migrations/`, ORM definitions | Core entities and relationships |
| ⑦ | External interfaces: route tables, controllers, API definition files (OpenAPI / proto / GraphQL schema) | Exposed capabilities |
| ⑧ | Test directories, CI config | Engineering practice |

For most modules, **looking at the entry point, directory index, and key class names** is enough; read source in depth only when tracing an end-to-end flow.

### Step 2: Identify the project type and add type-specific analysis

Judge the project type from the dependencies, entry points, and directory structure gathered in step 1 (**go by evidence, not by names**), and add the analysis from the matching section of
[project-type-checklists.md](references/project-type-checklists.md). Common types:
**CLI project**, **Web service**, **Library / SDK**, **Agent project**, **MCP Server**, **DevTool / Workflow tool**,
**Agent coding tool plugin / extension (Claude Code / Codex)**.

- A project can match several types at once (e.g. "Web service + ops CLI"). Do a separate type-specific analysis for each match, and give the evidence for each.
- If no clear type fits, write "未匹配到专项类型" (no specific type matched) and do only the general investigation; do not force a fit.

### Step 3: Pick 1-2 end-to-end flows and trace them fully

Pick the flows that best represent the project's core value (a typical HTTP request, the most central CLI command, one run of a scheduled job, one message-consumption pipeline).
**Trace representative flows, not all of them**; mention minor flows in one sentence. Start at the **entry point** and follow the call chain to the **final output / side effect**
(response, database write, file write, message sent), recording each hop: which file / function it passes (with path), key transformations / decision points,
how the data shape changes, and at which step external dependencies are called.

This is the **most information-dense** section of the report; from it alone the reader should understand how the project's main logic runs.

### Step 4: Organize output with the template for the chosen tier

**Read and fill the template for the tier chosen in step 0**. The three templates are independent; do not mix them:

- **Quick overview** → [template-quick.md](references/template-quick.md): half a screen to one screen.
- **Standard investigation (default)** → [template-standard.md](references/template-standard.md): 9 main sections;
  conditional sections that don't apply get one line, no padding to fill them.
- **Deep report** → [template-deep.md](references/template-deep.md): strictly cover all 10 chapters + appendix.
  Keep every chapter heading; when a chapter has no content write "未搞清楚 / 不适用（原因）" (not figured out / not applicable, with reason); skip nothing.

All three tiers follow the same investigation discipline; they differ only in **coverage and level of detail**. For the specific questions to ask when investigating each section, see
[investigation-checklist.md](references/investigation-checklist.md). Write the type-specific analysis from step 2 into the template's
"项目类型专项分析" (project-type analysis) section (the quick overview tier can omit it).

### Large projects: phases and parallelism (enable as needed)

Rough indicators of "large": more than 500 source files, more than 10 top-level modules, or a report too long to write in one output.
When any of these holds **and the user wants the standard or deep tier** (for a quick overview, just produce it; no phases needed):

1. **First output only "global overview + directory map"**, and tell the user "项目较大，我先给出全局概览和目录地图，
   然后按模块逐个深入，你可以在任何时候打断或调整顺序" (the project is large; I'll give the overview and directory map first, then go module by module, and you can interrupt or reorder at any time). This interim overview is **not bound by any template's completeness rules**.
2. **Investigate modules in parallel**: when the environment provides a subagent tool (Claude Code: `Agent` + `subagent_type=Explore`;
   Codex: a read-only `explorer` or equivalent agent thread), send "investigate module X" out as a separate task.
   **If the tool is not available, fall back to sequential investigation and state "未启用并行" (parallelism not enabled) in the report.**
3. **Aggregate**: after the subagents return, assemble everything yourself per the template, removing conflicts / duplication / inconsistencies between modules; the level of detail follows the chosen tier.
   The deep tier can also **draft report chapters in parallel** (descriptive chapters go to subagents, the core-logic chapters the main agent writes itself) to cut wall-clock writing time.

Splitting rules, task-brief template, output pacing, and two variants are in [parallel-strategy.md](references/parallel-strategy.md).

### Step 5: Self-check

Before output, check "common items + items for the chosen tier". Use only the current tier's list, so a quick overview is not expanded to deep-report standards,
and does not grow into an unnecessarily long report.

**Common items (all three tiers)**:

- [ ] Is the tier right? (Default standard investigation; deep report only when the user wants "full", overview when they want "quick")
- [ ] Are all four investigation principles kept? (Conclusions carry `path:line`; no guessing from names / README; "not applicable" vs "not figured out" kept apart;
      no real `.env` or credential files read; no real values / tokens / passwords / keys in the report or intermediate output)
- [ ] Is the whole report in Chinese?
- [ ] Did you ask about the destination before output? (terminal / file / both) When "file / both" was chosen, did you handle an existing file with the same name?

**🟢 Quick overview tier**:

- [ ] Is it kept to half a screen to one screen? Did it accidentally grow into a standard report?
- [ ] Are the one-sentence definition + tech stack + trimmed directory map + **a short description of one core flow** all there?
      (A short description, not hop by hop; type-specific analysis and overall assessment are **not needed**)

**🟡 Standard investigation tier**:

- [ ] Can the reader grasp the big picture from a glance at the one-page overview?
- [ ] Is there a "## 目录" table of contents at the start of the report (before the one-page overview)? Do its entries match the real ## section headings one to one, and do the links jump?
      (This is the TOC, not the same thing as the "directory map" in chapter 4)
- [ ] Does the directory map "highlight what matters" rather than list everything?
- [ ] Are there 1-2 end-to-end flows, with a file path for each hop?
- [ ] Was the project type identified and type-specific analysis done? (Write "未匹配" if none matched.) Is the overall assessment (including project highlights) given?
- [ ] Are uncertain points listed separately in the "not figured out" section, and kept apart from "not applicable"?

**🔴 Deep report tier**:

- [ ] Are all template chapters present with no headings dropped? Do empty chapters say "未搞清楚 / 不适用（原因）"?
- [ ] Are all standard-tier checks also met? (The deep tier is a superset of the standard tier)
- [ ] Are the deep-tier-only chapters (config / environment variables, observability, security) filled in or marked not applicable?
- [ ] Does the overall assessment chapter (chapter 9) give **project highlights**, each tied to `path:line` (not a generic "clear architecture")?
- [ ] If it matches **DevTool / Workflow tool**: did you **exhaustively cover all work scenarios** as "intent → entry point → flow"?
- [ ] If it matches **Agent coding tool plugin / extension**: did you separate Claude Code / Codex signals, **profile each item, and draw an overall assembly diagram**?
      With many items, did you use parallelism (or note it was not enabled)?
- [ ] If **parallel drafting by report chapter** was used: did you aggregate chapter by chapter / unify terms / **check consistency across chapters**?
      Did the one-page overview come out first, and were chapters pushed as they became ready? With no subagent tool or a small project, did you fall back to serial and note it?

### Step 6: Ask for the output destination

After the report is produced in the conversation and the step 5 self-check passes, **do not paste the full text yet**; ask the user where they want the report.
By default **do not write to disk automatically**; act on the user's choice.

- **How to ask**: when the environment provides an interactive choice tool, use it (e.g. Claude Code's AskUserQuestion or the user-input capability
  exposed by the current Codex session); if not available, ask in plain text and have the user reply with one option.
  - **Terminal**: output the full report in the conversation, do not write a file.
  - **File**: write it to a file; in the conversation only state the saved path and include the report's one-page overview, without repeating the full text.
  - **Both**: output the full report in the conversation, **and** write it to a file.
- **Where the one-page overview comes from** (the part left in the terminal when "file" is chosen): for the standard / deep tiers, take the report's `## 一页纸概览` section directly;
  the quick overview tier has no such section, so take the two or three lines of its `## 一句话定义` (one-sentence definition) and `## 核心价值` (core value) sections.
- **Write details when "file" or "both" is chosen**: write the **original text** of the report just produced (Chinese, Markdown) to the file.
  - **Default location**: the root of the investigated project.
  - **Default file name**: `<项目名>-调研报告-<YYYYMMDD>.md` (`<项目名>` is the project name, taken from the investigated directory name),
    e.g. `codebase-analyzer-调研报告-20260603.md`. If the user gives a path / file name, use theirs.
  - If **a file with the same name already exists** before writing, ask the user to confirm overwrite or rename; do not overwrite silently.
  - Write exactly the report from the conversation; do not trim or expand it for the file.
- **No second question after the choice**: "terminal" means output in the conversation only, no file; a user who wants both a file and the full text in the terminal should choose "both" up front.
- **When a large project is produced in phases**: ask about the destination only after all modules / chapters are aggregated into the complete report; what gets saved is the final complete version,
  not the interim overview. During streaming, push only progress + summaries to the terminal; do not paste each interim draft to the terminal.

## Output format rules

- **The whole report must be in Chinese** (including comments in code snippets; original code stays unchanged).
- Section order **follows the chosen tier's template**; the interim overview in phase 1 of a large project is not bound by the template.
- Wrap file paths in backticks, e.g. `src/server/router.ts:42`.
- Use fenced code blocks with a language tag for code snippets.
- **Use tables** for structured comparison data (module responsibilities, environment variables, external interfaces, external systems, etc.): this multi-column data that needs alignment
  is what tables are for. Do **not** put narrative text, long explanations, or connected reasoning in tables; lists or paragraphs read better.
- The environment variable table lists only variable name, purpose, whether required, and where it is loaded; do not read or copy real values to fill it.
- Use **bold** for emphasis; avoid long stretches of italics.
- **No ornamental prose**: when a plain statement exists, use it; do not replace statements with metaphors or flowery wording.
  Write "一个值得调整的参数", not "一个值得转动的旋钮"; write "这一点依然重要", not "这一点依然有一席之地".
  Such sentences show off the writer instead of conveying a point; metaphors also bring associations the writer didn't choose and can't control, and the reader has to work harder to decode them.

## Common mistakes

- "这个项目大概是一个 web 应用，应该用了 Express。": guessing without looking at the dependency files.
- Reading every file before starting to write the report: wastes context and likely loses the big picture.
- "认证相关的逻辑在 auth 模块里。": no path given, so the reader cannot check it.
- The end-to-end flow only says "request comes in, gets processed, returns": not traced to specific files / functions.
- Writing a firm conclusion like "本项目不涉及用户身份" as "没搞清楚认证在哪": treating not-applicable as a blind spot.
- Outputting a giant report directly without giving an overview first.
- Writing in English, or mixing Chinese and English.
- "认证模块是整个系统的心脏。": a metaphor instead of a statement; write "所有请求都先经过认证模块".
- Reading real `.env` / private keys / credential files to complete the config section, or writing tokens, passwords, keys, or sensitive defaults into the report.
- Flooding the terminal with the whole report without asking about the destination, or writing the report into the project directory without permission.
