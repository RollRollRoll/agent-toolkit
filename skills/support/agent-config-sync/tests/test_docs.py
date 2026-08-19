from aiconfig.docs import ConfigDocsResolver


CODEX_SCHEMA = {
    "type": "object",
    "properties": {
        "approval_policy": {
            "description": "Controls when Codex asks for approval.",
            "type": "string",
            "enum": ["untrusted", "on-request", "never"],
            "default": "on-request",
        },
        "sandbox_workspace_write": {"$ref": "#/$defs/WorkspaceWrite"},
    },
    "$defs": {
        "WorkspaceWrite": {
            "type": "object",
            "properties": {
                "writable_roots": {
                    "description": "Additional writable roots.",
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
        }
    },
}


def test_resolver_fetches_official_schema_and_extracts_field_metadata(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return CODEX_SCHEMA

    resolver = ConfigDocsResolver(tmp_path / "docs-cache.json", fetch_json=fetch)
    result = resolver.resolve("codex", "/approval_policy")

    assert result["found"] is True
    assert result["description"] == "Controls when Codex asks for approval."
    assert result["type"] == "string"
    assert result["allowedValues"] == ["untrusted", "on-request", "never"]
    assert result["default"] == "on-request"
    assert result["sourceUrl"].endswith("/codex/config-schema.json")
    assert len(calls) == 1

    cached = resolver.resolve("codex", "/sandbox_workspace_write/writable_roots")
    assert cached["description"] == "Additional writable roots."
    assert cached["type"] == "array<string>"
    assert len(calls) == 1


def test_resolver_supports_definitions_and_dynamic_object_keys(tmp_path):
    schema = {
        "type": "object",
        "properties": {
            "model_providers": {
                "type": "object",
                "additionalProperties": {"$ref": "#/definitions/Provider"},
            }
        },
        "definitions": {
            "Provider": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Provider display name."}
                },
            }
        },
    }
    resolver = ConfigDocsResolver(tmp_path / "docs-cache.json", fetch_json=lambda _: schema)

    result = resolver.resolve("codex", "/model_providers/custom/name")

    assert result["found"] is True
    assert result["description"] == "Provider display name."


def test_resolver_reports_unknown_field_without_inventing_description(tmp_path):
    resolver = ConfigDocsResolver(tmp_path / "docs-cache.json", fetch_json=lambda _: CODEX_SCHEMA)

    result = resolver.resolve("codex", "/unknown")

    assert result["found"] is False
    assert result["description"] is None
    assert result["sourceKind"] == "official-schema"
