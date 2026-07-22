#!/usr/bin/env python3
"""以可移植、可恢复审计的方式驱动 Codex headless 会话。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SAFE_SANDBOXES = {"read-only", "workspace-write"}
REQUIRED_EXEC_FLAGS = (
    "--json",
    "--sandbox",
    "--cd",
    "--ignore-user-config",
    "--ignore-rules",
    "--strict-config",
)
REQUIRED_RESUME_FLAGS = (
    "--json",
    "--ignore-user-config",
    "--ignore-rules",
    "--strict-config",
)


class RunnerError(RuntimeError):
    """表示运行前即可确定的配置或状态错误。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RunnerError(f"缺少运行文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f"运行文件不是有效 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RunnerError(f"运行文件顶层必须是对象：{path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _resolve_executable(command: str) -> str:
    if os.sep in command:
        path = Path(command).expanduser().resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RunnerError(f"Codex CLI 不可执行：{path}")
        return str(path)
    resolved = shutil.which(command)
    if not resolved:
        raise RunnerError(f"找不到 Codex CLI：{command}")
    return resolved


def _run_probe(executable: str, arguments: list[str], label: str) -> str:
    try:
        result = subprocess.run(
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RunnerError(f"Codex CLI 预检失败（{label}）：{exc}") from exc
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RunnerError(
            f"Codex CLI 预检失败（{label}，退出码 {result.returncode}）：{output}"
        )
    return output


def _probe_cli(command: str) -> dict[str, Any]:
    executable = _resolve_executable(command)
    version = _run_probe(executable, ["--version"], "--version")
    exec_help = _run_probe(executable, ["exec", "--help"], "exec --help")
    resume_help = _run_probe(
        executable, ["exec", "resume", "--help"], "exec resume --help"
    )
    missing = [flag for flag in REQUIRED_EXEC_FLAGS if flag not in exec_help]
    missing.extend(
        f"resume:{flag}" for flag in REQUIRED_RESUME_FLAGS if flag not in resume_help
    )
    if missing:
        raise RunnerError("Codex CLI 缺少 fail-closed 所需参数：" + "、".join(missing))
    return {
        "executable": executable,
        "version": version,
        "required_flags": list(REQUIRED_EXEC_FLAGS),
        "resume_required_flags": list(REQUIRED_RESUME_FLAGS),
    }


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_skill_name(skill_name: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", skill_name):
        raise RunnerError("skill 名只允许小写字母、数字和连字符，且最长 64 个字符")


def _load_run(run_dir_raw: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(run_dir_raw).expanduser().resolve()
    config = _read_json(run_dir / "run-config.json")
    state = _read_json(run_dir / "run-state.json")
    if config.get("schema_version") != SCHEMA_VERSION or state.get("schema_version") != SCHEMA_VERSION:
        raise RunnerError("运行目录版本不受当前 runner 支持")
    configured_run_dir = config.get("run_dir")
    if not isinstance(configured_run_dir, str) or Path(configured_run_dir).resolve() != run_dir:
        raise RunnerError("run-config.json 与 --run-dir 不匹配")
    sandbox_raw = config.get("sandbox")
    report_dir_raw = config.get("report_dir")
    isolated_home_raw = config.get("isolated_home")
    if not all(isinstance(value, str) for value in (sandbox_raw, report_dir_raw, isolated_home_raw)):
        raise RunnerError("run-config.json 缺少有效的 sandbox / report_dir / isolated_home")
    sandbox = Path(sandbox_raw).resolve()
    report_dir = Path(report_dir_raw).resolve()
    isolated_home = Path(isolated_home_raw).resolve()
    if sandbox == run_dir or sandbox.parent != run_dir.parent or not sandbox.is_dir():
        raise RunnerError("run-config.json 中的沙箱路径无效")
    if not _is_within(isolated_home, run_dir) or not isolated_home.is_dir():
        raise RunnerError("run-config.json 中的隔离 HOME 无效")
    if _is_within(report_dir, sandbox) or _is_within(report_dir, run_dir):
        raise RunnerError("run-config.json 中的报告目录破坏了零侵入边界")
    for key in ("session_id_file", "transcript_file", "stderr_file"):
        value = state.get(key)
        if not isinstance(value, str) or not _is_within(Path(value).resolve(), run_dir):
            raise RunnerError(f"run-state.json 中 {key} 必须位于编排目录内")
    return run_dir, config, state


def _command_doctor(args: argparse.Namespace) -> int:
    print(json.dumps(_probe_cli(args.codex), ensure_ascii=False, indent=2))
    return 0


def _command_init(args: argparse.Namespace) -> int:
    _validate_skill_name(args.skill_name)
    if args.sandbox_mode not in SAFE_SANDBOXES:
        raise RunnerError("--sandbox-mode 只允许 read-only 或 workspace-write")
    if args.timeout < 1 or args.max_turns < 1:
        raise RunnerError("超时秒数和最大轮数都必须大于 0")
    probe = _probe_cli(args.codex)

    sandbox = Path(args.sandbox).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    report_dir = Path(args.report_dir).expanduser().resolve()
    if sandbox == run_dir or sandbox.parent != run_dir.parent:
        raise RunnerError("沙箱与编排目录必须是同一父目录下的两个不同目录")
    if _is_within(report_dir, sandbox) or _is_within(report_dir, run_dir):
        raise RunnerError("持久报告目录不得位于沙箱或编排目录内")
    if sandbox.exists() or run_dir.exists():
        raise RunnerError("沙箱或编排目录已存在；为避免串跑，请换用新的目录名")

    sandbox.parent.mkdir(parents=True, exist_ok=True)
    sandbox.mkdir()
    run_dir.mkdir()
    isolated_home = run_dir / "home"
    isolated_home.mkdir()
    codex_home = Path(
        os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    ).expanduser().resolve()
    created_at = _utc_now()
    config: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex[:12],
        "created_at": created_at,
        "platform": "codex",
        "sandbox": str(sandbox),
        "run_dir": str(run_dir),
        "report_dir": str(report_dir),
        "isolated_home": str(isolated_home),
        "codex_home": str(codex_home),
        "skill_name": args.skill_name,
        "codex": probe,
        "sandbox_mode": args.sandbox_mode,
        "timeout_seconds": args.timeout,
        "max_turns": args.max_turns,
        "approval_policy": "never",
        "web_search": "disabled",
        "ignore_user_config": True,
        "ignore_rules": True,
    }
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "turns": [],
        "session_id_file": str(run_dir / "session-id"),
        "transcript_file": str(run_dir / "transcript-run.jsonl"),
        "stderr_file": str(run_dir / "stderr.log"),
    }
    _write_json(run_dir / "run-config.json", config)
    _write_json(run_dir / "run-state.json", state)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


def _read_prompt(path_raw: str, run_dir: Path) -> tuple[str, str]:
    path = Path(path_raw).expanduser().resolve()
    if not _is_within(path, run_dir):
        raise RunnerError("prompt 文件必须位于编排目录内")
    try:
        prompt = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RunnerError(f"prompt 文件不存在：{path}") from exc
    if not prompt.strip():
        raise RunnerError("prompt 不得为空")
    if "\0" in prompt:
        raise RunnerError("prompt 不得包含 NUL 字符")
    return prompt, hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _thread_ids(path: Path, start: int) -> list[str]:
    values: list[str] = []
    if not path.exists():
        return values
    with path.open("rb") as stream:
        stream.seek(start)
        for raw in stream:
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if (
                isinstance(event, dict)
                and event.get("type") == "thread.started"
                and isinstance(event.get("thread_id"), str)
            ):
                values.append(event["thread_id"])
    return values


def _append_runner_error(stderr_path: Path, message: str) -> None:
    with stderr_path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n[test-skill-codex-runner] {message}\n")


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        return
    process.wait()


def _verify_git_repo(sandbox: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(sandbox), "rev-parse", "--is-inside-work-tree"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RunnerError("Codex headless 沙箱必须先初始化为 Git 仓库")


def _invoke(args: argparse.Namespace, mode: str) -> int:
    run_dir, config, state = _load_run(args.run_dir)
    turns = state.get("turns")
    if not isinstance(turns, list):
        raise RunnerError("run-state.json 中 turns 必须是数组")
    if mode == "start" and turns:
        raise RunnerError("首轮已经执行；不得重复 start 或向旧记录追加新会话")
    if mode == "resume":
        if not turns:
            raise RunnerError("尚未执行首轮，不能 resume")
        if not turns[-1].get("success"):
            raise RunnerError("上一轮失败；为避免不确定状态，不得继续该会话")
        if len(turns) >= int(config["max_turns"]):
            raise RunnerError("已达到配置的最大轮数")

    prompt, prompt_hash = _read_prompt(args.prompt_file, run_dir)
    sandbox = Path(config["sandbox"])
    _verify_git_repo(sandbox)
    transcript_path = Path(state["transcript_file"])
    stderr_path = Path(state["stderr_file"])
    transcript_start = transcript_path.stat().st_size if transcript_path.exists() else 0
    stderr_start = stderr_path.stat().st_size if stderr_path.exists() else 0
    session_path = Path(state["session_id_file"])

    shared = [
        "--json",
        "--strict-config",
        "--ignore-user-config",
        "--ignore-rules",
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
    ]
    executable = config["codex"]["executable"]
    expected_session: str | None = None
    if mode == "start":
        command = [
            executable,
            "exec",
            *shared,
            "--color",
            "never",
            "--sandbox",
            config["sandbox_mode"],
            "--cd",
            str(sandbox),
            prompt,
        ]
    else:
        try:
            expected_session = session_path.read_text(encoding="utf-8").strip()
            uuid.UUID(expected_session)
        except (FileNotFoundError, ValueError) as exc:
            raise RunnerError("缺少有效的 Codex session-id，不能 resume") from exc
        command = [
            executable,
            "exec",
            "resume",
            *shared,
            "-c",
            f'sandbox_mode="{config["sandbox_mode"]}"',
            expected_session,
            prompt,
        ]

    child_env = os.environ.copy()
    child_env["HOME"] = config["isolated_home"]
    child_env["CODEX_HOME"] = config["codex_home"]
    started_at = _utc_now()
    started_monotonic = time.monotonic()
    timed_out = False
    process_exit = 1
    with transcript_path.open("ab") as stdout_stream, stderr_path.open("ab") as stderr_stream:
        try:
            process = subprocess.Popen(
                command,
                cwd=sandbox,
                env=child_env,
                stdout=stdout_stream,
                stderr=stderr_stream,
                start_new_session=(os.name == "posix"),
            )
        except OSError as exc:
            _append_runner_error(stderr_path, f"启动 Codex CLI 失败：{exc}")
            process = None
        if process is not None:
            try:
                process_exit = process.wait(timeout=int(config["timeout_seconds"]))
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate(process)
                process_exit = 124
                _append_runner_error(stderr_path, "本轮达到超时上限，已终止进程组")

    transcript_end = transcript_path.stat().st_size
    stderr_end = stderr_path.stat().st_size
    emitted_ids = _thread_ids(transcript_path, transcript_start)
    unique_ids = list(dict.fromkeys(emitted_ids))
    session_error: str | None = None
    if mode == "start":
        if len(unique_ids) != 1:
            session_error = "首轮必须且只能产生一个 thread.started.thread_id"
        else:
            expected_session = unique_ids[0]
            try:
                uuid.UUID(expected_session)
            except ValueError:
                session_error = "Codex 返回的 thread_id 不是有效 UUID"
            if session_error is None:
                session_path.write_text(expected_session + "\n", encoding="utf-8")
    elif unique_ids and any(value != expected_session for value in unique_ids):
        session_error = "续轮返回了与已记录 session-id 不一致的 thread_id"

    if timed_out:
        error = "本轮超时"
    elif process_exit != 0:
        error = f"Codex CLI 退出码为 {process_exit}"
    else:
        error = session_error
    success = error is None
    turn = {
        "turn": len(turns) + 1,
        "mode": mode,
        "started_at": started_at,
        "finished_at": _utc_now(),
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        "prompt_file": str(Path(args.prompt_file).expanduser().resolve()),
        "prompt_sha256": prompt_hash,
        "transcript_bytes": [transcript_start, transcript_end],
        "stderr_bytes": [stderr_start, stderr_end],
        "exit_code": process_exit,
        "timed_out": timed_out,
        "success": success,
        "error": error,
    }
    turns.append(turn)
    state["turns"] = turns
    state["updated_at"] = _utc_now()
    _write_json(run_dir / "run-state.json", state)
    if success:
        return 0
    if error:
        _append_runner_error(stderr_path, error)
    return 124 if timed_out else (process_exit if process_exit != 0 else 2)


def _command_status(args: argparse.Namespace) -> int:
    _, config, state = _load_run(args.run_dir)
    print(json.dumps({"config": config, "state": state}, ensure_ascii=False, indent=2))
    return 0


def _command_report_path(args: argparse.Namespace) -> int:
    run_dir, config, state = _load_run(args.run_dir)
    existing = state.get("report_path")
    if isinstance(existing, str):
        print(existing)
        return 0
    report_dir = Path(config["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    path = report_dir / f"test-report-{timestamp}-{config['run_id']}.md"
    path.touch(exist_ok=False)
    state["report_path"] = str(path)
    state["updated_at"] = _utc_now()
    _write_json(run_dir / "run-state.json", state)
    print(path)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="预检 Codex CLI")
    doctor.add_argument("--codex", default="codex", help="Codex CLI 命令或绝对路径")
    doctor.set_defaults(handler=_command_doctor)

    init = subparsers.add_parser("init", help="初始化隔离运行目录")
    init.add_argument("--codex", default="codex")
    init.add_argument("--sandbox", required=True)
    init.add_argument("--run-dir", required=True)
    init.add_argument("--report-dir", required=True)
    init.add_argument("--skill-name", required=True)
    init.add_argument("--sandbox-mode", default="workspace-write")
    init.add_argument("--timeout", type=int, default=600)
    init.add_argument("--max-turns", type=int, default=10)
    init.set_defaults(handler=_command_init)

    for name, mode in (("start", "start"), ("resume", "resume")):
        command = subparsers.add_parser(name)
        command.add_argument("--run-dir", required=True)
        command.add_argument("--prompt-file", required=True)
        command.set_defaults(handler=lambda args, selected=mode: _invoke(args, selected))

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(handler=_command_status)

    report = subparsers.add_parser("report-path")
    report.add_argument("--run-dir", required=True)
    report.set_defaults(handler=_command_report_path)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except RunnerError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
