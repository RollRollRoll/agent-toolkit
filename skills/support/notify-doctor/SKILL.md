---
name: notify-doctor
description: Diagnose why agent-notify Telegram notifications are not arriving by checking config, credentials, logs, and Bot reachability. Use when the user says notifications don't work, asks to diagnose or check agent notifications, or wants to see the effective notify config.
---

# Notify Doctor

Run the bundled diagnostic command and relay its output to the user:

```bash
python3 "<plugin root>/hooks/notify/bin/notify-doctor.py"
```

`<plugin root>` is the directory three levels above this skill (`skills/support/notify-doctor` → plugin root).

- Add `--offline` when the user asks for no network access; it skips `getMe` / `getChat`.
- The command is read-only: it never writes config and never sends a chat message.
- Exit 0: no `❌`. Exit 1: at least one `❌`. Relay each `⚠️` / `❌` line with the `→` fix hint under it.
- The output already masks the token. Never ask for or print the full token; for credential fixes, point to `notify-setup`.
