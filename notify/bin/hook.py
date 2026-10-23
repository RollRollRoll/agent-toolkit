"""hook 命令入口：python3 hook.py <claude|codex>，payload 从 stdin 读取。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_notify.hook import run  # noqa: E402

if __name__ == "__main__":
    agent = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001
        raw = ""
    sys.exit(run(agent, raw, dict(os.environ)))
