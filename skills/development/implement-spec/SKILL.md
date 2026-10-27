---
name: implement-spec
description: "Implement the result of to-spec and to-tickets in code."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `setup-env`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency. They have no channel to the user: their questions come back to you as a **blocked** report (see [Questions for the user](#questions-for-the-user)).

## Steps

1. Read the spec and tickets to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. For each ticket on the **frontier**, create a worktree on its own branch from the integration branch tip, inside the repo under `.worktrees/`, and dispatch an **implementer subagent** into it. `.worktrees/` stays untracked in the main checkout, so stage files by name whenever you commit there. Brief it with pointers to the spec and its ticket, and with the workflow in [Implementer subagents](#implementer-subagents).

5. When an **implementer subagent** reports **blocked**, relay its questions as described in [Questions for the user](#questions-for-the-user). When it reports done, fast-forward the integration branch onto its branch (`git merge --ff-only`). If the integration branch has moved since the subagent merged it, the fast-forward fails: [resume](#resuming-an-implementer-subagent) the same subagent to redo its merge step, and hold every other merge until it reports done and you fast-forward. After each fast-forward, tell every running **implementer subagent** that the integration branch has moved, so its merge step picks up the new tip.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer subagent**, with the review findings in place of a ticket.

8. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.

## Implementer subagents

Each **implementer subagent** builds one ticket in its own worktree:

1. Confirm the worktree is based on the integration branch tip, and reset onto it if not. Note that commit: it is the fixed point for its own `code-review` below.
2. Fetch the ticket from the issue tracker and state its title before starting.
3. Call the Skill tool with `tdd` to build the ticket. The seams listed in the spec's Test Seams section count as already confirmed with the user. Any other seam is a question for the user.
4. Run typechecking regularly, single test files regularly, and the full test suite once at the end.
5. Call the Skill tool with `code-review`, using the commit from step 1 as the fixed point and the ticket as the spec. Fix the issues it raises.
6. Commit to its own branch, then merge the integration branch tip into it, resolving any conflicts and rerunning the full test suite if the merge brought in changes.
7. Report done: the branch name and a one-line summary.

Whenever a step needs a decision from the user (an unconfirmed seam, an ambiguous ticket, a ticket that disagrees with the spec or with a file it points to, a choice the spec leaves open), or hits an environment problem it cannot solve within its permissions (a path, a permission, a failing tool), the subagent commits its work in progress to its branch, stops, and reports **blocked** with:

- each question, with the options it sees and the one it recommends;
- what is already built, and what each answer changes.

## Questions for the user

A **blocked** report comes back to you. Ask the user its questions, keeping the subagent's options and recommendation, and naming the ticket each question belongs to. The user decides every one of them, environment problems included, even when you could pick an option yourself. When several subagents are blocked at once, ask their questions together. The other **implementer subagents** keep running while you wait.

With the answers, [resume](#resuming-an-implementer-subagent) the subagent.

If an answer applies beyond its ticket, add it to the brief of every **implementer subagent** dispatched after it.

Environment problems you hit yourself (a denied write, a failed cleanup) go to the user the same way: stop that action, report what failed and the options you see, and let the user decide.

## Resuming an implementer subagent

Resume the same subagent if your harness can message a running or finished subagent. Otherwise dispatch a new **implementer subagent** into the same worktree, with what it needs to continue (the user's answers, or the step to redo) and a pointer to the commits already on its branch.
