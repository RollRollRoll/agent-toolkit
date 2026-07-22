import tomlkit

from aiconfig.renderer import render_codex


def test_codex_toml_is_stable_parseable_and_escapes_windows_paths():
    data = {
        "approval_policy": "on-request",
        "notify": ["pwsh.exe", "-File", "D:\\Scripts\\notify.ps1"],
        "sandbox_workspace_write": {"network_access": False},
    }
    first = render_codex(data)
    second = render_codex(data)
    assert first == second
    assert first.endswith("\n")
    assert tomlkit.parse(first)["notify"][2] == "D:\\Scripts\\notify.ps1"

