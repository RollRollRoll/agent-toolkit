"""稳定文本差异。"""

from __future__ import annotations

import difflib
from pathlib import Path


def diff_content(path: Path, generated: str) -> str:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = difflib.unified_diff(
        current.splitlines(keepends=True),
        generated.splitlines(keepends=True),
        fromfile=str(path),
        tofile=f"generated:{path.name}",
    )
    return "".join(lines)

