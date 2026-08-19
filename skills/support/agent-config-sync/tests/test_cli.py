from pathlib import Path

from aiconfig.cli import main


def test_full_cli_lifecycle_and_manual_edit_protection(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()

    assert main(["init", "--directory", str(project)]) == 0
    context_file = project / "context.yaml"
    context_file.write_text(
        f'home: "{home}"\nprofile: work\ntags: [development]\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(project)

    common = ["--context", str(context_file)]
    assert main(["validate", *common]) == 0
    assert main(["render", *common]) == 0
    assert (project / ".agent-config" / "generated" / "config.toml").is_file()
    assert (project / ".agent-config" / "generated" / "settings.json").is_file()
    assert main(["plan", *common]) == 0
    assert main(["apply", *common]) == 0
    assert (home / ".codex" / "config.toml").is_file()
    claude_path = home / ".claude" / "settings.json"
    assert claude_path.is_file()
    assert main(["status", *common]) == 0
    assert "codex: synced" in capsys.readouterr().out

    claude_path.write_text('{"manual": true}\n', encoding="utf-8")
    assert main(["apply", "claude", *common]) == 2
    assert claude_path.read_text(encoding="utf-8") == '{"manual": true}\n'

