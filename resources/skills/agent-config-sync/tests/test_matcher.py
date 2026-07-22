from aiconfig.matcher import matched_overlays, matches


CONTEXT = {
    "os": "linux",
    "runtime": "wsl",
    "hostname": "Digitalfyre-LA",
    "profile": "work",
    "tags": ["development", "company-network"],
}


def test_conditions_are_and_and_lists_are_any():
    assert matches({"os": ["linux", "macos"], "runtime": "wsl", "profile": "work"}, CONTEXT)
    assert not matches({"os": "linux", "runtime": "native"}, CONTEXT)


def test_hostname_is_case_insensitive_and_tags_require_all():
    assert matches({"hostname": "digitalfyre-la"}, CONTEXT)
    assert matches({"tags": {"contains": ["development", "company-network"]}}, CONTEXT)
    assert not matches({"tags": {"contains": ["missing"]}}, CONTEXT)


def test_overlays_preserve_declaration_order():
    overlays = [
        {"name": "linux", "when": {"os": "linux"}},
        {"name": "native", "when": {"runtime": "native"}},
        {"name": "work", "when": {"profile": "work"}},
    ]
    assert [item["name"] for item in matched_overlays(overlays, CONTEXT)] == ["linux", "work"]

