---
name: notify-test
description: Send a test Telegram notification through the agent-notify hooks and report whether the token and chat_id work. Use when the user asks to test or verify agent notifications.
---

# Notify Test

Run the bundled test command and relay its output to the user:

```bash
python3 "<plugin root>/notify/bin/notify-test.py"
```

`<plugin root>` is the directory three levels above this skill (`skills/support/notify-test` → plugin root).

- Exit 0 with `✅`: the notification was delivered.
- Exit 1 with `❌`: show the reason. If credentials are missing or wrong, suggest `notify-setup`. Never print the token.
