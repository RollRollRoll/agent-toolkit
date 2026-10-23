"""诊断 agent-notify 配置与 Bot 可达性，只读：python3 notify-doctor.py [--offline]"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_notify.doctor import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(dict(os.environ), argv=sys.argv[1:]))
