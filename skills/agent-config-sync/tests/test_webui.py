import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
import yaml

from aiconfig.errors import ConfigError
from aiconfig.cli import main
from aiconfig.importer import build_import_plan, dump_import_plan
from aiconfig.webui import WebUIState, create_server


class FakeDocsResolver:
    def resolve(self, target, path, *, refresh=False):
        return {
            "target": target,
            "path": path,
            "found": True,
            "description": f"Description for {path}",
            "type": "string",
            "allowedValues": [],
            "default": None,
            "sourceUrl": "https://example.invalid/schema.json",
            "sourceKind": "official-schema",
            "fetchedAt": "2026-07-22T00:00:00+00:00",
            "stale": False,
            "refresh": refresh,
        }


def _make_state(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"mode": "a", "keep": true}', encoding="utf-8")
    second.write_text('{"mode": "b", "keep": true}', encoding="utf-8")
    plan = build_import_plan([("claude", first), ("claude", second)])
    plan_path = tmp_path / "import-plan.yaml"
    plan_path.write_text(dump_import_plan(plan), encoding="utf-8")
    output_path = tmp_path / "agent-config.yaml"
    return WebUIState(plan_path, output_path, docs_resolver=FakeDocsResolver())


def test_state_updates_decision_then_previews_and_generates(tmp_path):
    state = _make_state(tmp_path)

    snapshot = state.snapshot()
    assert snapshot["summary"] == {
        "total": 2,
        "duplicates": 1,
        "unresolved": 1,
        "excluded": 0,
    }
    with pytest.raises(ConfigError) as unresolved:
        state.preview()
    assert unresolved.value.code == "IMPORT_CONFLICT_UNRESOLVED"

    state.update_decision("claude", "/mode", {"action": "take", "source": "claude-2"})
    preview = state.preview()
    assert yaml.safe_load(preview["facts"])["targets"]["claude"]["base"]["mode"] == "b"
    assert json.loads(preview["claude"])["mode"] == "b"

    result = state.generate()
    assert result["path"] == str(tmp_path / "agent-config.yaml")
    assert yaml.safe_load((tmp_path / "agent-config.yaml").read_text(encoding="utf-8"))["targets"]

    with pytest.raises(ConfigError) as existing:
        state.generate()
    assert existing.value.code == "IMPORT_OUTPUT_EXISTS"


def test_state_rejects_invalid_or_protected_decisions(tmp_path):
    source = tmp_path / "settings.json"
    source.write_text('{"env": {"TOKEN": "sk-ant-secret"}}', encoding="utf-8")
    plan = build_import_plan([("claude", source)])
    plan_path = tmp_path / "import-plan.yaml"
    plan_path.write_text(dump_import_plan(plan), encoding="utf-8")
    state = WebUIState(plan_path, tmp_path / "agent-config.yaml", docs_resolver=FakeDocsResolver())

    with pytest.raises(ConfigError) as caught:
        state.update_decision("claude", "/env/TOKEN", {"action": "keep"})
    assert caught.value.code == "IMPORT_DECISION_INVALID"


def test_state_queries_docs_through_resolver(tmp_path):
    state = _make_state(tmp_path)

    result = state.lookup_docs("claude", "/mode", refresh=True)

    assert result["description"] == "Description for /mode"
    assert result["refresh"] is True


def test_http_api_requires_session_token(tmp_path):
    state = _make_state(tmp_path)
    server = create_server(state, port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    url = f"http://{host}:{port}/api/state"
    try:
        with pytest.raises(HTTPError) as denied:
            urlopen(url)
        assert denied.value.code == 403

        request = Request(url, headers={"X-Aiconfig-Token": "test-token"})
        response = json.loads(urlopen(request).read().decode("utf-8"))
        assert response["summary"]["unresolved"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_ui_does_not_render_import_workflow(tmp_path):
    state = _make_state(tmp_path)
    server = create_server(state, port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        html = urlopen(f"http://{host}:{port}/").read().decode("utf-8")
        assert 'class="stepper"' not in html
        assert 'aria-label="处理进度"' not in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_ui_displays_json_pointer_as_readable_hierarchy(tmp_path):
    state = _make_state(tmp_path)
    server = create_server(state, port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        script = urlopen(f"http://{host}:{port}/app.js").read().decode("utf-8")
        assert 'function formatDisplayPath(pointer)' in script
        assert '.join(" › ")' in script
        assert '"item-path", formatDisplayPath(item.path)' in script
        assert 'ui.detailPath.textContent = formatDisplayPath(item.path)' in script
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_ui_reveals_selected_detail_and_distinguishes_decisions(tmp_path):
    state = _make_state(tmp_path)
    server = create_server(state, port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        script = urlopen(f"http://{host}:{port}/app.js").read().decode("utf-8")
        styles = urlopen(f"http://{host}:{port}/styles.css").read().decode("utf-8")
        assert "ui.detail.scrollIntoView" in script
        assert 'element("span", `decision-tag ${decisionName}`' in script
        assert ".decision-tag.retained" in styles
        assert ".decision-tag.excluded" in styles
        assert ".item-row.decision-excluded.selected" in styles
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_ui_command_passes_resolved_paths_and_options(tmp_path, monkeypatch):
    plan_path = tmp_path / "import-plan.yaml"
    output_path = tmp_path / "agent-config.yaml"
    called = {}

    def fake_serve_ui(plan, output, *, port, open_browser):
        called.update(plan=plan, output=output, port=port, open_browser=open_browser)

    monkeypatch.setattr("aiconfig.webui.serve_ui", fake_serve_ui)

    assert main(
        [
            "ui",
            "--plan",
            str(plan_path),
            "--output",
            str(output_path),
            "--port",
            "0",
            "--open",
        ]
    ) == 0
    assert called == {
        "plan": plan_path.resolve(),
        "output": output_path.resolve(),
        "port": 0,
        "open_browser": True,
    }
