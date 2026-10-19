---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `setup-env`.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec using the template below, then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

<spec-template>

# Implementation-Ready Delivery Spec

## Purpose of this document

The `Implementation-Ready Delivery Spec` is the single authoritative document before task breakdown. It answers three kinds of question:

1. **How the system should behave**: the user problem, solution, scope, behavioral requirements, prohibited behavior, edge scenarios, and acceptance criteria.
2. **How the system will be implemented**: the current baseline, technical decisions, components, data, interfaces, failure handling, and compatibility plan.
3. **How to confirm the implementation is correct**: testing principles, test seams, verification methods, and coverage from requirements to design and verification.


## Writing rules

1. Use the project's domain glossary vocabulary throughout, and respect the relevant ADRs.
2. Define each piece of information in full in exactly one authoritative place; other sections refer to it by ID (`REQ`, `SCN`, `DEC`, `VAL`, etc.).
3. Behavior sections describe only externally observable results, with no technology choices or architecture.
4. Technical design must not redefine behavioral requirements; it only explains how they are met.
5. Describe modules, interfaces, and contracts by default. Do NOT list specific implementation file paths; they may end up being outdated very quickly.
6. Don't embed implementation code by default. Only when a prototype's state machine, schema, reducer, or type shape expresses a confirmed decision more precisely than prose, keep the smallest decision-rich snippet and note that it came from a prototype.
7. Don't write a task-by-task build list ahead of time; design dependencies are not task dependencies.
8. Optional sections that don't apply may be deleted, but you must be able to give the reason they don't apply; they must not disappear through oversight.
9. No ornate prose: when there is a plain way to say something, say it plainly; don't replace statements with metaphors and flowery wording. Write "a parameter worth adjusting", not "a knob worth turning"; write "this still matters", not "this still has its place". Metaphors bring associations the author didn't choose and can't control, the reader has to work harder to decode them, and the spec loses precision.

---

## Minimal ID scheme

| Type | Format | Use |
|---|---|---|
| Positive requirement | `REQ-001` | Behavior the system must provide |
| Negative requirement | `NEG-001` | Behavior the system must not exhibit |
| Quality requirement | `QOS-001` | Quantifiable performance, reliability, security, etc. |
| Scenario | `SCN-001-A` | Observable acceptance scenario for a requirement |
| Technical decision | `DEC-001` | Major technical decision, or one that needs tracing |
| Verification | `VAL-001` | Automated test, benchmark, fault injection, or manual check |

Components, interfaces, and data entities use stable names directly by default; no extra IDs are required.

---

# Implementation-Ready Delivery Spec: `<feature name>`

```yaml
spec_id: <SPEC-ID>
related_issue: <issue or project link>
source_context:
  - <GLOSSARY.md or GLOSSARY-MAP.md>
related_adrs:
  - <ADR; write none if there are none>
last_updated: <YYYY-MM-DD>
```

---

## 1. Problem, Solution, Outcome and Scope

### 1.1 Problem

The problem that the user is facing, from the user's perspective. Don't write the technical solution here.

```markdown
<who hits what problem in what situation, and what it leads to>
```

### 1.2 Solution Overview

The solution to the problem, from the user's perspective: what capability the system will provide, and how users or upstream / downstream systems get the result. Don't write components, databases, frameworks, or protocol choices.

```markdown
<what user-visible solution the system provides, and how the main flow improves the current problem>
```

### 1.3 User Stories (as needed)

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an `<actor>`, I want a `<feature>`, so that `<benefit>`
2. As an `<actor>`, I want a `<feature>`, so that `<benefit>`

<user-story-example>

1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending

</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.


### 1.4 In Scope

- `<capability explicitly built in this delivery>`
- `<main flow explicitly covered in this delivery>`
- `<compatibility, migration, or runtime behavior this delivery must guarantee>`

### 1.5 Out of Scope

- `<capability explicitly not built>`
- `<content adjacent to the current problem but not part of this delivery>`

### 1.6 Hard Constraints

- `<compatibility constraint>`
- `<performance or capacity constraint>`
- `<security or compliance constraint>`
- `<tech stack, deployment environment, or dependency constraint>`
- `<settled ADR constraint this design cannot change>`

### 1.7 Change Summary

| Change Type | Content | Impact on existing system |
|---|---|---|
| Added | `<new behavior or capability>` | `<impact>` |
| Modified | `<changed behavior>` | `<impact>` |
| Removed | `<removed behavior>` | `<impact>` |

---

## 2. Behavioral Contract

This chapter is the only authoritative definition of system behavior.

Normative vocabulary:

- `MUST`: must be met;
- `MUST NOT`: must not happen;
- `SHOULD`: should be met by default, with explicit exceptions allowed;
- `MAY`: allowed but not required.

Requirements may be organized like this:

```markdown
### ADDED Requirements
### MODIFIED Requirements
### REMOVED Requirements
```

`MODIFIED` must give the full contract after the change, not just a diff summary; `REMOVED` must say how the system behaves after the removal.

### 2.1 Functional Requirements

#### REQ-001: `<behavior title>`

The system MUST `<behavior observable by the user or an external system>`.

##### SCN-001-A: `<normal scenario>`

- GIVEN `<precondition, optional>`
- WHEN `<trigger>`
- THEN `<observable result>`
- AND `<additional result, optional>`

##### SCN-001-B: `<error or edge scenario>`

- GIVEN `<precondition>`
- WHEN `<error, edge, or race condition>`
- THEN `<result the system must show>`

### 2.2 Negative Requirements

#### NEG-001: `<prohibited behavior title>`

The system MUST NOT `<observable behavior that must not happen>`.

Verification:

- `<check at the user, API, or external system level>`
- `<supporting check at the code, dependency, configuration, or documentation level>`

A negative requirement needs at least one verification observable by the user or an external system, not only "a certain class does not exist in the code".

### 2.3 Quality Requirements (as needed)

Keep only when there are explicit, quantifiable quality targets.

#### QOS-001: `<quality requirement title>`

The system MUST `<quantified performance, capacity, reliability, security, or compliance target>`.

Verification:

- `<load test, benchmark, fault injection, audit, or observation method>`

---

## 3. Technical Design

This chapter answers "how to implement it" and must not redefine the system behavior in §2.

It describes stable modules, interfaces, data constraints, and technical decisions. Do NOT list specific implementation file paths, which go out of date quickly. Don't embed implementation code, unless a prototype snippet expresses a confirmed decision more precisely than prose.

### 3.1 Existing Context / System Context

#### Brownfield

- Current relevant modules and responsibilities:
- Current main data flows:
- Current interfaces, events, and data structures:
- Current error handling and runtime constraints:
- Existing test seams and test patterns:
- Similar implementations or prior art in the codebase:
- Domain terms and ADRs to respect:
- Existing behavior that must not break:

#### Greenfield

- System boundary:
- External actors and external systems:
- External dependencies:
- Deployment and runtime boundary:
- Main domain contexts and their relationships:
- Settled tech stack or platform constraints:

Keep only the current state relevant to this feature; don't rewrite the whole system architecture.

### 3.2 Key Technical Decisions

Write a full Decision only for decisions that are major, hard to reverse, or involve a real trade-off.

#### DEC-001: `<technical decision title>`

**Selected**

```markdown
<the option finally adopted>
```

**Alternatives**

- `<candidate option A>`
- `<candidate option B>`

**Trade-off**

| Dimension | Selected | Alternative |
|---|---|---|
| Complexity | `<assessment>` | `<assessment>` |
| Performance | `<assessment>` | `<assessment>` |
| Reliability | `<assessment>` | `<assessment>` |
| Maintainability | `<assessment>` | `<assessment>` |
| Migration Cost | `<assessment>` | `<assessment>` |

**Rationale**

```markdown
<why this option was chosen, and why the others were not>
```

**Supports**

- `REQ-xxx`
- `NEG-xxx`
- `QOS-xxx`

**Assumptions**

- `<unverified premise this decision depends on; delete if none>`

**ADR**

- `<ADR or N/A>`

Routine, easily reversed decisions can be shortened to:

```markdown
- <decision point>: <choice> (<one-sentence reason>)
```

### 3.3 Components and Data Flow

| Component | Change | Responsibility | Depends On | Supports |
|---|---|---|---|---|
| `<component>` | Add / Modify / Remove | `<single responsibility>` | `<dependencies>` | `<REQ / NEG / QOS>` |

Main data flow:

```text
<entry point>
  → <component A>
  → <component B>
  → <storage, external interface, or event>
  → <result>
```

### 3.4 Data and Interface Changes

| Item | Type | Change | Contract / Constraint | Supports |
|---|---|---|---|---|
| `<entity or interface>` | Data / API / Event / Config | Add / Modify / Remove | `<key fields, input/output, or constraints>` | `<REQ / NEG / QOS>` |

External interfaces and cross-module contracts must state:

- input;
- output;
- error semantics;
- idempotency semantics;
- permissions and data visibility;
- backward compatibility;
- event ordering, delivery, and deduplication semantics.

### 3.5 State, Concurrency and Idempotency (as needed)

Keep only what applies. If it doesn't apply, delete this section or briefly state why.

#### State Model

```text
<state A>
  ├─ <condition> → <state B>
  └─ <condition> → <state C>
```

#### Concurrency

- `<concurrency boundary>`
- `<locks, versions, transactions, leases, or serialization>`
- `<whether different entities or partitions can run in parallel>`
- `<how concurrency conflicts show externally>`

#### Idempotency

- `<how duplicate requests are handled>`
- `<how events or commands are deduplicated>`
- `<what the idempotency key and its lifetime are>`

### 3.6 Error and Failure Handling

| Failure | Observable Behavior | Recovery / Degradation | Covered Scenario |
|---|---|---|---|
| `<failure case>` | `<externally observable result>` | `<recovery, retry, compensation, or degradation>` | `<SCN>` |

Failure design must cover at least:

- invalid input or state;
- dependency timeout or unavailability;
- partial success;
- retries and repeated execution;
- data inconsistency;
- manual takeover or safe stop when automatic recovery is impossible.

### 3.7 Migration, Compatibility, Rollout and Rollback (as needed)

In brownfield work, keep this section whenever data, interfaces, configuration, or runtime behavior change.

#### Migration

- `<schema, data, or configuration migration>`
- `<migration order>`
- `<how it runs during the mixed-version period>`
- `<migration failure handling>`

#### Compatibility

- `<API, event, data, old client, or mixed-version compatibility>`
- `<which old behavior must be kept>`

#### Rollout

- `<feature flag, rollout scope, enable order, and observation window>`

#### Rollback

- `<trigger conditions>`
- `<code, configuration, schema, or data rollback>`
- `<degraded behavior when rollback is impossible>`

### 3.8 Observability, Security and Performance (as needed)

Delete the parts that don't apply; don't fill them in just to complete the template.

#### Observability

- Logs:
- Metrics:
- Traces:
- Business events:
- Alert conditions:
- Key identifiers needed for diagnosis and audit:

#### Security

- Authentication:
- Authorization:
- Sensitive data:
- Audit:
- Main threats and mitigations:

#### Performance

- Latency budget:
- Throughput budget:
- Capacity assumptions:
- Resource budget:
- Performance degradation boundary:
- Load test or benchmark method:

---

## 4. Verification and Traceability

### 4.1 Testing Principles

- Only test external behavior, not implementation details.
- Prefer reusing the highest existing seam in the codebase that can observe the target behavior.
- Add a seam only when existing seams can't observe a key behavior; add as few as possible.
- Unit tests are for pure logic and high combinatorial complexity; they don't replace integration verification of external behavior.
- Every `SCN` must have a verification method, every `NEG` a negative verification, and every `QOS` quantified evidence.
- Test design should reference similar tests, fixtures, harnesses, or conventions in the codebase (prior art) rather than invent a new pattern.

### 4.2 Test Seams

| Seam | Level | Reason | Prior Art | Covers |
|---|---|---|---|---|
| `<test entry point>` | Unit / Component / Integration / Contract / E2E | `<why test at this level>` | `<existing similar test or pattern; write none if there is none>` | `<REQ / NEG / QOS>` |

### 4.3 Verification Plan

| Verification | Requirement / Scenario | Method | Expected Result |
|---|---|---|---|
| VAL-001 | `<REQ, NEG, QOS, or SCN>` | `<automated test, benchmark, fault injection, or manual check>` | `<pass condition>` |

### 4.4 Requirement Coverage

This table is the minimal traceability loop. Every `REQ`, `NEG`, and `QOS` in this version must have a design location and a verification method.

| Requirement | Design Location | Verification | Status |
|---|---|---|---|
| REQ-001 | `<component / interface / DEC / design section>` | VAL-001 | Covered |
| NEG-001 | `<design restriction / interface / DEC>` | VAL-002 | Covered |
| QOS-001 | `<performance, security, or reliability design>` | VAL-003 | Covered |

Allowed statuses are only:

- `Covered`: design and verification are both explicit;
- `Blocked`: missing behavior, design, or verification information that blocks breakdown;
- `Deferred`: explicitly not in this version, with the condition for revisiting stated.

### 4.5 Verification Commands

```bash
<build command>
<unit test command>
<integration / contract / e2e test command>
<lint command>
<static analysis or other required check>
```

The final document must use the repo's real commands, not abstract tool names.

### 4.6 Completion Criteria

- All scenarios of every `REQ` in this version pass;
- All negative verifications of every `NEG` pass;
- Every `QOS` meets its quantified threshold;
- Requirement Coverage has no unexplained `Blocked`;
- Brownfield compatibility, migration, rollout, and rollback verifications pass;
- No unexplained skipped tests;
- Key logs, metrics, events, and audit information can be observed;
- §5 Open Items has no blocking unresolved questions.

---

## 5. Open Items

Record only supplementary information that doesn't fit the sections above but is genuinely useful for implementation and review. Don't hide unresolved key questions in this section.

- `<supplementary note>`

</spec-template>
