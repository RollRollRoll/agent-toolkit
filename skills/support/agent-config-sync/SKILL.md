---
name: agent-config-sync
description: Extract existing configuration into a single declaration, then use it to safely sync user-level Codex and Claude Code configuration.
---

# Agent Config Sync: two-platform config sync

Treat `agent-config.yaml` as the single source of truth. Generate configuration with the deterministic CLI that ships with this skill. Do not hand-assemble TOML or JSON to overwrite user files.

## Locate the CLI

Prefer the installed `aiconfig`. If the command is not available, run this from the current skill directory:

```bash
python3 scripts/aiconfig.py
```

Every command searches upward from the current directory for `agent-config.yaml` by default. You can also pass `--config <path>`.

## Standard workflow

When extracting facts from existing configuration:

1. If the user has not stated an interaction preference, first ask whether to start the local web UI and wait for their choice. If the user has already said to use or not use the UI, do not ask again.
2. For each file the user explicitly provides, run `aiconfig import inspect --source <target>=<path>`. The same target can be passed more than once.
3. Read the generated `.agent-config/import-plan.yaml` and explain the auto-deduplicated items, conflicts, sensitive fields, and out-of-scope fields.
4. If the user chose the UI, run `aiconfig ui` and use the page as the main place for review and decisions. Give the local address with its session token. Use `--open` only when the user explicitly asks to open the browser automatically. While the page is available, do not also ask item-by-item questions in the conversation.
5. If the user declines the UI, or the UI fails to start, the page is unreachable, or the current environment cannot operate the page, explain why you are falling back and switch to Q&A: show each conflict's candidates one at a time and have the user explicitly choose `take`, `union`,
   `set`, or `exclude`. Do not pick a source yourself or merge different arrays.
6. Write the decisions from the page or the Q&A into the plan, then run `aiconfig import generate`, or let the local UI generate it. Stop if any conflict is unresolved.
7. Run `aiconfig validate` and `aiconfig plan` to confirm the effect of the generated declaration.

`import inspect` only merges multiple configs for the same target. It does not infer multi-machine overlays. Always handle Codex and Claude Code configuration separately.
For the full plan format and decision rules, see [Importing existing configuration](references/importing.md).

For read-only analysis:

1. Run `aiconfig detect`.
2. Run `aiconfig validate`. Stop if it fails.
3. Run `aiconfig plan`.
4. Explain the matched overlays, application order, target paths, diffs, and warnings.

When the user explicitly asks to apply, update, or write:

1. Run `detect`, `validate`, and `plan` in that order.
2. If validation fails, stop and give the error code and a suggested fix.
3. Run `aiconfig apply [codex|claude]`.
4. Run `aiconfig status [codex|claude]`.
5. Report the changed files and backup paths.

Do not run `apply` just because the user asked to "check, compare, or analyze". If a target file has local changes since the last apply, do not add `--force` on your own; explain the conflict and wait for the user's explicit authorization.

## Common tasks

- Initialize a declaration: `aiconfig init`
- Merge existing configuration: `aiconfig import inspect --source codex=<path> --source claude=<path>`
- Generate the declaration from a confirmed plan: `aiconfig import generate`
- Review the import plan visually: `aiconfig ui [--open]`
- Inspect the environment: `aiconfig detect` or `aiconfig detect --json`
- Validate all targets or one target: `aiconfig validate [codex|claude]`
- Render to `.agent-config/generated/`: `aiconfig render [codex|claude]`
- Preview matches and diffs: `aiconfig plan [codex|claude]`
- Apply all targets or one target: `aiconfig apply [codex|claude]`
- Check sync status: `aiconfig status [codex|claude]`

## Configuration boundaries

- Keep the native semantics of `targets.codex` and `targets.claude` separate. Do not invent cross-tool permission mappings.
- Manage only `~/.codex/config.toml` and `~/.claude/settings.json`.
- Do not read, copy, or write tokens, OAuth state, credentials, sessions, caches, logs, or `~/.claude.json`.
- Do not modify project-level `.codex/config.toml` or `.claude/settings.json`.
- Do not continue to apply after validation fails.
- Do not bypass backups, atomic writes, or local-change detection.
- Do not silently overwrite the import plan or an existing `agent-config.yaml`.
- Do not merge different arrays automatically; compute a stable union only after the user explicitly chooses `union`.
- The UI listens only on the loopback address and does not upload configuration. Online field descriptions only read public schemas and never send configuration paths or values.

## Read references as needed

- When writing or explaining a declaration, read [Declaration format](references/declaration-format.md).
- When extracting from existing files, deduplicating, resolving conflicts, or excluding fields, read [Importing existing configuration](references/importing.md).
- When starting the visual review or explaining where online descriptions come from, read [Local review UI](references/ui.md).
- When handling overrides, array operations, or deletions, read [Merge rules](references/merge-rules.md).
- When explaining target boundaries, read [Codex configuration](references/codex-config.md) or [Claude settings](references/claude-settings.md).
- When you hit a stable error code, read [Troubleshooting](references/troubleshooting.md).
