# Resolving an in-progress Git conflict

Use this process only when a merge, rebase, or cherry-pick is already in progress and the user has authorized resolving the conflicts. The goal is to preserve the original intent of both sides, not to get rid of the conflict markers as fast as possible.

## 1. See the current state and the goal

First record these facts:

- `git status --short --branch` and the full `git status`.
- The conflicting files listed by `git diff --name-only --diff-filter=U`.
- Which of stage 1 (common base), stage 2 (ours), and stage 3 (theirs) actually exist for each path in `git ls-files -u`. Delete/modify,
  rename, and add/add conflicts do not necessarily have all three stages.
- The current `HEAD`, and `MERGE_HEAD`, `REBASE_HEAD`, `CHERRY_PICK_HEAD` when they exist.
- The goal of the operation, as stated in the user's original command or in the current conversation.

Identify the operation state in `.git` read-only. Do not edit internal control files such as the sequencer, the rebase todo, or MERGE_MSG.

If you cannot determine the operation type or goal, tell the user the evidence and the gaps first. Without a goal ("what is this merge / rebase meant to achieve"), there is no basis for choosing between incompatible intents.

## 2. Find the primary sources for each conflict

Understand deeply why each change was made, and what the original intent was. Build a short decision record for each conflicting path:

1. Look at the actual content of the common base, ours, and theirs. Use `git show :1:<path>`, `:2:<path>`, `:3:<path>` when needed, and do not assume all three stages exist.
2. Read the related commit messages (subject and body), the path history, blame where needed, and the diffs that introduced each side's change. When the commit messages do not explain enough, check the PRs, the original issues/tickets, design docs, or specs.
3. Write down separately, for each side, what behavior it changed, why, and which nearby code and tests it depends on.
4. Decide whether the conflict is content, delete/modify, rename, file path move, generated file, or add/add. A file-level conflict cannot be handled only as text hunks.

Watch the meaning of ours / theirs:

- In a merge, ours is usually the current `HEAD`, and theirs is the side being merged in.
- In a rebase, ours is usually the side being rebased onto, and theirs is the commit currently being replayed. Do not treat "ours is the user's branch" as a general rule.

Prefer the primary source that owns the intent. When you find no basis, keep the uncertainty and let the user choose. Do not use "the code looks newer", "the commit is later", or "it changes more" as a reason to pick a side.

## 3. Resolve each hunk semantically

Resolve each hunk in this order of priority:

1. Preserve both intents where possible: combine them into the smallest result that serves both purposes.
2. Where incompatible, pick the one matching the stated goal of this merge / rebase / cherry-pick and note the trade-off.
3. When the evidence cannot decide, stop on that hunk and ask the user. Do **not** invent new behaviour.

While editing:

- Change only the conflict and the code directly needed to integrate it. Do not refactor nearby code while you are there.
- Do not overwrite whole files with `--ours` or `--theirs` unless the intent evidence clearly requires taking one side for the whole file.
- After removing the conflict markers, reread the full function, type, config section, and nearby tests. Text that parses does not mean the semantics are merged.
- For a delete/modify conflict, check which still holds: the reason for the deletion or the purpose of the modification. If the modification needs to move, move its intent to the new authoritative location instead of mechanically keeping the old file.
- For a generated file, first confirm the repo's generation source and generation command. Change the source, then regenerate following the project's process; do not hand-splice the output.

After resolving each file:

1. Check for leftover conflict markers. If the file legitimately contains similar text, tell them apart by hand.
2. Look at the full file and its diff against the common base, and check that both intents in the decision record are covered.
3. Stage only this checked path. Do not use `git add .` or `git add -A`.
4. Confirm `git ls-files -u -- <path>` has no entries before moving to the next file.

## 4. Verify the merged behavior as a whole

After all files are resolved, first confirm:

- `git diff --name-only --diff-filter=U` and `git ls-files -u` are both empty.
- The staged diff contains only conflict resolutions and necessary integration changes, and has not swallowed unrelated changes from one side.
- Key callers, types, config references, renamed paths, and tests are consistent with the new overall state.

Discover the project's **automated checks** and run them, typically typecheck, then targeted tests, affected tests, the full test suite, and format. If formatting changes files, review the diff again and rerun the affected checks.

Fix only problems caused directly by integrating the conflict (anything the merge broke). If verification exposes a new feature need unrelated to either side's original intent, stop and report it as a follow-up ordinary change; do not fold it into the conflict resolution.

If tests fail, dependencies are missing, or the environment is unavailable, report the actual command, the cause of the error, and what was not verified. Do not describe "no conflict entries left" as the resolution being correct.

## 5. Confirm and continue the Git operation

Before running continue, show the user:

- The current operation type and goal.
- For each file, the intent adopted, how compatible intents were combined, and the trade-offs for incompatible ones.
- The scope of the staged diff.
- The checks that were run and their results, and what was not verified.
- The exact command about to run: `git merge --continue`, `git rebase --continue`, or `git cherry-pick --continue`.
- The possible effect on the commit sequence, branch history, and later pushes.

After explicit confirmation, run only the continue command that matches the current state. Do not use a plain `git commit` to bypass the rebase / cherry-pick sequencer.

After continuing, rerun this process's state checks:

- If new conflicts appear, start again from step 1, and get confirmation again for the new resolution.
- When the operation finishes, check the final `git status`, the commit history, and how far the branch is ahead / behind.
- If pushing after a rebase would need a force push, stop and report it; this skill does not force push.

Do not run `--abort`, `--skip`, reset, or an overwriting checkout on your own. If the user asks for one of these, treat it as a new high-risk operation: explain what will be discarded or skipped and get separate confirmation.
