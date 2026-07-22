import json

from aiconfig.renderer import render_claude


def test_claude_json_is_stable_unicode_and_parseable():
    data = {"提示": "中文", "permissions": {"defaultMode": "default"}}
    first = render_claude(data)
    assert first == render_claude(data)
    assert "中文" in first and "\\u4e2d" not in first
    assert first.endswith("\n")
    assert json.loads(first) == data

