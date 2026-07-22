import pytest

from aiconfig.errors import ConfigError
from aiconfig.validator import scan_secrets, validate_claude_scope


def test_rejects_claude_field_from_other_file():
    with pytest.raises(ConfigError) as caught:
        validate_claude_scope({"autoConnectIde": True})
    assert caught.value.code == "CLAUDE_FIELD_OUT_OF_SCOPE"


def test_secret_scanner_reports_location_without_value():
    warnings = scan_secrets({"targets": {"claude": {"env": {"TOKEN": "sk-ant-secret"}}}})
    assert warnings == [
        "WARNING [POSSIBLE_SECRET_FOUND] possible secret found at targets.claude.env.TOKEN"
    ]
    assert "sk-ant-secret" not in warnings[0]

