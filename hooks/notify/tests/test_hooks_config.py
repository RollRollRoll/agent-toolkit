from __future__ import annotations

import json
from pathlib import Path

# hooks 配置位于 hooks/ 目录（本文件在 hooks/notify/tests/ 下）
HOOKS_DIR = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((HOOKS_DIR / name).read_text(encoding="utf-8"))


def test_both_hooks_configs_are_valid_json():
    for name in ["hooks.json", "codex-hooks.json"]:
        assert isinstance(_load(name)["hooks"], dict)


def test_claude_notification_matcher_covers_waiting_and_permission_types():
    # REQ-008：Notification matcher 恰好包含四种类型
    entries = _load("hooks.json")["hooks"]["Notification"]
    types = {t for entry in entries for t in entry["matcher"].split("|")}
    assert types == {"idle_prompt", "permission_prompt",
                     "elicitation_dialog", "elicitation_url_dialog"}


def test_claude_hooks_do_not_register_permission_request():
    # NEG-003：Claude Code 插件不注册 PermissionRequest
    assert "PermissionRequest" not in _load("hooks.json")["hooks"]
