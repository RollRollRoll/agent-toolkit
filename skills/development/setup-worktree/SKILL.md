---
name: setup-worktree
description: Create and verify an isolated Git worktree, locking the base commit explicitly before creating it.
---

# Setup Worktree: Workspace Isolation

## Goal

Before starting a stretch of development, or running several tasks in parallel, **set up an isolated git workspace (worktree)** so the work happens in
a separate directory with an isolated checkout (and its own branch when needed). It does not pollute the current workspace and makes parallel lines of development easier.

Any situation that needs an isolated workspace can call it. Its job is limited to setting up and verifying the isolated environment;
it is not responsible for later cleanup or wrap-up.

## Invocation contract

**Inputs**

- **expected base** (optional): the required starting commit. If not given, use the current local `HEAD`; do not switch to the remote default branch on your own.
- **Purpose / naming hint**: the related task or feature name, used to name the branch and worktree directory so they are easy to recognize and clean up later.
- **Whether a separate branch is needed**: just an isolated checkout, or a long-lived branch.

**Returns**

- Worktree path, HEAD state (branch name or detached), **the full commit ID verified to equal the expected base**, and platform.
- If verification fails or the workspace has uncommitted changes, return **BLOCKED**: report actual and expected values and hand it to the caller / user.

**Responsibility boundaries**

- Do not automatically stash / commit / discard uncommitted changes in the current workspace.
- Do not merge, clean up, or remove worktrees; this skill only sets up isolation.
- Do not write business code or run tests.

## When to use / when not to use

**Use it when**:

- Starting a stretch of development that you want isolated in a clean workspace (not mixed with current uncommitted changes).
- Running several tasks in parallel, where each needs its own isolation and must not touch the others' files.
- Maintaining several lines of development at once (several worktrees).

**Do not use it when**:

- The change is small and needs no isolation: just work in the current workspace.
- The job is wrap-up / merge / deleting a worktree: that is not this skill's job.
- You are not in a git repository: worktrees are a git feature, so confirm it is a git repository first.

## Core flow (detect → lock base → create → verify)

1. **Detect the current state**:
   - In a git repository? No: say it does not apply, stop.
   - **Already in a suitable isolated environment?** Yes: do not create another; still check that the current `HEAD` is the base the caller asked for.
   - Any uncommitted changes (including untracked files)? Yes: **stop creating and have the user handle them first**. Do not automatically stash, commit, or discard them, and do not assume the new worktree will carry these changes.
2. **Lock the expected base**:
   - When the caller gives a base explicitly, use the commit the caller gave.
   - When not given, record the full commit ID of the current local `HEAD` with `git rev-parse HEAD`; use this local `HEAD` as the base by default and do not switch to the remote default branch on your own.
   - Parallel tasks must each record their expected base; if a batch of tasks must share the same origin, all worktrees use the same commit ID.
3. **Pick a creation method per platform that guarantees the expected base**:
   - Use the platform's native tool only when it **is guaranteed to create from the expected base**; when you cannot confirm its semantics, fall back to the explicit command:
     `git worktree add -b <branch-name> <path> <expected-base>`.
   - **Claude Code**: respect the `worktree.baseRef` semantics. The default `fresh` creates from the `origin` default branch; only `head` creates from the local `HEAD`.
     This setting affects `--worktree`, `EnterWorktree`, and subagent isolation alike. When the expected base is the local `HEAD`,
     do not treat the default `fresh` as equivalent, and do not change the user's settings on your own.
   - **Codex App**: a managed Worktree is created from the `HEAD` of the branch chosen in a new task and starts in detached HEAD by default.
     Before creating, have the user choose `Worktree` and the starting branch in the composer, or use Handoff in an existing task. Use this path only when the chosen branch's `HEAD` equals the expected base;
     after creating, verify with the real commit ID, and do not skip verification because of the branch name shown in the UI. When a long-lived branch is needed, use `Create branch here` after verification; do not report the default detached HEAD as a separate branch.
   - **Codex CLI / IDE**: do not assume Codex App's managed Worktree/Handoff exists; when isolation is needed, use an explicit `git worktree add`.
     Codex App's `.worktreeinclude` is only for copying local files that Git ignores and that are really needed. Do not use it to carry ordinary uncommitted changes, and do not add credential files without the user's consent.
   - Record **platform, worktree path, HEAD state (detached or branch name), and expected base** for later verification and cleanup.
4. **Verify after creating; do not start work until it passes**:
   - Run `git rev-parse HEAD` in the new worktree; the result must exactly match the expected base's commit ID.
   - Confirm the new worktree is clean and the original workspace was not changed; for a Codex App managed Worktree, also record whether it is detached HEAD.
   - If HEAD does not match: **stop, make no code changes, and do not silently fix it with rebase / reset**; report actual and expected values and let the user decide what to do next.

> Check: is the new worktree in a separate directory, with `HEAD == expected base`, a clear HEAD state, and both old and new workspaces clean? Isolation holds only when all of these are true.

## Notes

- **Detect before creating**: if you are already in a suitable worktree, do not create a nested one.
- **Base semantics come first**: native platform tools and manual commands are just means; whether you land exactly on the expected base is what decides the choice.
- **Do not mix platforms**: handle Claude Code's `EnterWorktree/worktree.baseRef`, Codex App's Worktree/Handoff, and
  Codex CLI's explicit Git commands separately; do not interpret one platform's parameters in terms of another.
- **Traceable names**: name the branch / worktree path after the related task / feature so it is easy to recognize and clean up later.
- **Do not carry dirty changes**: do not automatically stash, commit, or copy uncommitted changes from the current workspace.
- **Do not clean up here**: removing / merging the worktree when done goes back to the caller; get the user's explicit confirmation before removing a worktree.

## Common mistakes

- Creating without detecting: nesting a worktree inside an existing worktree.
- Seeing `EnterWorktree` and calling it directly without confirming which commit it creates from.
- In Codex App, looking only at the starting branch name and not checking the managed Worktree's real `HEAD`.
- Describing Codex App's default detached HEAD as a separate branch already created.
- Automatically stashing / committing when the current workspace has uncommitted changes, then continuing to create.
- Not checking `HEAD` after creating, so the task starts on the wrong base.
- Merging / deleting worktrees / cleaning up here: out of scope, this skill only sets up isolation.
- Forcing a worktree in a non-git directory.
- Forcing a worktree for a small change: if it needs no isolation, do not isolate (YAGNI).
