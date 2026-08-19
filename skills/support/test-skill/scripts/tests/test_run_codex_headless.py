#!/usr/bin/env python3
"""run-codex-headless.py 的无真实模型回归测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "run-codex-headless.py"


class RunCodexHeadlessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fake = self.root / "fake-codex"
        self.fake.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import pathlib
                import sys
                import time

                args = sys.argv[1:]
                if args == ["--version"]:
                    print("codex-cli 0.145.0-fake")
                    raise SystemExit(0)
                if args == ["exec", "--help"]:
                    print("--json --sandbox --cd --ignore-user-config --ignore-rules --strict-config")
                    raise SystemExit(0)
                if args == ["exec", "resume", "--help"]:
                    print("--json --ignore-user-config --ignore-rules --strict-config")
                    raise SystemExit(0)

                is_resume = len(args) > 1 and args[0:2] == ["exec", "resume"]
                prompt = args[-1]
                session = args[-2] if is_resume else "0199a213-81c0-7800-8aa1-bbab2a035a53"
                call_file = pathlib.Path.cwd() / "fake-calls.jsonl"
                with call_file.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({
                        "args": args,
                        "prompt": prompt,
                        "home": os.environ.get("HOME"),
                        "codex_home": os.environ.get("CODEX_HOME"),
                    }, ensure_ascii=False) + "\\n")
                if prompt == "__SLEEP__":
                    time.sleep(3)
                print(json.dumps({"type": "thread.started", "thread_id": session}), flush=True)
                print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}), flush=True)
                print(json.dumps({"type": "turn.completed"}), flush=True)
                print("fake stderr", file=sys.stderr, flush=True)
                """
            ),
            encoding="utf-8",
        )
        self.fake.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_runner(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNNER), *arguments],
            check=check,
            capture_output=True,
            text=True,
        )

    def init_run(
        self, name: str, timeout: int = 5, sandbox_mode: str = "workspace-write"
    ) -> tuple[Path, Path, Path]:
        sandbox = self.root / name
        run_dir = self.root / f"{name}-run"
        report_dir = self.root / "reports" / name
        self.run_runner(
            "init",
            "--codex",
            str(self.fake),
            "--sandbox",
            str(sandbox),
            "--run-dir",
            str(run_dir),
            "--report-dir",
            str(report_dir),
            "--skill-name",
            "sample-skill",
            "--sandbox-mode",
            sandbox_mode,
            "--timeout",
            str(timeout),
        )
        subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
        return sandbox, run_dir, report_dir

    def test_start_resume_and_unique_report_path(self) -> None:
        sandbox, run_dir, report_dir = self.init_run("case with spaces")
        first_prompt = "使用 $sample-skill；保留引号 ' 与换行\n第二行"
        second_prompt = "第二轮：$() 只应作为普通文本"
        first_file = run_dir / "turn-001.txt"
        second_file = run_dir / "turn-002.txt"
        first_file.write_text(first_prompt, encoding="utf-8")
        second_file.write_text(second_prompt, encoding="utf-8")

        self.run_runner("start", "--run-dir", str(run_dir), "--prompt-file", str(first_file))
        self.run_runner("resume", "--run-dir", str(run_dir), "--prompt-file", str(second_file))

        session = (run_dir / "session-id").read_text(encoding="utf-8").strip()
        self.assertEqual(session, "0199a213-81c0-7800-8aa1-bbab2a035a53")
        calls = [
            json.loads(line)
            for line in (sandbox / "fake-calls.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual([call["prompt"] for call in calls], [first_prompt, second_prompt])
        self.assertIn("--json", calls[0]["args"])
        self.assertIn("--sandbox", calls[0]["args"])
        self.assertIn("workspace-write", calls[0]["args"])
        self.assertIn("--ignore-user-config", calls[0]["args"])
        self.assertIn("--ignore-rules", calls[0]["args"])
        self.assertIn('approval_policy="never"', calls[0]["args"])
        self.assertIn('web_search="disabled"', calls[0]["args"])
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", calls[0]["args"])
        self.assertEqual(calls[1]["args"][-2], session)
        self.assertTrue(Path(calls[0]["home"]).resolve().is_relative_to(run_dir.resolve()))

        first = self.run_runner("report-path", "--run-dir", str(run_dir)).stdout.strip()
        second = self.run_runner("report-path", "--run-dir", str(run_dir)).stdout.strip()
        self.assertEqual(first, second)
        self.assertEqual(Path(first).parent.resolve(), report_dir.resolve())
        state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state["turns"]), 2)
        self.assertTrue(all(turn["success"] for turn in state["turns"]))

    def test_timeout_blocks_resume(self) -> None:
        _, run_dir, _ = self.init_run("timeout-case", timeout=1)
        prompt_file = run_dir / "turn-001.txt"
        prompt_file.write_text("__SLEEP__", encoding="utf-8")
        result = self.run_runner(
            "start", "--run-dir", str(run_dir), "--prompt-file", str(prompt_file), check=False
        )
        self.assertEqual(result.returncode, 124)
        state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertTrue(state["turns"][0]["timed_out"])

        another = run_dir / "turn-002.txt"
        another.write_text("继续", encoding="utf-8")
        resumed = self.run_runner(
            "resume", "--run-dir", str(run_dir), "--prompt-file", str(another), check=False
        )
        self.assertEqual(resumed.returncode, 2)
        self.assertIn("上一轮失败", resumed.stderr)

    def test_rejects_danger_full_access(self) -> None:
        result = self.run_runner(
            "init",
            "--codex",
            str(self.fake),
            "--sandbox",
            str(self.root / "unsafe"),
            "--run-dir",
            str(self.root / "unsafe-run"),
            "--report-dir",
            str(self.root / "reports"),
            "--skill-name",
            "sample-skill",
            "--sandbox-mode",
            "danger-full-access",
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("只允许 read-only 或 workspace-write", result.stderr)
        self.assertFalse((self.root / "unsafe").exists())

    def test_requires_git_repo_before_start(self) -> None:
        sandbox = self.root / "no-git"
        run_dir = self.root / "no-git-run"
        self.run_runner(
            "init",
            "--codex",
            str(self.fake),
            "--sandbox",
            str(sandbox),
            "--run-dir",
            str(run_dir),
            "--report-dir",
            str(self.root / "reports"),
            "--skill-name",
            "sample-skill",
        )
        prompt = run_dir / "turn-001.txt"
        prompt.write_text("开始", encoding="utf-8")
        result = self.run_runner(
            "start", "--run-dir", str(run_dir), "--prompt-file", str(prompt), check=False
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("必须先初始化为 Git 仓库", result.stderr)


if __name__ == "__main__":
    unittest.main()
