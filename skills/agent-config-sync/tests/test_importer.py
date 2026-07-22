import json

import pytest
import yaml

from aiconfig.cli import main
from aiconfig.errors import ConfigError
from aiconfig.importer import build_import_plan, declaration_from_import_plan


def _item(plan, target, path):
    return next(item for item in plan["targets"][target]["items"] if item["path"] == path)


def test_multiple_sources_merge_objects_and_deduplicate_equal_values(tmp_path):
    first = tmp_path / "first.toml"
    second = tmp_path / "second.toml"
    first.write_text('approval_policy = "on-request"\n[sandbox]\nenabled = true\n', encoding="utf-8")
    second.write_text('approval_policy = "on-request"\n[sandbox]\nmode = "strict"\n', encoding="utf-8")

    plan = build_import_plan([("codex", first), ("codex", second)])

    approval = _item(plan, "codex", "/approval_policy")
    assert approval["status"] == "duplicate"
    assert approval["action"] == "keep"
    assert approval["sources"] == ["codex-1", "codex-2"]

    declaration = declaration_from_import_plan(plan)
    assert declaration["targets"]["codex"]["base"] == {
        "approval_policy": "on-request",
        "sandbox": {"enabled": True, "mode": "strict"},
    }


def test_different_scalars_and_arrays_require_explicit_decisions(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps({"mode": "a", "allow": ["Read", "Write"]}), encoding="utf-8")
    second.write_text(json.dumps({"mode": "b", "allow": ["Read", "Bash"]}), encoding="utf-8")

    plan = build_import_plan([("claude", first), ("claude", second)])
    assert _item(plan, "claude", "/mode")["status"] == "conflict"
    assert _item(plan, "claude", "/allow")["status"] == "conflict"

    with pytest.raises(ConfigError) as caught:
        declaration_from_import_plan(plan)
    assert caught.value.code == "IMPORT_CONFLICT_UNRESOLVED"

    mode = _item(plan, "claude", "/mode")
    mode.update({"action": "take", "source": "claude-2"})
    allow = _item(plan, "claude", "/allow")
    allow["action"] = "union"

    declaration = declaration_from_import_plan(plan)
    assert declaration["targets"]["claude"]["base"] == {
        "mode": "b",
        "allow": ["Read", "Write", "Bash"],
    }


def test_user_can_exclude_single_field_or_subtree(tmp_path):
    source = tmp_path / "settings.json"
    source.write_text(
        json.dumps({"keep": True, "remove": 1, "nested": {"drop": 2, "alsoDrop": 3}}),
        encoding="utf-8",
    )
    plan = build_import_plan([("claude", source)])
    _item(plan, "claude", "/remove")["action"] = "exclude"
    plan["targets"]["claude"]["excludes"] = ["/nested"]

    declaration = declaration_from_import_plan(plan)

    assert declaration["targets"]["claude"]["base"] == {"keep": True}


def test_json_pointer_escaping_and_additional_excludes(tmp_path):
    source = tmp_path / "settings.json"
    source.write_text(json.dumps({"a/b": {"~key": 1}, "drop": {"child": 2}}), encoding="utf-8")
    plan = build_import_plan([("claude", source)])

    assert _item(plan, "claude", "/a~1b/~0key")["value"] == 1
    declaration = declaration_from_import_plan(plan, additional_excludes=[("claude", "/drop")])

    assert declaration["targets"]["claude"]["base"] == {"a/b": {"~key": 1}}


def test_set_decision_uses_explicit_selected_value(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"mode": "a"}', encoding="utf-8")
    second.write_text('{"mode": "b"}', encoding="utf-8")
    plan = build_import_plan([("claude", first), ("claude", second)])
    _item(plan, "claude", "/mode").update({"action": "set", "selectedValue": "custom"})

    declaration = declaration_from_import_plan(plan)

    assert declaration["targets"]["claude"]["base"]["mode"] == "custom"


def test_sensitive_and_out_of_scope_fields_are_excluded_without_storing_values(tmp_path):
    source = tmp_path / "settings.json"
    source.write_text(
        json.dumps({"env": {"TOKEN": "sk-ant-secret"}, "autoConnectIde": True, "keep": "value"}),
        encoding="utf-8",
    )

    plan = build_import_plan([("claude", source)])

    sensitive = _item(plan, "claude", "/env/TOKEN")
    assert sensitive == {
        "path": "/env/TOKEN",
        "status": "sensitive",
        "sources": ["claude-1"],
        "action": "exclude",
    }
    out_of_scope = _item(plan, "claude", "/autoConnectIde")
    assert out_of_scope["status"] == "out-of-scope"
    assert "value" not in out_of_scope

    declaration = declaration_from_import_plan(plan)
    assert declaration["targets"]["claude"]["base"] == {"keep": "value"}


def test_cli_import_inspect_and_generate_lifecycle(tmp_path):
    first = tmp_path / "first.toml"
    second = tmp_path / "second.toml"
    first.write_text('model = "gpt-5"\nnotify = ["one"]\n', encoding="utf-8")
    second.write_text('model = "gpt-5"\nnotify = ["two"]\n', encoding="utf-8")
    plan_path = tmp_path / "import-plan.yaml"
    output_path = tmp_path / "agent-config.yaml"

    assert main(
        [
            "import",
            "inspect",
            "--source",
            f"codex={first}",
            "--source",
            f"codex={second}",
            "--plan",
            str(plan_path),
        ]
    ) == 0

    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    _item(plan, "codex", "/notify").update({"action": "take", "source": "codex-2"})
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True), encoding="utf-8")

    assert main(["import", "generate", "--plan", str(plan_path), "--output", str(output_path)]) == 0
    declaration = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert declaration["targets"]["codex"]["base"] == {"model": "gpt-5", "notify": ["two"]}


def test_cli_generate_refuses_to_overwrite_existing_declaration(tmp_path):
    source = tmp_path / "settings.json"
    source.write_text('{"keep": true}\n', encoding="utf-8")
    plan = build_import_plan([("claude", source)])
    plan_path = tmp_path / "import-plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    output_path = tmp_path / "agent-config.yaml"
    output_path.write_text("existing\n", encoding="utf-8")

    assert main(["import", "generate", "--plan", str(plan_path), "--output", str(output_path)]) == 2
    assert output_path.read_text(encoding="utf-8") == "existing\n"
