import pytest

from aiconfig.errors import ConfigError
from aiconfig.merger import deep_merge, merge_target


def test_deep_merge_scalar_replace_and_array_replace():
    base = {"sandbox": {"enabled": True}, "roots": ["/base"]}
    overlay = {"sandbox": {"enabled": False, "mode": "strict"}, "roots": ["/new"]}
    assert deep_merge(base, overlay) == {
        "sandbox": {"enabled": False, "mode": "strict"},
        "roots": ["/new"],
    }


def test_append_prepend_and_delete():
    base = {"roots": ["/base"], "sandbox": {"enabled": True, "legacy": True}}
    overlays = [
        {"name": "append", "set": {"roots": {"$append": ["/tail"]}}},
        {"name": "prepend-delete", "set": {"roots": {"$prepend": ["/head"]}, "sandbox": {"legacy": {"$delete": True}}}},
    ]
    assert merge_target(base, overlays) == {
        "roots": ["/head", "/base", "/tail"],
        "sandbox": {"enabled": True},
    }


def test_new_nested_array_operation_is_applied():
    assert deep_merge({}, {"permissions": {"allow": {"$append": ["Read"]}}}) == {
        "permissions": {"allow": ["Read"]}
    }


def test_base_is_normalized_and_does_not_emit_delete_operator():
    assert merge_target({"keep": True, "drop": {"$delete": True}}, []) == {"keep": True}


def test_compound_type_conflict_is_rejected():
    with pytest.raises(ConfigError, match="隐式替换") as caught:
        deep_merge({"sandbox": {}}, {"sandbox": []})
    assert caught.value.code == "MERGE_TYPE_CONFLICT"
