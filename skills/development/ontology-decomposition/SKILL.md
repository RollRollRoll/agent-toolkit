---
name: ontology-decomposition
description: Decompose a system into an ontology of its business world (objects, relations, states, rules, actions, events), then map that model onto software architecture, delivered as six Chinese model assets. Use when the user asks for 本体论拆解 (ontology decomposition) of a new system, or for the gap between a target ontology and an existing system being refactored.
---

# Ontology Decomposition

Define the **business world** first, the software system second. Decompose by what exists and happens in the business (objects, properties, relations, states, rules, actions, events); together these form one **ontology**, the single semantic model every later artifact maps from. Pages, menus, database tables, and microservices are mappings of the ontology, decided in step 7; the ontology's structure comes from business scenarios alone.

## Pick the branch

- **New system**: run steps 1-8.
- **Existing system** (refactor, gap analysis): read [references/existing-system.md](references/existing-system.md) before step 1. It adds a bottom-up path and a gap analysis around the same eight steps.

## Sources and output

Business sources are the user, product and process docs, tickets, and an existing `GLOSSARY.md` (reuse its terms as written; record any conflict you find as an open question). Ask the user for whatever the sources leave unanswered, batching the questions per step.

Write the deliverables in Chinese into `docs/ontology/` of the target repo, or the location the user names; ask before overwriting an existing file. File list and formats are in [references/deliverables.md](references/deliverables.md). Each step names the files it writes; write them when that step completes.

Give every element a stable ID so later files can cite it: `CQ-01` competency questions, `S-01` scenarios, `R-01` relations, `RULE-01` rules, `A-01` actions, `E-01` events. An Object is cited by its English PascalCase identifier next to its Chinese name (`Robot 机器人`).

## Steps

### 1. Bound the business world

State the business goal, the actors, what the system manages, what it leaves to its neighbours, and the **competency questions**: the business questions the finished ontology must be able to answer ("哪些机器人现在能执行这张任务？").

Done when all of these are written down and every out-of-scope item names the system or role that owns it.

### 2. Extract scenarios

Reconstruct end-to-end scenarios: trigger, actors, ordered steps, business result. For each normal flow, list its exception flows (what can fail at each step and what the business does about it) and the collaborations that cross the system boundary.

Done when every competency question is exercised by at least one scenario, every normal scenario has its exception flows listed, and the user has confirmed the boundary and the scenario list. Everything downstream derives from these two, so this is the one gate where you stop for confirmation. Write `00-scope-and-scenarios.md` and the index `README.md` before you stop.

### 3. Identify objects

Pull every noun and verb phrase out of the scenario steps and classify each with this test (examples from a robot control system):

| Question | Model as | Example |
|---|---|---|
| Does it have its own identity and a business meaning others refer to? | Object | 机器人、任务 |
| Does it only describe a feature of another object? | Property | 任务优先级、电量 |
| Does it describe a link between objects? | Relation | 机器人执行任务 |
| Does it name a category an object belongs to? | Type | 巡检任务、搬运任务 |
| Does it state a fact that happened at a moment? | Event | 机器人离线 |
| Does it name an operation applied to an object? | Action | 分配机器人 |
| Does it limit the conditions under which something may happen? | Rule | 能力不匹配禁止分配 |

Judge an Object's independence by business meaning: would the business refer to it, track it, or ask about it on its own? Having a database ID is evidence of nothing. Keep Object and instance apart (`机器人` is the Object, `R-07` an instance). For each Object record its identity criterion (what makes two instances the same one), type hierarchy, properties, lifecycle, and two or three sample instances.

Done when every concept in the scenarios sits in exactly one category, each concept has one term (its synonyms collapsed into the dictionary's 避免 column), and every Object states its identity criterion and lifecycle. Write `01-semantic-dictionary.md` and `02-object-catalog.md` now; steps 4-6 add their terms to the dictionary as they go.

### 4. Build relations

Define each relation on six dimensions:

| Dimension | Content |
|---|---|
| Source | the Object the relation starts from |
| Target | the Object it connects to |
| Semantics | the business meaning, as a verb phrase |
| Cardinality | one-to-one, one-to-many, many-to-many |
| Constraint | the conditions under which the relation holds |
| Temporality | current relation or historical record |

```text
Task ── requires ──> Capability
Robot ── provides ──> Capability
Task ── hasExecution ──> TaskExecution
TaskExecution ── performedBy ──> Robot
```

Mark each as association, inheritance, composition, or dependency. Relations define structure; execution order belongs to scenarios and actions. A candidate relation that only says "A happens before B" is a process step: move it to step 6.

Done when every relation has all six dimensions filled and every Object is connected by at least one relation. An isolated Object is out of scope or missing a relation: resolve which. Write `03-relation-graph.md` and add the relations to the dictionary.

### 5. Define states and rules

For every Object with a lifecycle, draw its state machine: states, allowed transitions, terminal states. Collect rules in three kinds: **state constraints** (what a state permits), **invariants** (true in every state), **decision rules** (conditions that choose an outcome).

Done when every state is reachable from the initial state and either has an exit or is marked terminal, and every rule cites the elements it constrains and the scenario step it came from. Write the state and rule sections of `04-behavior-model.md` and add the rules to the dictionary.

### 6. Define actions and events

Describe every action in the same five parts:

- **Precondition**: 机器人可用、能力匹配、满足调度约束
- **Action**: 分配机器人
- **Transition**: 执行实例进入「已分配」
- **Event**: 机器人已分配
- **Failure handling**: 分配失败时释放预留资源，或重新选择机器人

Name events as past-tense facts.

Done when every transition from step 5 is caused by a named action, every action has all five parts (failure handling states what is released, retried, or escalated), and every exception flow from step 2 lands in an action's failure handling or in an action of its own. Complete `04-behavior-model.md` with the actions and events, and add them to the dictionary.

### 7. Map to system capabilities

| Ontology layer | Concern | Engineering form |
|---|---|---|
| Object model | entities, properties, types | domain model, data model |
| Relation model | how objects connect | associations, indexes, queries |
| Rule model | constraints that must hold | domain rules, validators, policy engine |
| Action model | operations that can run | application services, command interfaces |
| Event model | what changed | domain events, message bus |
| State model | how lifecycles advance | state machines, execution engine |
| Application model | how users operate the objects | pages, APIs, business flows |

Fill the capability matrix: one row per Object and per Action, mapped to application function, service, API, and data. An Object is a unit of meaning, a service a unit of deployment: draw each service boundary from business consistency, transactions, team ownership, and deployment needs, and write that reason beside it.

Done when every Object and Action has a row, every empty cell is marked 缺口, and every service boundary carries its reason. Write `05-capability-matrix.md`.

### 8. Validate with instances and iterate

Walk every scenario step by step with concrete instances (`R-07` 接到 `T-123`), citing the element IDs each step uses. A step with nothing to cite is a gap: return to the step that owns the missing element, fix it, and re-walk. An element no scenario cites is redundant: remove it, or add the scenario that needs it. Then run the quality check, giving each item a verdict with evidence. A check passes only when no open gap counts against it; otherwise it fails and names those gaps.

- **Completeness**: the model explains the core scenarios and their exceptions.
- **Consistency**: each concept has one definition and one set of rules. Test it: search every file for each term in the dictionary's 避免 column; any hit outside that column fails the check.
- **Independence**: core Objects stand free of any page or system module.
- **Composability**: different businesses reuse the same Objects and actions.
- **Evolvability**: a new scenario fits without wide changes to the core model. Test it: invent one plausible new scenario and count the elements it forces you to change.

Done when every step of every scenario cites elements or is listed as an open gap with its reason, every competency question is answered by naming the Objects and relations that answer it, and all five checks carry a verdict. Write `06-scenario-validation.md`, and record the model version and what changed in this pass in `README.md`.

## Report

Finish with a short Chinese summary in the conversation: where the files are and the count of objects, relations, rules, actions, and events, then every capability gap, failed quality check, and open question that needs the user, each by its ID in one line.
