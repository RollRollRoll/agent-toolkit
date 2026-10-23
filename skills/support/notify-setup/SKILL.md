---
name: notify-setup
description: Walk the user through configuring the agent-notify Telegram bot token and chat_id with an interactive wizard. Use when the user wants to set up, configure, or reconfigure agent notifications.
---

# Notify Setup

The wizard reads the bot token with hidden input, so it needs a real terminal. Do not run it yourself, and never ask the user to paste the token into the conversation.

1. Resolve the absolute path of `notify/bin/notify-setup.py`. The plugin root is two levels above this skill's directory (`skills/support/notify-setup` → plugin root).
2. Tell the user to run it in their own terminal window:

   ```bash
   python3 "<absolute path>/notify/bin/notify-setup.py"
   ```

3. Explain what the wizard will do:
   - ask for the token from @BotFather and validate it;
   - ask them to message the bot, then detect the chat_id (they can also type one);
   - write `~/.config/agent-notify/config.json` with permission 600, keeping other settings;
   - send a test notification.
4. After they finish, offer to run `notify-test` to confirm delivery.

If the wizard reports a network error, suggest checking the network or proxy. If it reports `Unauthorized`, the token is wrong.
