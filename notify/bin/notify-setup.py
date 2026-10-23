"""交互式配置向导：python3 notify-setup.py（需在交互终端运行）"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_notify.setup import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(dict(os.environ)))
