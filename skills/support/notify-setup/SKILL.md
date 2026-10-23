---
name: notify-setup
description: Walk the user through configuring the agent-notify Telegram bot token and chat_id with an interactive wizard. Use when the user wants to set up, configure, or reconfigure agent notifications.
---

# Notify Setup

The wizard reads the bot token with hidden input, so it needs a real terminal. Do not run it yourself, and never ask the user to paste the token into the conversation.

1. Resolve the absolute path of `notify/bin/notify-setup.py`. The plugin root is three levels above this skill's directory (`skills/support/notify-setup` → plugin root).
2. Tell the user to run it in their own terminal window:

   ```bash
   python3 "<absolute path>/notify/bin/notify-setup.py"
   ```

   The wizard explains each step itself; don't repeat its prompts here.
3. After they finish, offer to run `notify-test` to confirm delivery.
