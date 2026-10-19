---
name: git-commit-push
description: Resolve an in-progress git merge, rebase, or cherry-pick conflict, or organize finished changes into atomic commits and push them after the user confirms.
---

# Git Commit & Push: Conflict Resolution, Commit, and Push

## Goal

Safely finish two related kinds of work:

- For an in-progress merge / rebase / cherry-pick, find the original intent of both sides of each conflict, merge each one semantically, verify, and continue the operation after confirmation.
- For ordinary working-tree changes, organize them into one or more commits that each hold a **single logical change**, so every commit runs, can be reviewed, and can be reverted. Then push the confirmed commits to the remote the user names.

Only handle **conflict operations that have already started**, commits, and pushes. Do not start or abort a merge / rebase / cherry-pick yourself. Do not also create a PR, clean up the working tree, widen the implementation scope, or rewrite published history.

## Invocation contract

This is a capability unit of agent-toolkit. The user can trigger it directly, and other skills can call it.

**Inputs**

- **Target action**: resolve an in-progress conflict / commit / push (can be combined).
- **Target remote and branch**: required when there are several remotes. Do not push to all of them by default.
- **Verification commands** (optional): the tests, build, or static checks to run for each commit batch.

**Returns**

- Current branch and final working-tree state; the conflict operation type, resolved files, and key intent trade-offs.
- Short ID and subject of each new commit, and the push result for each remote.
- What is uncommitted / unpushed / unverified / excluded, and any `.gitignore` entries suggested but not yet handled.

**Responsibility boundaries**

- Do not start or abort a merge / rebase / cherry-pick; do not force-push or rewrite published history; do not create PRs or clean up the working tree.
- Do not automatically stash, discard, or overwrite user changes; do not run commit / push / continue before confirmation.

**Boundary**: during development, the "after each task, commit code + tests + progress together atomically" step is the caller's own gate action.
The caller does it itself, not through this skill. This skill is for standalone batched commits, pushes, and resolving in-progress conflicts.

## Workflow

### 1. Read-only preflight

First read the applicable `AGENTS.md`, `CLAUDE.md`, contribution guide, and commit conventions in the repo, then check:

- Confirm you are in a Git repository and get the repository root.
- Use `git status --short --branch` to check staged, unstaged, untracked, and branch state.
- Use `git branch --show-current` to confirm the current branch. If HEAD is detached, decide whether a recognized rebase caused it; for any other detached HEAD state, stop and let the user choose the target branch.
- Use `git diff --name-only --diff-filter=U`, `git ls-files -u`, and `git status` to check for unresolved conflicts and identify an in-progress merge,
  rebase, or cherry-pick.
- Use `git remote -v`, the branch upstream, and push config to identify available remotes; do not guess the target from the remote name alone.
- Check whether the current branch is ahead of or behind its locally known upstream, and note that remote-tracking info may not be fresh.

Route on the preflight result:

- Unmerged entries or a recognized in-progress operation exist: if the user explicitly asked to resolve conflicts, read and follow the whole [conflict resolution process](references/conflict-resolution.md). If the user only asked to commit or push,
  first report the operation type and conflicting files, and get permission to extend the scope to conflict resolution before editing.
- Unmerged entries exist but no matching operation can be identified: stop and ask where these entries came from. Do not guess which Git operation to continue.
- No in-progress operation, but the locally known upstream is ahead of the current branch: stop and let the user choose how to integrate. Do not pull, merge, or rebase automatically.
- No conflicts: go on to review the candidate content.

If Git has already created merge / rebase / cherry-pick commits when the conflict process finishes, do not wrap them again in duplicate commits. If the user also asked to push, go straight to safe push; otherwise report the result and stop.
If separate ordinary working-tree changes remain after the operation finishes, send only those remaining changes into the commit process below.

### 2. Review all candidate content

Review staged, unstaged, and untracked content together; do not look at `git diff` alone. Keep the staging state you found on entry. Do not automatically unstage,
stash, discard, or overwrite user changes.

Check in particular:

- **Sensitive data**: keys, tokens, passwords, private keys, certificates, connection strings, `.env`, credential files, and config containing secrets.
- **Junk content**: logs, caches, temp files, editor files, build output, coverage results, and large files generated by accident.
- **Unrelated changes**: changes outside this goal, of unknown origin, or that the user already had.
- **Unusual diffs**: large-scale reformatting, whole-file line-ending changes, unexpected binary files, renames, or deletions.
- **Line endings and permissions**: use `.gitattributes`, `git ls-files --eol`, `git diff --summary`, and
  `git diff --check` to check EOL, executable bits, and file mode changes.

Never show secret values in output; report only the file path, suspected type, and suggested handling. When you find sensitive data, stop immediately and do not stage or commit:

1. Tell the user to remove or replace the secret, and rotate exposed credentials as needed.
2. Suggest adding local secret files and junk output to `.gitignore`.
3. If the file is already tracked by Git, state clearly that adding it to `.gitignore` alone will not stop tracking it, and ask the user how to handle it.
4. If the secret may already be in history, explain that cleaning history is a separate high-risk task; do not do it automatically in this skill.

For generated files or permission changes that may legitimately belong in version control, do not exclude them on your own judgment; confirm intent with the user first.

### 3. Design atomic commits

Group by "purpose of the change", not by file type. Code, its tests, and necessary docs usually belong in the same logical commit.

Every planned commit must:

- Express only one complete, self-contained, easy-to-understand logical change.
- Build and run without depending on later changes that are not yet committed.
- Be reviewable on its own, and revertible on its own when needed.
- Include the tests or verification that prove the change; when it cannot be verified, state why.

If the candidate changes contain different implementation logic, split them into several commits. If one file mixes several logical changes, stage exact hunks. If they cannot be split safely,
stop and explain the blocker. Do not rewrite user code just to get atomic commits. Do not blindly use `git add .` or `git add -A`.

For each batch, give:

1. Purpose of the change.
2. Files or hunks included.
3. Proposed commit subject; for complex commits, also the body.
4. Matching verification command.

### 4. Write commit messages

Follow the repo's existing commit conventions first. If the repo has none, use a short, clear, searchable subject that states directly "what was done" and why.
Use the Conventional Commits format only when the repo already uses it.

Avoid vague descriptions such as `update`, `fix bug`, `misc changes`, `tweak code`. Complex commits must have a body that gives at least two of the following:
background / reason, key implementation decisions, behavior impact or compatibility, risks and how it was verified. The body explains "why";
do not repeat the diff's file list.

Example:

```text
fix(config): avoid overwriting existing settings when fields are missing

When importing a partial config, update only the explicitly declared fields
and keep local settings that are not declared. This prevents cross-device
sync from accidentally wiping platform-specific settings.
```

### 5. Get one explicit authorization

Before any `git merge --continue`, `git rebase --continue`, `git cherry-pick --continue`,
`git commit`, or `git push`, show the user and confirm:

- The current branch.
- If in the conflict process: the operation type, the intent judgment and resolution for each conflict, trade-offs, verification results, and the continue command to be run.
- Each commit batch with its full commit message.
- The verification to be run and what remains unverified.
- Target remote, source branch, and target branch.
- Whether an upstream needs to be set.

One confirmation can cover a fully listed sequence of operations. If a new conflict appears after continuing a rebase / cherry-pick, or the scope, a resolution decision, a commit message, the branch, or the remote changes, confirm again. The current confirmation cannot cover conflicts that have not appeared yet.

When there are several remotes, you must ask which remote or remotes to push to; never push to all by default. The same goes for pull: run it only when the user explicitly asks to pull,
and first have the user choose the exact remote and branch. Do not use a pull with an implicit source, and do not merge several remotes automatically.

### 6. Stage, verify, and commit batch by batch

For each approved batch, in order:

1. Stage only the explicit paths or hunks of that batch.
2. Use `git diff --cached --stat`, `git diff --cached --summary`,
   `git diff --cached --check`, and the full staged diff to recheck the scope.
3. Confirm again that the index has no secrets, junk files, unusual EOL / permissions, and no logical changes from other batches.
4. Run the relevant tests, build, or static checks for the batch. If the test environment contains later uncommitted changes, state that the verification is not isolated,
   and do not claim the commit was verified on its own.
5. Create the commit only after the checks pass, then check the commit ID, subject, and remaining working-tree state.

If the staged content does not match the approved plan, stop and show the diff again. If verification fails, do not commit a "red" state and do not change the implementation on your own;
report the failure and let the user decide whether to go back to development or adjust the scope.

### 7. Safe push

Before pushing, recheck the current branch, upstream, commits to push, and working-tree state. Use commands with an explicit remote and refspec, and avoid bare
`git push`, which can trigger unexpected config. When there is no upstream, set one only after the user confirms.

- Do not push tags, other branches, or all remotes by default.
- Push to several approved remotes in order and record success or failure for each. On partial success, report it as it is; do not rewrite remotes that already succeeded.
- When a push is rejected for non-fast-forward, remote updates, or policy, stop immediately. Ask the user to choose and finish an integration step such as merge / rebase first.
  Do not pull, merge, rebase, or force-push automatically.
- Do not use `--force` or `--force-with-lease`. Any history rewrite must leave this process and be assessed and authorized explicitly as a separate high-risk task.
- If, after a rebase is resolved, the remote branch can only be updated by force-push, report the finished local state and the push blocker, then stop. Do not infer force-push permission from the rebase permission.
- When a pushed commit needs fixing, create a new fix commit by default; do not use amend, reset, or rebase to rewrite published history.

### 8. Report the result

When done, report:

- Current branch and final working-tree state.
- Conflict operation type, resolved files, key intent trade-offs, and whether the merge / rebase / cherry-pick finished.
- Short ID and subject of each new commit.
- Push result and target ref for each remote.
- What is uncommitted, unpushed, unverified, or excluded.
- Files or patterns suggested for `.gitignore` but not yet handled.

Never treat a successful commit as a successful push, and never report a blanket "done" when something partly failed.

## Safety boundaries

- Do not commit or output sensitive data.
- Do not put different implementation logic into one commit.
- Do not replace semantic judgment with deleting conflict markers, taking `ours` / `theirs` for whole files, or making the tests pass.
- Do not automatically start, skip, or abort a merge / rebase / cherry-pick; when the user asks for one of these, explain the impact separately and get authorization.
- Do not run any continue command before the user confirms the resolution summary and verification results.
- Do not automatically stash, discard, clean, or overwrite user changes.
- Do not change history that has already been pushed, and do not force-push.
- Do not commit or push before the user confirms the current branch, commit batches, and remote target.
