# Investigation question checklist

> This checklist applies to the quick overview, standard investigation, and deep report; they differ only in how far each item is expanded.
> The "template section X.Y" numbers below follow the full chapters of [template-deep.md](template-deep.md); the standard tier merges some sections, so map by meaning.
>
> When investigating each section, use the matching questions to check coverage. When the project truly does not involve an item, write "不适用（原因）" (not applicable, with reason);
> when you have not figured it out yet, write "未搞清楚（原因）" (not figured out, with reason). Do not mix the two. You do not need to write every question into the report, but check each one.
>
> **Sensitive-information boundary**: do not open real `.env`, `secrets.*`, `credentials.*`, package-manager auth files, private keys, or cloud credential files, and do not run `env` / `printenv`.
> Take config evidence only from `.env.example` / `.env.sample`, example config, and loading code. When reporting environment variables, write only variable name, purpose, whether required, and where it is loaded; never real values or sensitive defaults.

---

## 0. General heuristics

- **"If any" principle**: every question implicitly means `if any`. When the project does not involve an item, there is no need to invent content, but say it was not found or does not apply, so the reader does not think you skipped it.
- **Go by evidence, not names**: when judging "is this the entry point / is this the core", give evidence (dependency graph, import relationships, who calls it).
  Asserting the entry point from the file name `main.py` alone can be wrong (many projects put the entry point in `cmd/`, `bin/`, or a framework-convention location).
- **"Should" is a dangerous word**: in the report, write either "I read X and confirmed it is Y" or "I did not see it; I assume it is Y". Do not write vague statements like "it should be Y".

---

## 1. Positioning and features

- What does the first paragraph of the README say? How does the project describe itself?
- Are there demo screenshots, GIFs, example commands, or example requests? These show directly "what it does".
- Is it for end users (a product), developers (a library / framework / SDK), ops (a tool), or a specific industry?
- Does the README / website / package description explicitly state "what it does not do" (non-goals)?
- What are the main inputs? (HTTP requests / CLI arguments / files / messages / events / database changes ...)
- What are the main outputs? (responses / database writes / files written / messages sent / push notifications ...)
- How many core user flows are there? Which one is used most?

**Feature map** (template section 1.4; ask these for every core feature):
- **How is the feature triggered**? (CLI command / HTTP request / function call / schedule / event)
- **Where is the entry point**? (specific file:line)
- **Where is the core implementation**? (the function / class that does the real work, with path)
- **Input and output**: what shape comes in, what shape goes out?
- **Is it verified in the source**, or only claimed by the README (mark the latter as unverified)?

---

## 2. Overall architecture

- Is this a **single-process** or **multi-process / multi-service** project? What is the evidence? (e.g. multiple `main`s, a `Procfile`, multiple Deployments in k8s manifests)
- Single repo with a single package, or a monorepo? If a monorepo, what are the dependencies between packages?
- How do modules communicate: in-process function calls / internal HTTP / gRPC / message queue / shared database? Give one concrete call site for each.
- Is there clear "layering"? e.g. controller → service → repository / handler → usecase → repo / pages → api → lib.
- Where is the boundary between the project and the outside? Through which "exits" are external dependencies (database, cache, third-party APIs, SSO, object storage, etc.) accessed? Which files / modules are these exits concentrated in?
- Is there an explicit "event bus / task queue / scheduler"? If so, where are the event producers and consumers?
- Is there a **plugin / extension mechanism**? How are plugins registered and discovered?

**Control flow** (template section 2.5; data flow answers "where does the data go", control flow answers "what drives execution, when does it end, what happens on error"):
- **How the main entry dispatches**: after receiving a request / command, how is it dispatched to the handling logic? (route table / command dispatch / task queue)
- **Main loop / state machine**: is there a long-running main loop, event loop, or state machine? How do states change? If none, it "exits after a single run".
- **How errors propagate**: how do errors pass upward from lower layers? Is there unified error handling / a catch-all?
- **When the task ends**: what is the normal termination condition? (request returns / command finishes / stop signal received)
- **Failure handling**: is there retry / rollback / fallback / circuit breaking? Where is it implemented? If none, write "无" (none) explicitly.

---

## 3. Tech stack

- Where did you read the language version? (pinned in `.nvmrc` / `.python-version` / `go.mod` / `pyproject.toml`, etc.)
- What is the core framework, and how is it used? (e.g. Spring Boot with starters, Express composing its own middleware, FastAPI + Pydantic style ...)
- Database choice: SQL (which dialect) or NoSQL? Through an ORM or raw SQL? Where is the connection pool initialized?
- Is there a cache layer? A separate service like Redis, or in-process (e.g. lru_cache, caffeine)?
- Is there a message queue? Where are production / consumption? Is an outbox / dead-letter queue used?
- For key third-party libraries, list those that **shape the architecture**; small utility libraries need not be listed. For example, `prisma`, `celery`, `sqlalchemy`, `zod`, `grpcio`, `langchain`,
  and `react-query` should be listed; common libraries such as `lodash`, `pydantic`, and `requests` depend on the case.

---

## 4. Code structure and core implementation

### Directory structure and file map (template sections 4.1 / 4.2)
- How are the top-level directories divided? By layer (controller/service/repo), by business domain, or by package in a monorepo? What is the evidence?
- Which directories "matter": which directories hold the entry point, core algorithms, external interfaces, and data models?
- Are there directories that should obviously be ignored (generated code, vendored dependencies, build output)?
- Can you say in one sentence "to find X, go to directory Y"? That is exactly the **directory map** to draw in the report.

### Program entry
- What is the start command? Look at `scripts.start` in `package.json`, the `run` target in the `Makefile`, the `Procfile`,
  `CMD` in the `Dockerfile`, `[project.scripts]` in `pyproject.toml`.
- What initialization happens after startup? List it in time order: config loading → DI container / framework → database connection → route registration → listen on port / wait for messages.

### Data models
- Where are entities defined? (ORM model / proto / TypeScript interface / Pydantic schema)
- Is there a migrations directory? What is the migration tool?
- How are relationships between core entities (1:1, 1:N, N:N) expressed? Foreign keys or join tables?
- Does the code distinguish "database entities" from "domain models / DTOs / API schemas"? Where does the conversion happen?

### Core algorithms / complex logic
- **Find the parts unique to the project**: every project has 1-3 places of core code where "if this breaks, the whole project is useless". They might be:
  - scheduling / ranking / matching algorithms
  - state machines / workflow engines
  - parsers / compilers / DSLs
  - inference / rendering pipelines
  - complex SQL / query building
  - concurrency / locks / transaction boundaries
- Once found, describe the **idea**; do not paste large blocks of code. Paste the 10-30 most important lines only when needed.

### External interfaces
- HTTP routes: through framework decorators (FastAPI / Flask), config files (`routes.rb`), or explicit registration (Express `app.get`)?
- gRPC / GraphQL: where are the proto / schema files?
- CLI commands: which library? (Click / Cobra / Commander / yargs / argparse) Which function does each subcommand map to?
- SDK public API: what do the re-exports in `__init__.py` / `index.ts` / `mod.rs` contain?

---

## 5. End-to-end flow tracing (most important)

Priority when picking flows:
1. **The flow users notice most** (a typical request, the main CLI command)
2. **The flow that crosses the most modules** (shows the architecture best)
3. **The flow most likely to fail** (transactions, external calls, state changes)

For every hop while tracing, answer:
- **Where it comes in, where it goes out**: call site → called function.
- **How the data shape changes**: it comes in as an HTTP body / proto / string; what does it go out as?
- **Key decisions**: if branches, state-machine transitions, config-driven behavior.
- **Side effects**: database writes / messages sent / external requests / files written / logs written.
- **Error branches**: where do exceptions propagate to? Is there try/catch, does it reach unified error handling?
- **Concurrency**: synchronous, asynchronous, parallel, or queued?

> If one flow spans more than a dozen files, the project is tightly coupled; that by itself is an observation worth writing into "技术债" (technical debt).

---

## 6. Configuration, dependencies, and running

- Config loading order: example config / public non-sensitive defaults in config code → environment variables → command-line arguments? Which has the highest priority? Do not read real environment files to confirm the order.
- Is there a `.env.example` / `config.example.*`? This is one of the first files a newcomer looks at.
- Which **variable names** switch between environments (dev / staging / prod)? (e.g. `NODE_ENV`, `APP_ENV`, `PROFILE`; do not read or report real values)
- Which external services are **required** for the project to start? Which are optional (degrade when missing)?
- Build: does a single command work? Does it need docker / a local toolchain / a private registry?
- CI/CD: does the repo have `.github/workflows`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildkite.yml`, or similar? What is the typical pipeline?
- Logging: which library? Output to stdout or files? Structured or not? Where is the log level configured?
- Monitoring: are metrics emitted? Is an OpenTelemetry / Prometheus client integrated?
- Error tracking: is there initialization code for something like Sentry / Bugsnag?

---

## 7. Engineering practice and quality

- Where is the test directory? Which framework runs the tests? What is the coverage?
- Are tests colocated with the implementation or separated?
- Are there fixtures / factories / test containers (testcontainers)?
- Where is the linter / formatter / type checker configured? Is it enforced in CI?
- Does the repo have ADRs (architecture decision records), design docs, a CHANGELOG?
- How are TODO / FIXME / HACK / XXX comments distributed? Which directories do they cluster in?
- Authentication: where does user identity come in (cookie / header / token)? Which middleware / interceptor handles it?
- Authorization: is permission-checking logic scattered across controllers or unified in one layer?
- Sensitive data: judge how keys, passwords, and tokens are managed from config-loading code, ignore rules, and file tracking status. If you find files that look committed by mistake, such as `.env` or `secrets.yml`, report only the **path and the risk**; do not open them or output their contents.

---

## 8. Project-type analysis

> Template chapter 8. Based on the project type (CLI / Web / SDK / Agent / MCP / DevTool),
> go through the matching questions in [project-type-checklists.md](project-type-checklists.md). If no type can be determined, write "未匹配到专项类型" (no specific type matched).

---

## 9. Overall assessment (highlights / fit / further development)

> Template chapter 9. Answer based on the **facts** you saw earlier, not impressions.

- **Highlights**: does the project have a "cleverest / most distinctive / most worth-learning" design? (an elegant abstraction / a unique algorithm / a clean extension mechanism / a smart engineering trade-off ...) **What is clever about it**, at which `path:line`,
  and why do others find it hard to do this well? Highlights must be tied to specific source code; **do not write a generic "clear architecture"**.
- **Strengths (decision view)**: what strengths do you see in the source / architecture? (clear design / thorough tests / well-defined extension points / complete docs ...)
- **Limitations**: what weaknesses do you see? (tight coupling / missing tests / outdated docs / hard dependency on a framework ...)
- **Suitable / unsuitable scenarios**: in which scenarios is using it directly appropriate? In which is it not recommended, and why?
- **Worth further development or not**: how are code readability, modularity, extension points, and technical debt? If worth it, where to start; if not, what the alternative is.

---

## 10. Unclear parts / assumptions / known issues

The last step before finishing the investigation: actively collect the following:

- In which sections did you write "据 X 推测 / 可能 / 应该" (inferred from X / possibly / should)? Pull out the preconditions behind those sentences.
- Which code reads strangely or seems unreasonable (not necessarily a code smell; it may be a business constraint you do not know about)?
- Which directories / files did you not look at? State the "uncovered areas" so the reader knows the blind spots.
- Where do the README and the actual code disagree?
- Do any TODO / FIXME comments point to clearly unfinished features?
