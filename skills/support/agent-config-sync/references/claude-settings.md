# Claude Code settings.json boundaries

`targets.claude.base` and each overlay's `set` use native Claude Code `settings.json` fields directly. The generator outputs UTF-8,
two-space-indented JSON and adds no tool metadata.

This skill does not manage `~/.claude.json`, credentials, OAuth tokens, project-level settings, hooks, or session data.

The fields below belong to other Claude Code files and must not be written to `settings.json`. The validator reads the list from this section, so updating the fields does not require changing the skill prompt or Python constants.

<!-- rejected-fields:start -->
- `autoConnectIde`
- `autoInstallIdeExtension`
- `diffTool`
- `externalEditorContext`
<!-- rejected-fields:end -->

