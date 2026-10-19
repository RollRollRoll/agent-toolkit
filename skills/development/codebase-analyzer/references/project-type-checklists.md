# Project-type analysis checklists

> After the top-down skim in step 1, first judge the project type from the dependency manifests, entry points, and directory structure,
> then add the analysis from the matching section. The project name and README are only clues; they cannot be the sole basis for classification.
> A project can match several types at once (e.g. "Web service + ops CLI"). Add one analysis per matched type, each with its evidence.
> These checklists supplement the chosen tier's report template ([template-standard.md](template-standard.md) / [template-deep.md](template-deep.md),
> in the "项目类型专项分析" (project-type analysis) section); the general sections are still filled per the template. The quick overview usually omits type-specific analysis.

---

## How to judge the type first (go by evidence, not names)

- **CLI project**: dependencies include `argparse`/`click`/`cobra`/`commander`/`yargs`;
  a `bin` field in `package.json` / `[project.scripts]` in `pyproject.toml` / a `cmd/` directory.
- **Web service**: dependencies include `express`/`fastapi`/`flask`/`spring-boot`/`gin`/`nest`; there is route registration / controllers; it listens on a port at startup.
- **Library / SDK**: meant to be imported by others, with no standalone long-running entry point; `package.json` has `main`/`exports` but no `bin`;
  published to npm / PyPI / crates / Maven.
- **Agent project**: dependencies include `langchain`/`langgraph`/`autogen`/`crewai` or an LLM vendor SDK; the code has prompt templates, tool registration, an agent loop.
- **MCP Server**: dependencies include `@modelcontextprotocol/sdk` or `mcp`; it declares tools/resources/prompts;
  uses a stdio / SSE / HTTP transport.
- **DevTool / Workflow tool**: aimed at developers itself; used to generate code / docs, orchestrate workflows, or integrate with Git/CI/issues.
- **Agent coding tool plugin / extension**: has a `SKILL.md`, and matches platform signals such as Claude Code's `.claude/` / `.claude-plugin/`,
  or Codex's `.agents/` / `.codex/` / `.codex-plugin/` / `AGENTS.md`.

> It is fine if no clear type can be determined: write "未匹配到专项类型" (no specific type matched) and produce only the general report. Do not force a fit.

---

## a. CLI project

- **Command list**: which commands / subcommands exist? Where are they registered (with path)?
- **Argument parsing**: which library? How are arguments / options / flags defined? Where are required items and defaults?
- **Command → business logic**: which function / handler does each command map to (with path)?
- **Output format**: output to stdout or files? Plain text / table / JSON / colored TTY? What is the exit-code convention?

## b. Web service

- **API routes**: where are all routes registered? List the main route → handler mappings (with paths).
- **Layering**: is there a Controller / Service / Repository (or equivalent) layering? The responsibility and directory of each layer.
- **Database models**: where are core entities defined? ORM or raw SQL? Where is the migrations directory?
- **Authentication and authorization**: where does identity come in (cookie/header/token)? Which middleware validates it? What is the authorization model?
- **Deployment method**: Dockerfile / compose / k8s / serverless? How is it released?

## c. Library / SDK

- **External API / public interface**: where are the public exports (re-exports in `index.ts` / `__init__.py` / `mod.rs`)?
  Which parts are public and which are internal?
- **Example usage**: what is the minimal working example in the README / `examples/` / docs?
- **Version compatibility**: how is semantic versioning done? Are there deprecation markers, breaking-change records (CHANGELOG)? Which runtime / language versions are supported?
- **Extension method**: how do users extend it (plugins / callbacks / subclassing / config injection)? Where are the extension points defined?

## d. Agent project

- **Agent roles**: how many agents are there? What role does each play (with definition location)?
- **Prompts**: where are system / role prompts written? Hard-coded, templated, or in external files?
- **Tools**: which tools are registered? Where are the tool schemas / implementations? How are they called?
- **Memory / context**: is there a memory mechanism? Where are short-term / long-term memories stored? How is context assembled and trimmed?
- **Planner / Executor / Reviewer**: are planning, execution, and review roles separated? Where is each implemented?
- **State transitions**: how does the state machine / loop of one task run? What is the termination condition (with code location)?
- **Multi-agent collaboration**: how do multiple agents collaborate (orchestration / conversation / blackboard / leader-follower)? Where is the collaboration logic?
- **Multi-turn interaction**: does it support multi-turn conversation / persistent sessions? Where is turn state stored?
- **Side-effect capabilities**: does the agent read or write code, run commands, access the network / file system? Where are these capabilities declared and triggered?
- **Output traceability**: can the agent's output be traced back to source / document evidence, or is it pure generation? Is there a citation / evidence mechanism?
- **Safety guardrails**: are there mechanisms against hallucination (fact checking / citation constraints), overreach (permission boundaries), and mistakes (confirmation for dangerous operations / sandboxing)? Where are they implemented?
- **Integrability**: is it suitable for, or already integrated with, MCP, OpenSpec, CI/CD, or code review workflows? Where are the integration points?

## e. MCP Server

- **Capability list**: which tools / resources / prompts does it provide? Where is each defined?
- **Transport**: stdio / SSE / HTTP? Where is it initialized?
- **Tool schema**: how is each tool's input / output schema declared? Where is argument validation?
- **Permission boundaries**: which resources can it access? Are there path / operation allowlists, confirmation for dangerous operations?
- **External system connections**: which external systems does it connect to (DB / API / file system)? Where is the connection config?

## f. DevTool / Workflow tool

### General questions (all tiers)
- **Normal development flow**: how many steps is the standard way to use it? What is the entry command / trigger?
- **Generated files**: which files does it create / modify? Which directory do the outputs land in?
- **Relationship with Git / CI / specs / issues**: does it read or write git, trigger CI, consume specs / issues? Where are the integration points?
- **Changes code or generates docs**: does it change user code directly, or only generate docs / config? What is the scope and reversibility of its changes?

### 🔴 Deep-tier only: exhaustive work-scenario overview

> **Needed only in the deep report tier**. The goal is to cover "every job a user can do with it", missing none. Expand in three layers, "intent → entry point → flow":

1. **List of user intents / tasks**: exhaustively list which tasks users can complete with it, one intent per line (go by evidence, not names).
2. **Each intent → its entry points**: which commands / triggers serve this intent? (with `path`)
3. **Each entry point → main path + branch paths**: the full flow, including key branches such as success / failure / fallback / special input.

**Requirements**:
- Cover **all entry points**, none missing.
- One intent can map to several entry points, and one entry point can serve several intents; cross-mark them as they really are.
- Every conclusion carries `path:line`.
- Division of work with chapter 5 "端到端代表性流程" (representative end-to-end flows) of the deep template: chapter 5 picks the 1-2 most central flows and **traces them hop by hop**; this section **covers breadth** across all scenarios, and flows can be coarser (main path + key branches).

---

## g. Agent coding tool plugin / extension (Claude Code / Codex)

> Projects that contain skill / slash command / hook / subagent designs. **Only the deep report tier** does the full item-by-item interpretation.

### Evidence (go by evidence, not names)
- **Shared signals**: `SKILL.md`, references / scripts, MCP config, hooks, subagent / custom agent definitions.
- **Claude Code**: `.claude/`, `.claude/skills/`, `.claude/commands/`, `CLAUDE.md`,
  `settings.json` / `settings.local.json`, `.claude-plugin/plugin.json` / `marketplace.json`, `agents/`.
- **Codex**: `.agents/skills/`, `.agents/plugins/marketplace.json`, `AGENTS.md` / `AGENTS.override.md`,
  `.codex/config.toml`, `.codex/agents/*.toml`, `.codex/hooks.json` or hooks in config, `.codex-plugin/plugin.json`.
- One repo can support both platforms. State item by item which files are shared, which are thin adapter layers, and which behaviors hold only on one platform; do not treat same-named concepts as fully compatible in their parameters.

### Per-item profile template (one uniform profile for each skill / command / hook / subagent / custom agent)
- **What it is + trigger condition**: a skill's `description` / how a command is invoked / a hook's matching timing and event / the role of a subagent or custom agent
- **Platform and discovery path**: Claude Code, Codex, or both; which manifest, directory, or config discovers it; whether there is a thin adapter entry
- **Input / output / side effects**: what it takes, what it produces, whether it has side effects such as writing files / changing code / running commands
- **Internal key logic**: with `path:line`; which references / scripts / templates it uses
- **Dependencies and collaboration**: what it calls, what calls it

### Overall assembly diagram
> How these extension items are **technically orchestrated** into a whole: which entry point triggers which skill, when hooks are inserted, who invokes subagents, and how Claude Code / Codex manifests point to the shared core.
> A **technical view**, distinct from the user view of the type f scenario overview.

### With many items: parallel interpretation
> When there are many items and interpreting them all at once would fill the context, dispatch subagents in batches per the "Variant: parallel by extension item" section of [parallel-strategy.md](parallel-strategy.md).
