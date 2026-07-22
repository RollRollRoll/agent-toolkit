import pytest

from aiconfig.errors import ConfigError
from aiconfig.variables import resolve_variables, substitute_tree


CONTEXT = {
    "os": "linux",
    "runtime": "wsl",
    "hostname": "host",
    "user": "alice",
    "home": "/home/alice",
    "profile": "work",
    "tags": [],
}


def test_nested_and_environment_default_variables():
    variables = resolve_variables(
        {"workspace": "${env:WORKSPACE:-${home}/workspace}", "cache": "${workspace}/.cache"},
        CONTEXT,
        {},
    )
    assert variables["workspace"] == "/home/alice/workspace"
    assert variables["cache"] == "/home/alice/workspace/.cache"
    assert substitute_tree({"path": "${cache}", "direct": "${env:OTHER:-${home}/other}"}, variables, environ={}) == {
        "path": "/home/alice/workspace/.cache",
        "direct": "/home/alice/other",
    }


def test_overlay_style_definition_overrides_builtin():
    variables = resolve_variables({"home": "D:\\Users\\alice", "workspace": "${home}\\Work"}, CONTEXT, {})
    assert variables["workspace"] == "D:\\Users\\alice\\Work"


def test_missing_and_cycle_are_rejected():
    with pytest.raises(ConfigError) as missing:
        resolve_variables({"workspace": "${missing}"}, CONTEXT, {})
    assert missing.value.code == "VARIABLE_NOT_FOUND"

    with pytest.raises(ConfigError) as cycle:
        resolve_variables({"a": "${b}", "b": "${a}"}, CONTEXT, {})
    assert cycle.value.code == "VARIABLE_CYCLE"

