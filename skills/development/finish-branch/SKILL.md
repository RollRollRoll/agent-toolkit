---
name: finish-branch
description: "Wrap up the current branch or worktree: clean up debugging leftovers, run final verification, then let the user decide whether to merge, keep, open a PR, or discard."
---

# Finish Branch: Wrapping Up Development

## Goal

After a stretch of development is **implemented**, **wrap up** the current branch / worktree: first run a read-only state preflight, then clean up debugging leftovers and run the final tests,
and finally offer the options "merge / keep locally / create PR / discard", leaving destructive and external actions to the user.

Use it after development is done, to clean up leftovers, run final verification, and decide where the branch goes. Setting up a workspace is not its job.

## Invocation contract

**Inputs**

- **Final verification command**: how to run the project's full acceptance check.
- **Scope of this development** (optional): used to judge which debugging leftovers were introduced by this work; if not given, clean only what can be confirmed.
- **Caller** (optional): when called by another skill, state the caller. If the cleanup produces code changes, control must go back to the caller to redo the overall acceptance check.

**Returns**

- Preflight conclusion (branch / worktree / staged and untracked state, ahead/behind relative to the main branch).
- What was cleaned up, final test results, the wrap-up option the user chose, and **the actions actually taken**.
- For an unauthorized action, stop before it and report truthfully; do not decide for the user.

**Responsibility boundaries**

- Do not wrap up if tests fail. Do not automatically commit / merge / push / open a PR / delete a branch / remove a worktree; get confirmation for each one separately.
- Do not automatically stash, `git clean`, or silently discard to create a "clean state".
- Do not set up a workspace or do code review; this skill only wraps up.

## When to use / when not to use

**Use it when**:

- A stretch of development is done and tests pass, and you need to decide what to do with the branch.
- Wrapping up after the overall acceptance check passes.
- You finished work in a worktree and want to merge it back and clean up the worktree.

**Do not use it when**:

- Development is not finished or tests fail: finish development and fix the tests first, then wrap up.
- You need to set up an isolated workspace: that is not this skill's job.

## Core flow (state preflight → clean up debugging leftovers → final verification → offer options → execute with authorization)

1. **Run a read-only state preflight first**:
   - Confirm the current branch, whether you are in a worktree, and staged / unstaged / untracked state.
   - If there are any non-ignored changes on entry, show a summary and stop, and let the user decide. **Do not clean up, commit, stash, or discard first**, so user changes do not get mixed into the wrap-up.
2. **Clean up debugging leftovers from this development**:
   - Check this diff for temporary logs, debug prints, breakpoints, temporary flags, and code added only to investigate a problem.
   - Clean up only leftovers you can confirm this development introduced. When the purpose is unclear, ask the user first; do not touch unrelated code along the way.
   - Cleanup must happen before the final tests, so a "green before cleanup" result is not taken as the final result.
3. **Run the final tests and confirm all green**: run the full acceptance check the project defines. **Not green, no wrap-up**: go back and fix, then rerun the final tests.
4. **Recheck repo / worktree state**:
   - If cleanup produced changes, show the diff and get explicit commit authorization before committing; after committing, confirm the state is clean again.
   - If cleanup produced code changes, control must go back to the caller to redo the overall acceptance check; the review conclusion from before cleanup cannot be reused.
   - Relationship to the main branch (how many commits ahead / behind).
5. **Offer the wrap-up options**:
   - **Merge to main**: merge back into the main branch.
   - **Keep locally**: leave it on the branch, do not merge yet.
   - **Create PR**: push and open a PR; write the PR body by invoking `pr` with the Skill tool.
   - **Discard**: abandon this work (delete the branch / worktree). **Irreversible**.
6. **Execute after getting the matching authorization**:
   - `git commit`, merge, push, creating a PR, and deleting a branch all need the user's explicit confirmation of the specific action before running.
   - Even if the code is merged or discarding is decided, `git worktree remove` needs separate confirmation; do not read "chose merge" as also authorizing removal of the worktree.
   - For keep locally, only report the branch / worktree path and state; do not make implicit commits or cleanups.

## Safety gates

- **⚠️ State changes need explicit user confirmation, never automatic**: commit, merge, push, create PR, delete branch, discard, remove worktree. Follow the current repo's `CLAUDE.md` / `AGENTS.md` and the platform's approval policy.
- **No wrap-up if tests fail**: go back and get them green first.
- **Tests must come after debug cleanup**: any cleanup or fix invalidates earlier test results, so rerun them.
- **The overall acceptance check also goes stale**: if cleanup produces code changes after the overall acceptance check passed, review again.
- **Discarding is irreversible**: **confirm twice** before deleting a branch; also get explicit confirmation before removing a worktree.
- **Detect before acting**: acting before the state is clear (wrong branch, missed uncommitted changes) can cause damage.
- **No implicit fallbacks**: do not use automatic stash, automatic commits, `git clean`, or silent discards to create a "clean state".

> Check: does every commit, merge, push, PR, deletion, or worktree removal you are about to run have explicit authorization for that action? If one is missing, stop before it.

## Common mistakes

- Wrapping up / merging when tests fail.
- Running tests first, deleting debug prints afterwards, and not rerunning tests.
- Starting cleanup when there were dirty changes on entry, mixing user changes into the wrap-up.
- Changing code after the overall acceptance check and then merging on the old review conclusion.
- Finding uncommitted changes and automatically committing / stashing to keep the flow going.
- Automatically merging / pushing / opening a PR without letting the user decide (dangerous operation).
- Removing the worktree after the merge is approved: the user only confirmed the merge, not the removal.
- Discarding (deleting the branch) without a second confirmation.
- Acting without checking state: on the wrong branch / missing uncommitted changes.
- Setting up a workspace here: out of scope, this skill only wraps up.
