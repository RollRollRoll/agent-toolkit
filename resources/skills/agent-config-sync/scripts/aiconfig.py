#!/usr/bin/env python3
"""无需安装即可运行的 aiconfig 入口。"""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))

from aiconfig.cli import main  # noqa: E402


raise SystemExit(main())

