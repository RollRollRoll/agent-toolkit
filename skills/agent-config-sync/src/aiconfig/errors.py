"""稳定错误码与用户可读错误。"""

from __future__ import annotations


class ConfigError(Exception):
    """携带稳定错误码的配置错误。"""

    def __init__(self, code: str, message: str, *, location: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.location = location

    def format(self) -> str:
        lines = [f"ERROR [{self.code}]", "", self.message]
        if self.location:
            lines.extend(["", f"Location: {self.location}"])
        return "\n".join(lines)

