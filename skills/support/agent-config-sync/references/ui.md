# Local review UI

## Default interaction entry point

If the user has not stated a preference, first ask whether to start the local web UI and wait for their choice. If the user agrees, start the UI and use it as the main place to work; while the page is available, do not also ask item-by-item questions in the conversation. Use `--open` only when the user explicitly wants the browser opened automatically.

If the user declines, or the UI fails to start, the page is unreachable, or the current environment cannot operate the page, briefly explain why and fall back to item-by-item Q&A. Do not keep retrying the UI. The Q&A uses the same `keep`, `take`, `union`, `set`,
`exclude` decision rules as the UI.

Generate the import plan first, then start the UI:

```bash
aiconfig import inspect \
  --source codex=~/.codex/config.toml \
  --source claude=~/.claude/settings.json
aiconfig ui --plan .agent-config/import-plan.yaml --output agent-config.yaml
```

The UI can:

- Show all sources, auto-deduplicated results, conflicts, sensitive fields, and out-of-scope fields.
- Filter by target and status, and choose `keep`, `take`, `union`, `set`, or `exclude` item by item.
- Suggest keeping or excluding an item, with a reason, based on its status, local paths, and schema defaults, without changing the user's decisions automatically. For conflicts it only suggests resolving the conflict first; it does not pick a source for the user.
- On desktop, keep the details panel on the right within the current viewport while the config item list scrolls; selecting an item does not jump the page back to the top of the details area.
- Write decisions back into the import plan immediately, and once all conflicts are resolved, preview the source-of-truth YAML, Codex TOML, and Claude JSON.
- Download the preview, or generate `agent-config.yaml`. An existing file needs a second confirmation and is backed up automatically before being overwritten.
- Fetch field descriptions, types, allowed values, and defaults online from the Codex and Claude Code config schemas.

## Network and caching

- Codex schema: `https://developers.openai.com/codex/config-schema.json`
- Claude Code schema: `https://json.schemastore.org/claude-code-settings.json`
- Schemas are cached for 24 hours by default, at `~/.config/aiconfig/docs-cache.json`.
- If a refresh fails but an old cache exists, the UI marks it "离线缓存" (offline cache). With no cache, it shows an error and does not make up field descriptions.
- Clicking an official schema link opens an external web page, but the URL never carries config paths or config values.

## Local security boundaries

The server listens only on `127.0.0.1` and generates a random session token on every start. Once the token reaches the browser, it is stored in the current tab's session and removed from the address bar; every local API requires the token. UI assets do not depend on a CDN, the import plan is never uploaded, and there is no remote deployment mode.

The default port is `8765`. On a port conflict you can choose another port, or use `--port 0` to assign one automatically. Press `Ctrl-C` to stop the server. Use `--open` only when the user explicitly wants the browser opened.
