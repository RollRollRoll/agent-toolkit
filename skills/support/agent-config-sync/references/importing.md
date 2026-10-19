# Importing existing configuration

## Choose the interaction mode

If the user has not stated a preference, first ask whether to start the local web UI and wait for their choice. If the user agrees, use the UI as the main place for review and decisions. If the user declines, or the UI fails to start, the page is unreachable, or the current environment cannot operate the page, explain why and switch to item-by-item Q&A.
While the UI is available, do not also ask the same decisions in the conversation.

## Two-phase workflow

Pass one or more sources explicitly; the same target can be repeated:

```bash
aiconfig import inspect \
  --source codex=~/.codex/config.toml \
  --source codex=./backup/config.toml \
  --source claude=~/.claude/settings.json
```

By default the command generates `.agent-config/import-plan.yaml`. After reviewing and resolving conflicts, generate the source-of-truth file:

```bash
aiconfig import generate --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

If the user chose the UI, start the local review UI to make item-by-item decisions, preview, and generate:

```bash
aiconfig ui --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

The command prints a local address with a session token. Add `--open` only when the user explicitly asks to open the browser automatically. The UI and manual editing use the same plan format, and the decision rules are identical. For online descriptions, caching, and local security boundaries, see [Local review UI](ui.md).

When falling back to Q&A, show the candidate sources and values for each conflict in the plan's order, wait for the user to explicitly choose `take`, `union`, `set`, or `exclude`, then write the decision back into the plan. Do not decide yourself, and do not merge different arrays automatically.

An existing plan or source-of-truth file is not overwritten by default; use `--force` only with the user's explicit agreement. The first version only merges multiple configs for the same target into `base`. It does not infer overlays, and it does not merge fields across Codex and Claude Code.

## Merging and deduplication

- Objects merge recursively.
- Identical scalars or identical whole arrays are kept once, with all their sources recorded.
- Different scalars, different arrays, or a type mismatch between object and non-object are marked `conflict`.
- Arrays are never unioned automatically, to avoid breaking order-sensitive fields such as command arguments.
- Suspected secrets are marked `sensitive`, and out-of-scope Claude fields are marked `out-of-scope`. Neither writes the original value into the plan, and both are excluded by default.

Config item paths use JSON Pointer, for example `/permissions/allow`. Write `~` in a key as `~0` and `/` as `~1`.

## Decision actions

- `keep`: keep a value that has no conflict.
- `take`: pick one `source` from the conflict candidates.
- `union`: take a stable union of conflicting arrays in source order, removing only exactly identical elements.
- `set`: set the value explicitly with `selectedValue`.
- `exclude`: drop the config item.
- `unresolved`: an unresolved conflict; it blocks generating the source-of-truth file.

Example:

```yaml
- path: /model
  status: conflict
  candidates:
    - sources: [codex-1]
      value: gpt-5
    - sources: [codex-2]
      value: gpt-5.1
  action: take
  source: codex-1
```

Put JSON Pointers in a target's `excludes` to drop a whole subtree:

```yaml
targets:
  codex:
    excludes:
      - /model_providers/custom
```

You can also add exclusions temporarily at generation time:

```bash
aiconfig import generate --exclude codex=/model_providers/custom
```

Never change `sensitive` or `out-of-scope` items to keep. If you need environment variable placeholders, edit `agent-config.yaml` explicitly after the import finishes, then validate again.
