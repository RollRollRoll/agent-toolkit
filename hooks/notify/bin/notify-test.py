"""发送一条测试通知，同步报告结果：python3 notify-test.py"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_notify.testcmd import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(dict(os.environ)))
