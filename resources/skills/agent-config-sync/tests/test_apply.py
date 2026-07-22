import json
from pathlib import Path

import pytest
import tomlkit

from aiconfig.errors import ConfigError
from aiconfig.state import hash_text
from aiconfig.writer import apply_content


def test_apply_creates_backup_and_preserves_valid_output(tmp_path):
    target = tmp_path / ".codex" / "config.toml"
    target.parent.mkdir()
    old = 'model = "old"\n'
    new = 'model = "new"\n'
    target.write_text(old, encoding="utf-8")
    state = {"targets": {"codex": {"generatedHash": hash_text(old)}}}

    backup = apply_content(
        "codex",
        target,
        new,
        state,
        tmp_path / "backups",
        tomlkit.parse,
        force=False,
    )
    assert backup is not None and backup.read_text(encoding="utf-8") == old
    assert target.read_text(encoding="utf-8") == new


def test_apply_refuses_manual_modification_unless_forced(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text('{"mode": "manual"}\n', encoding="utf-8")
    state = {"targets": {"claude": {"generatedHash": hash_text('{"mode": "generated"}\n')}}}

    with pytest.raises(ConfigError) as caught:
        apply_content("claude", target, '{}\n', state, tmp_path / "backups", json.loads, force=False)
    assert caught.value.code == "TARGET_FILE_MODIFIED"
    assert json.loads(target.read_text(encoding="utf-8"))["mode"] == "manual"

    apply_content("claude", target, '{}\n', state, tmp_path / "backups", json.loads, force=True)
    assert json.loads(target.read_text(encoding="utf-8")) == {}

