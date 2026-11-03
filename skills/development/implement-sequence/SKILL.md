---
name: implement-sequence
description: "Implement a set of tickets one at a time, each next ticket picked by closeness to the last one done and closed as soon as it is built."
disable-model-invocation: true
---

You have been given a set of tickets: a spec or parent issue whose sub-issues are the tickets, or a list of ticket references. If the reference is ambiguous, ask.

The issue tracker should have been provided to you. If not, tell the user to run `setup-env`.

The goal is every ticket in the set built on one branch, **one at a time**, each the way `implement` builds work and closed on the tracker as soon as it is done, with no PR.

The tickets are a **task graph** with blocking edges. The **frontier** is the open tickets in the set whose blockers are all closed. The tracker doc says how to read blocking edges.

## Steps

1. Read every ticket in the set and its blocking edges. Note the current `HEAD`: it is the fixed point for the final `code-review`. Then ask the user, in one message:
   - if the current branch is the default branch, whether to build on it or on a new branch; every round of this run uses that answer;
   - every decision the spec or tickets leave open that you can already see, with the options and the one you recommend.

   Problems that only surface during implementation still come back as **blocked** reports.

2. Note the **last ticket**: the ticket finished most recently in this run. On the first round, it is the ticket in the set closed most recently on the tracker; when none is closed, there is no last ticket.

3. Pick one ticket from the frontier by **closeness** to the last ticket:
   1. **Business closeness**: same domain concept, user flow, or feature as the last ticket (use the `GLOSSARY.md` vocabulary to judge).
   2. **Implementation closeness**: touches the same modules, seams, or data as the last ticket; its changed files and summary are the evidence.
   3. Ties, or no last ticket: the first in tracker order.

   Before the Agent call, output this line to the user as reply text, not in your reasoning:

   `Next: <ticket> — shares <what> with <last ticket>`

4. Dispatch one **implementer subagent** for the picked ticket; every ticket and the review fixes are built by implementer subagents, never by you. Dispatch it in the foreground, on the branch. Brief it as described in [Implementer subagents](#implementer-subagents), adding the answers from the user so far that apply beyond their ticket. Only one subagent runs at a time.

5. When it reports **blocked**, ask the user its questions as described in [Questions for the user](#questions-for-the-user), then resume it. When it reports done, check its commit is on the branch, close the ticket with a comment naming the commit and the pick reason from step 3 (when the tracker lives in the repo, commit that change), and record its summary and changed files as the evidence for the next pick.

6. Repeat from step 2 until the frontier is empty. If open tickets remain outside the frontier (blocked by tickets outside the set, or a cycle), stop and ask the user how to proceed.

7. Call the Skill tool with `code-review` on the branch, using the commit from step 1 as the fixed point and the set of tickets as the spec. Split its findings:
   - **Product decisions**: findings that change agreed or shipped behaviour, or that the spec leaves open. Ask the user about them first, each with the options and the one you recommend.
   - **Fixes**: every other finding.

   Then dispatch a single **implementer subagent** with the fixes and the user's answers in place of a ticket; there is no ticket to close for it.

8. Report: the tickets in the order built, each with its commit and pick reason, and the review-fix commit.

## Implementer subagents

Each **implementer subagent** builds one ticket on the branch, exactly the way `implement` does. Its brief is the ticket reference, a pointer to the spec, and this text from `implement`, verbatim:

> Implement the work described by the user in the spec or tickets.
>
> If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.
>
> Call the Skill tool with "tdd" where possible, at pre-agreed seams.
>
> Run typechecking regularly, single test files regularly, and the full test suite once at the end.
>
> Once done, call the Skill tool with "code-review" to review the work.
>
> Commit your work to the current branch.

followed by these additions, since the subagent has no channel to the user:

- The seams listed in the spec's Test Seams section are the pre-agreed seams. Any other seam is a question for the user.
- Before starting, note the current `HEAD`. Run `code-review` with that commit as the fixed point and the ticket as the spec, and fix the issues it raises.
- When done, report in this format: `Done: <commit> | files: <changed files> | <one-line summary>`.
- Whenever `implement` would ask the user (an ambiguous ticket, an unconfirmed seam, a ticket that disagrees with the spec or with a file it points to, a choice the spec leaves open), when the Skill tool cannot call `tdd` or `code-review`, or when an environment problem cannot be solved within your permissions (a path, a permission, a failing tool): leave the work uncommitted in the working tree, stop, and report **blocked**: a first line `Blocked: <one-line reason>`, then each question, the options you see and the one you recommend, what is already built, and what each answer changes.

## Questions for the user

A **blocked** report comes back to you. Ask the user its questions, keeping the subagent's options and recommendation, and naming the ticket. The user decides every one of them, environment problems included, even when you could pick an option yourself. Nothing else runs while you wait.

The answers are for the blocked subagent, whatever their wording (an answer like "just do it yourself" still goes to the subagent). With the answers, resume the same subagent if your harness can message it. Otherwise dispatch a new **implementer subagent** for the same ticket, with the answers and a pointer to the uncommitted work in the working tree.

Environment problems you hit yourself go to the user the same way: stop that action, report what failed and the options you see, and let the user decide.
