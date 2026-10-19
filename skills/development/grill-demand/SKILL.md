---
name: grill-demand
description: "Interview the user in depth to settle problem, scope, behavior, and technical decisions layer by layer, creating docs (ADRs and glossary) as you go. The result should be enough for to-spec to produce a complete spec directly."
disable-model-invocation: true
---

# Grill Demand: build the shared understanding a spec needs

## Role

This skill is the interview upstream of `to-spec`. `to-spec` only synthesizes the existing conversation and the codebase; it does not interview the user any further. So this skill must fill in what the codebase can't confirm and the conversation hasn't yet made clear: the real intent, scope, behavioral contract, and technical decisions.

Before starting the interview, call the Skill tool twice, for "grilling" and "domain-modeling". Each skill's own doc holds its rules:

- **`grilling`**: rounds, the frontier, facts are yours to find, decisions are the user's.
- **`domain-modeling`**: write terms and ADRs to disk as they come up (`GLOSSARY.md` / `docs/adr/`).

This doc only covers the order in which the layers open up, and what the design tree must cover.

This skill needs the user to take part live. It is not for CI, scheduled jobs, or autonomous loops.

## Layered expansion: layers are frontier prerequisites

The coverage checklist has three layers. **A lower layer's questions have the upper layer being settled as a prerequisite.** This is not a separate process; it is grilling's "a question enters the frontier only once its prerequisites are settled", made concrete:

1. While the **problem and scope layer** is unclear (you aren't even sure "what is being solved"), the frontier holds only this layer's questions. Prefer stating your current assumption in full and asking the user to falsify it, for example "My current understanding is that you want X, because Y", with your confidence level. This lets the user correct the whole picture directly, not just pick among options. When the user answers in the abstract (`scalable`, `clean architecture`, "the industry-standard way"), keep asking whether it maps to a real need. When you find a weak spot in the plan, say specifically what is wrong.
2. A **behavior layer** question has as its prerequisite that the capability it belongs to is in scope.
3. A **technical layer** question has as its prerequisite that the behavior it implements is settled. Don't move into technology choices while behavior is still unstable.

Whenever uncertainty surfaces at a higher layer (for example, a technical option makes you realize "the problem they want solved isn't that one at all"), the affected lower branches lose their prerequisites. Go back and reconfirm the higher layer first.

**Size it first**: if the idea is really several independent subsystems, point that out and split it first, then run this process on each one. Don't grow one design tree into a manual for the whole system.

## Coverage checklist (go through every item before ending)

The checklist maps to the Implementation-Ready Delivery Spec template in `to-spec` (see [../to-spec/SKILL.md](../to-spec/SKILL.md)). Anything the template needs that the codebase can't confirm must be covered here; when the template changes, update this checklist to match.

Each item has only three valid end states: **settled** / **not applicable (with a stated reason)** / **explicitly deferred (goes into the spec's Open Items)**. "Never came up" is not an end state.

### A · Problem and scope layer (feeds spec §1)

- **Real intent**: who, in what situation, hits what problem, what happens if it isn't solved, and why now. The literal request is not always the real pain point; keep confirming the reason behind it.
- **Solution (user's view)**: what user-visible capability the system will provide, and how the main flow improves the problem. No components or technology choices.
- **Actors**: which kinds of actor exist and what each needs to get done (raw material for user stories).
- **In scope / out of scope**: two explicit lists. **"Out of scope" must not be empty**; every out-of-scope item must be convertible into a verifiable prohibition at the behavior layer.
- **Hard constraints**: compatibility, performance and capacity, security and compliance, tech stack / deployment environment / external dependencies, existing ADRs. Ask about each of the five, or rule it out.
- **Brownfield add / change / remove**: an Added / Modified / Removed list for existing behavior. For changes, state the full behavior after the change; for removals, state how the system behaves after removal.
- **Greenfield capability tiers**: collect the capability dimensions ("already in the request" plus "added") into a list, and put each dimension in one tier: in / not by default / later version. Don't include everything by default. Whether to first run a survey of the feature space (so a whole class of capability isn't missed) is **the user's decision**: give a recommendation and a one-sentence reason, then wait for the answer. The survey can use a research / deep-research style skill from the environment; if none can run, fall back to listing from domain knowledge and note that no survey was done. Survey output is reference, not requirements; nothing from it is included by default.

### B · Behavior layer (feeds spec §2)

- **Each in-scope capability**: written as an externally observable MUST behavior, with both normal and error / edge scenarios expressible as GIVEN/WHEN → THEN (it only counts once both the trigger and the observable result have been discussed). Anything without an observable result ("should be easy to use", "performance should be good") is a goal, not a verifiable behavior; keep clarifying.
- **Edge probes**: boundary values / null and empty states / sort stability / concurrency and races / idempotency and duplicates / precision / encoding / timeouts and failures. Judge each one for applicability, and write the applicable ones as scenarios.
- **Each prohibition**: how to verify from the user's or an external system's side that it did not happen (no such entry point / doesn't return such data / no such visible capability). A code-level check alone ("there is no such class") does not count as clear.
- **Quantified quality targets**: whether performance, capacity, reliability, or security and compliance have targets that must be quantified (QOS), and how to verify them. If none, state explicitly "this version has no quantified quality targets".

### C · Technical layer (feeds spec §3-4)

- **Decision probes**: for each dimension, judge needs a decision / not applicable (with reason) / deferred: data model; interface contracts; state management; error and failure handling; concurrency and consistency; performance and scale; security and permissions; observability; migration and compatibility; testing strategy and seams; external dependencies and technology choices. "Forgot to think about it" and "thought about it and judged it not applicable" are different things.
- **Major, hard-to-reverse decisions** (a new core data model, external contracts, storage and framework choices, new dependencies, performance budgets, compatibility and security boundaries): give at least two candidate options, the trade-offs of each, and a recommendation, then let the user decide. For routine, reversible decisions: infer, give a one-sentence reason, and state the assumption out loud ("assuming internal read-only, no authentication needed"). Confirm the APIs and version features of a chosen technology from official docs or source, not from memory.
- **Architecture placement**: which (new or modified) component each in-scope behavior lands on, and how the main data flow goes. Treat major structural changes (a new service / new layer / new component boundary) as major decisions.
- **External and cross-module contracts**: for each relevant interface, check input, output, error semantics, idempotency semantics, permissions and data visibility, backward compatibility, and event ordering, delivery, and deduplication.
- **Six failure classes**: invalid input or state, dependency timeout or unavailability, partial success, retries and repeated execution, data inconsistency, and manual takeover or safe stop when automatic recovery is impossible. For each, the externally observable behavior and the recovery method.
- **Brownfield evolution**: migration (order, mixed-version period, failure handling), old behavior that must be kept, rollout and observation window, rollback triggers and method. This item applies whenever data / interfaces / configuration / runtime behavior change.

### D · Fact checklist (look these up yourself; don't ask the user)

Following grilling's rules, dispatch subagents to find these facts as the basis for each layer's questions:

- **Current state**: relevant modules and responsibilities, main data flows, interfaces / events / data structures, error handling and runtime constraints, existing behavior that must not break.
- **Prior art**: similar implementations, existing test seams and test patterns, fixture and harness conventions.
- **Real commands**: how build / test / lint run (the spec's Verification Commands only accepts real commands).
- **Domain docs**: `GLOSSARY.md` terms and relevant ADRs. These are also what domain-modeling uses to challenge terms and reconcile them with the code.

The final choice of test seams, and the user's confirmation of it, happens in `to-spec`. Here you only map the existing seams and ask about any hard preference the user has for test levels.

## End gate

Once grilling's frontier is empty, go through coverage checklist A-D once more. If any item is still undiscussed, put it back on the frontier as a new branch. End only when every item is in one of the three end states.

1. Restate the shared understanding in the user's own words: what is being solved / what is in and out of scope / key technical decisions (one sentence each) / what counts as done / deferred items. Also mention the branches that were not expanded further.
2. Check that domain-modeling has written terms and ADRs as they came up, and nothing is left unrecorded.
3. Tell the user: this discussion is enough for `to-spec`; run `to-spec` to produce and publish the spec. **Don't run to-spec yourself, and don't start implementing.**

## Common mistakes

- Expanding behavior and technical branches in parallel before the problem layer is clear. Layers are not process decoration; they are prerequisites.
- Leaving "out of scope" empty, or writing only "no sync" without being able to say how to verify it didn't happen.
- Glossing over a major, hard-to-reverse decision (data model / external contract / new dependency) with "just use X", without laying out candidates and trade-offs.
- Asking the user for codebase facts a subagent could find.
- Declaring the session over as soon as the frontier is empty, without sweeping the coverage checklist, so "never came up" gets mixed in with "covered".
- Writing and publishing the spec at the end as well. Producing the spec is to-spec's job; this skill stops at shared understanding.
- Restating grilling's round rules or to-spec's template format here. Each rule lives in its own skill.
