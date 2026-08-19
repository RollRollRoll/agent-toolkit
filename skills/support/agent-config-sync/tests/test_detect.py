from aiconfig.detect import detect_context, detect_os, detect_runtime


def test_detect_supported_operating_systems():
    assert detect_os("Windows") == "windows"
    assert detect_os("Linux") == "linux"
    assert detect_os("Darwin") == "macos"


def test_detect_wsl_from_environment_and_proc():
    assert detect_runtime({"WSL_DISTRO_NAME": "Ubuntu"}, lambda _: "") == "wsl"
    assert detect_runtime({}, lambda _: "Linux version Microsoft WSL2") == "wsl"
    assert detect_runtime({}, lambda _: "Linux native") == "native"


def test_command_line_context_overrides_local_file(tmp_path):
    context_file = tmp_path / "context.yaml"
    context_file.write_text("profile: work\ntags: [local]\n", encoding="utf-8")
    context = detect_context(
        context_file=context_file,
        profile="personal",
        tags=["cli"],
        system="Linux",
        hostname="Host",
        user="alice",
        home=str(tmp_path),
        read_text=lambda _: "native",
        environ={},
    )
    assert context["profile"] == "personal"
    assert context["tags"] == ["cli"]

