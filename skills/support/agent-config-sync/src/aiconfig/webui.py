"""导入计划的本地审阅界面与同源 HTTP API。"""

from __future__ import annotations

import json
import secrets
import webbrowser
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

from .detect import detect_context
from .docs import ConfigDocsResolver
from .errors import ConfigError
from .importer import (
    declaration_from_import_plan,
    dump_declaration,
    dump_import_plan,
    load_import_plan,
    validate_import_item_decision,
)
from .state import data_dir
from .validator import validate_declaration, validate_schema
from .writer import atomic_write, backup_file


SKILL_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = SKILL_ROOT / "assets" / "ui"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _parse_declaration(text: str) -> dict[str, Any]:
    value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ConfigError("CONFIG_SCHEMA_INVALID", "生成的事实文件顶层必须是对象。")
    validate_schema(value)
    return value


class WebUIState:
    """封装 UI 可执行的全部本地状态变更。"""

    def __init__(
        self,
        plan_path: Path,
        output_path: Path,
        *,
        docs_resolver: ConfigDocsResolver | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.plan_path = Path(plan_path).expanduser().resolve()
        self.output_path = Path(output_path).expanduser().resolve()
        self.context = context or detect_context()
        self.docs_resolver = docs_resolver or ConfigDocsResolver(
            data_dir(self.context["home"]) / "docs-cache.json"
        )

    def snapshot(self) -> dict[str, Any]:
        plan = load_import_plan(self.plan_path)
        summary = {"total": 0, "duplicates": 0, "unresolved": 0, "excluded": 0}
        for target_plan in plan["targets"].values():
            for item in target_plan.get("items", []):
                summary["total"] += 1
                if item.get("status") == "duplicate":
                    summary["duplicates"] += 1
                if item.get("action") == "unresolved":
                    summary["unresolved"] += 1
                if item.get("action") == "exclude":
                    summary["excluded"] += 1
        return {
            "plan": plan,
            "summary": summary,
            "planPath": str(self.plan_path),
            "outputPath": str(self.output_path),
            "outputExists": self.output_path.exists(),
        }

    def update_decision(self, target: str, path: str, decision: dict[str, Any]) -> dict[str, Any]:
        if target not in {"codex", "claude"} or not isinstance(path, str) or not isinstance(decision, dict):
            raise ConfigError("IMPORT_DECISION_INVALID", "决策请求结构无效。", location=path)
        allowed = {"action", "source", "selectedValue"}
        if set(decision) - allowed or not isinstance(decision.get("action"), str):
            raise ConfigError("IMPORT_DECISION_INVALID", "决策包含不支持的字段。", location=path)
        plan = load_import_plan(self.plan_path)
        target_plan = plan["targets"].get(target)
        if not isinstance(target_plan, dict):
            raise ConfigError("IMPORT_DECISION_INVALID", f"导入计划中不存在目标：{target}")
        selected = None
        for item in target_plan.get("items", []):
            if isinstance(item, dict) and item.get("path") == path:
                selected = item
                break
        if selected is None:
            raise ConfigError("IMPORT_DECISION_INVALID", "导入计划中不存在该配置项。", location=path)

        candidate = deepcopy(selected)
        candidate.pop("source", None)
        candidate.pop("selectedValue", None)
        candidate.update(decision)
        validate_import_item_decision(candidate)
        selected.clear()
        selected.update(candidate)
        atomic_write(self.plan_path, dump_import_plan(plan), yaml.safe_load)
        return self.snapshot()

    def preview(self) -> dict[str, Any]:
        declaration = declaration_from_import_plan(load_import_plan(self.plan_path))
        targets = [name for name in ("codex", "claude") if name in declaration["targets"]]
        prepared, warnings = validate_declaration(declaration, self.context, targets)
        return {
            "facts": dump_declaration(declaration),
            "codex": prepared["codex"][2] if "codex" in prepared else None,
            "claude": prepared["claude"][2] if "claude" in prepared else None,
            "warnings": warnings,
        }

    def generate(self, *, force: bool = False) -> dict[str, Any]:
        if self.output_path.exists() and not force:
            raise ConfigError(
                "IMPORT_OUTPUT_EXISTS",
                "事实文件已存在；确认后才能覆盖。",
                location=str(self.output_path),
            )
        preview = self.preview()
        backup = None
        if self.output_path.exists():
            backup = backup_file(
                "declaration",
                self.output_path,
                self.output_path.parent / ".agent-config" / "backups",
            )
        atomic_write(self.output_path, preview["facts"], _parse_declaration)
        return {
            "path": str(self.output_path),
            "backup": str(backup) if backup else None,
            "preview": preview,
        }

    def lookup_docs(self, target: str, path: str, *, refresh: bool = False) -> dict[str, Any]:
        return self.docs_resolver.resolve(target, path, refresh=refresh)


def _error_status(error: ConfigError) -> HTTPStatus:
    if error.code == "IMPORT_OUTPUT_EXISTS":
        return HTTPStatus.CONFLICT
    if error.code in {"DOC_LOOKUP_FAILED", "TARGET_WRITE_FAILED"}:
        return HTTPStatus.BAD_GATEWAY
    return HTTPStatus.BAD_REQUEST


def create_server(
    state: WebUIState,
    *,
    port: int,
    token: str,
    host: str = "127.0.0.1",
) -> ThreadingHTTPServer:
    """创建仅监听回环地址、API 需会话令牌的 HTTP 服务。"""

    class Handler(BaseHTTPRequestHandler):
        server_version = "aiconfig-ui"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _headers(self, status: HTTPStatus, content_type: str, length: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()

        def _send_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self._headers(status, "application/json; charset=utf-8", len(body))
            self.wfile.write(body)

        def _send_error(self, error: ConfigError) -> None:
            self._send_json(
                {"error": {"code": error.code, "message": error.message, "location": error.location}},
                _error_status(error),
            )

        def _authorized(self) -> bool:
            if not self.path.startswith("/api/"):
                return True
            if secrets.compare_digest(self.headers.get("X-Aiconfig-Token", ""), token):
                return True
            self._send_json(
                {"error": {"code": "UI_TOKEN_REQUIRED", "message": "缺少或无效的本地 UI 会话令牌。"}},
                HTTPStatus.FORBIDDEN,
            )
            return False

        def _body(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ConfigError("UI_REQUEST_INVALID", "Content-Length 无效。") from exc
            if length < 0 or length > 1024 * 1024:
                raise ConfigError("UI_REQUEST_INVALID", "请求体超过 1 MiB 限制。")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeError, ValueError) as exc:
                raise ConfigError("UI_REQUEST_INVALID", "请求体必须是 JSON 对象。") from exc
            if not isinstance(value, dict):
                raise ConfigError("UI_REQUEST_INVALID", "请求体必须是 JSON 对象。")
            return value

        def do_GET(self) -> None:
            if not self._authorized():
                return
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/state":
                    self._send_json(state.snapshot())
                    return
                if parsed.path == "/api/preview":
                    self._send_json(state.preview())
                    return
                if parsed.path == "/api/docs":
                    query = parse_qs(parsed.query)
                    target = query.get("target", [""])[0]
                    path = query.get("path", [""])[0]
                    refresh = query.get("refresh", ["0"])[0] == "1"
                    self._send_json(state.lookup_docs(target, path, refresh=refresh))
                    return
                asset = "index.html" if parsed.path in {"", "/"} else parsed.path.removeprefix("/")
                if asset not in {"index.html", "styles.css", "app.js"}:
                    self._send_json({"error": {"code": "NOT_FOUND", "message": "页面不存在。"}}, HTTPStatus.NOT_FOUND)
                    return
                path = UI_ROOT / asset
                body = path.read_bytes()
                self._headers(HTTPStatus.OK, CONTENT_TYPES.get(path.suffix, "application/octet-stream"), len(body))
                self.wfile.write(body)
            except ConfigError as exc:
                self._send_error(exc)
            except OSError as exc:
                self._send_error(ConfigError("UI_ASSET_FAILED", f"无法读取界面资源：{exc}"))

        def do_POST(self) -> None:
            if not self._authorized():
                return
            parsed = urlparse(self.path)
            try:
                body = self._body()
                if parsed.path == "/api/decision":
                    self._send_json(
                        state.update_decision(
                            body.get("target"),
                            body.get("path"),
                            body.get("decision"),
                        )
                    )
                    return
                if parsed.path == "/api/generate":
                    force = body.get("force", False)
                    if not isinstance(force, bool):
                        raise ConfigError("UI_REQUEST_INVALID", "force 必须是布尔值。")
                    self._send_json(state.generate(force=force))
                    return
                self._send_json({"error": {"code": "NOT_FOUND", "message": "接口不存在。"}}, HTTPStatus.NOT_FOUND)
            except ConfigError as exc:
                self._send_error(exc)

    return ThreadingHTTPServer((host, port), Handler)


def serve_ui(plan_path: Path, output_path: Path, *, port: int = 8765, open_browser: bool = False) -> None:
    state = WebUIState(plan_path, output_path)
    state.snapshot()
    token = secrets.token_urlsafe(24)
    try:
        server = create_server(state, port=port, token=token)
    except OSError as exc:
        raise ConfigError("UI_SERVER_FAILED", f"无法启动本地 UI：{exc}") from exc
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/?token={token}"
    print(f"本地审阅界面：{url}", flush=True)
    print("仅监听 127.0.0.1；按 Ctrl-C 停止。", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
