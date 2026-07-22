#!/usr/bin/env python3
"""run-headless.py 的无真实模型回归测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "run-headless.py"


class RunHeadlessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fake = self.root / "fake-claude"
        self.fake.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import pathlib
                import sys
                import time

                args = sys.argv[1:]
                if args == ["--version"]:
                    print("2.1.198-fake")
                    raise SystemExit(0)
                if args == ["--help"]:
                    # 官方 CLI 明确说 --help 不保证列出全部参数；runner 不得据此误拒绝。
                    print("--tools --allowedTools --output-format --resume")
                    raise SystemExit(0)

                separator = args.index("--")
                prompt = args[separator + 1]
                call_file = pathlib.Path.cwd() / "fake-calls.jsonl"
                with call_file.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"args": args, "prompt": prompt}, ensure_ascii=False) + "\\n")
                if prompt == "__SLEEP__":
                    time.sleep(3)
                print(json.dumps({"type": "system", "session_id": "fake-session"}), flush=True)
                print(json.dumps({"type": "result", "session_id": "fake-session"}), flush=True)
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

    def init_run(self, name: str, timeout: int = 5) -> tuple[Path, Path, Path]:
        sandbox = self.root / name
        run_dir = self.root / f"{name}-run"
        report_dir = self.root / "reports" / name
        self.run_runner(
            "init",
            "--claude",
            str(self.fake),
            "--sandbox",
            str(sandbox),
            "--run-dir",
            str(run_dir),
            "--report-dir",
            str(report_dir),
            "--skill-name",
            "sample-skill",
            "--timeout",
            str(timeout),
        )
        return sandbox, run_dir, report_dir

    def test_start_resume_and_unique_report_path(self) -> None:
        sandbox, run_dir, report_dir = self.init_run("case with spaces")
        first_prompt = "--output-format 只是 prompt；保留引号 ' 与换行\n第二行"
        second_prompt = "第二轮：$() 只应作为普通文本"
        first_file = run_dir / "turn-001.txt"
        second_file = run_dir / "turn-002.txt"
        first_file.write_text(first_prompt, encoding="utf-8")
        second_file.write_text(second_prompt, encoding="utf-8")

        self.run_runner("start", "--run-dir", str(run_dir), "--prompt-file", str(first_file))
        self.run_runner("resume", "--run-dir", str(run_dir), "--prompt-file", str(second_file))

        self.assertEqual((run_dir / "session-id").read_text(encoding="utf-8").strip(), "fake-session")
        calls = [json.loads(line) for line in (sandbox / "fake-calls.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([call["prompt"] for call in calls], [first_prompt, second_prompt])
        self.assertIn("--tools", calls[0]["args"])
        self.assertIn("--allowedTools", calls[0]["args"])
        self.assertIn("Read(/**)", calls[0]["args"])
        self.assertNotIn("Skill(sample-skill),Read(/**),Write(/**),Edit(/**)", calls[0]["args"])
        self.assertIn("--setting-sources", calls[0]["args"])
        self.assertIn("--strict-mcp-config", calls[0]["args"])
        self.assertEqual(calls[0]["args"][calls[0]["args"].index("--") + 1], first_prompt)
        self.assertEqual(calls[1]["args"][calls[1]["args"].index("--resume") + 1], "fake-session")

        first = self.run_runner("report-path", "--run-dir", str(run_dir)).stdout.strip()
        second = self.run_runner("report-path", "--run-dir", str(run_dir)).stdout.strip()
        self.assertEqual(first, second)
        self.assertEqual(Path(first).parent.resolve(), report_dir.resolve())
        self.assertTrue(Path(first).is_file())
        self.assertRegex(Path(first).name, r"^test-report-\d{4}-\d{2}-\d{2}-\d{6}-[0-9a-f]{12}\.md$")

        state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state["turns"]), 2)
        self.assertTrue(all(turn["success"] for turn in state["turns"]))

    def test_timeout_is_portable_and_blocks_resume(self) -> None:
        _, run_dir, _ = self.init_run("timeout-case", timeout=1)
        prompt_file = run_dir / "turn-001.txt"
        prompt_file.write_text("__SLEEP__", encoding="utf-8")
        result = self.run_runner(
            "start", "--run-dir", str(run_dir), "--prompt-file", str(prompt_file), check=False
        )
        self.assertEqual(result.returncode, 124)
        state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertTrue(state["turns"][0]["timed_out"])
        self.assertFalse(state["turns"][0]["success"])

        another = run_dir / "turn-002.txt"
        another.write_text("继续", encoding="utf-8")
        resumed = self.run_runner(
            "resume", "--run-dir", str(run_dir), "--prompt-file", str(another), check=False
        )
        self.assertEqual(resumed.returncode, 2)
        self.assertIn("上一轮失败", resumed.stderr)

    def test_rejects_broad_bash_preapproval(self) -> None:
        result = self.run_runner(
            "init",
            "--claude",
            str(self.fake),
            "--sandbox",
            str(self.root / "unsafe"),
            "--run-dir",
            str(self.root / "unsafe-run"),
            "--report-dir",
            str(self.root / "reports"),
            "--skill-name",
            "sample-skill",
            "--tools",
            "Skill,Bash",
            "--allowed-tools",
            "Skill(sample-skill),Bash",
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("禁止无边界预授权 Bash", result.stderr)
        self.assertFalse((self.root / "unsafe").exists())

    def test_bash_requires_explicit_narrow_rules(self) -> None:
        result = self.run_runner(
            "init",
            "--claude",
            str(self.fake),
            "--sandbox",
            str(self.root / "bash-default"),
            "--run-dir",
            str(self.root / "bash-default-run"),
            "--report-dir",
            str(self.root / "reports"),
            "--skill-name",
            "sample-skill",
            "--tools",
            "Skill,Bash",
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("必须显式填写 --allowed-tools", result.stderr)

    def test_narrow_bash_forces_os_sandbox(self) -> None:
        sandbox = self.root / "bash-narrow"
        run_dir = self.root / "bash-narrow-run"
        self.run_runner(
            "init",
            "--claude",
            str(self.fake),
            "--sandbox",
            str(sandbox),
            "--run-dir",
            str(run_dir),
            "--report-dir",
            str(self.root / "reports"),
            "--skill-name",
            "sample-skill",
            "--tools",
            "Skill,Read,Bash",
            "--allowed-tools",
            "Skill(sample-skill),Read(/**),Bash(git status:*)",
        )
        prompt_file = run_dir / "turn-001.txt"
        prompt_file.write_text("检查状态", encoding="utf-8")
        self.run_runner("start", "--run-dir", str(run_dir), "--prompt-file", str(prompt_file))

        call = json.loads((sandbox / "fake-calls.jsonl").read_text(encoding="utf-8"))
        settings_index = call["args"].index("--settings")
        settings = json.loads(call["args"][settings_index + 1])
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertTrue(settings["sandbox"]["failIfUnavailable"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertIn(str(run_dir.resolve()), settings["sandbox"]["filesystem"]["denyRead"])


if __name__ == "__main__":
    unittest.main()
