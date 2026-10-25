"""Small local HTTP server. All third-party model calls stay on this backend."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import socket
import threading
from urllib.parse import unquote, urlsplit

from .backend import AppError, CampusService, MAX_UPLOAD_BYTES, Settings, UPLOAD_PATTERN


def safe_static_path(root: Path, request_path: str) -> Path | None:
    try:
        decoded = unquote(request_path, errors="strict")
        if "\x00" in decoded or "\\" in decoded:
            return None
        relative = "index.html" if decoded == "/" else decoded.lstrip("/")
        target = (root / relative).resolve()
        target.relative_to(root.resolve())
        if any(part.startswith(".") for part in Path(relative).parts):
            return None
        return target if target.is_file() else None
    except (ValueError, OSError, UnicodeError):
        return None


class CampusHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class CampusHandler(BaseHTTPRequestHandler):
    server_version = "CampusLens"
    sys_version = ""

    def __init__(self, *args, service: CampusService, extraction_slots: threading.BoundedSemaphore, **kwargs):
        self.service = service
        self.extraction_slots = extraction_slots
        super().__init__(*args, **kwargs)

    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def log_message(self, format_string, *args):
        # Never log request headers, uploaded data, model responses or API keys.
        pass

    def _headers(self, status: int, media_type: str, length: int, *, cache: str = "no-store"):
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()

    def _json(self, status: int, value: dict):
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(payload))
        self.wfile.write(payload)

    def _error(self, exc: AppError):
        self._json(exc.status, {"error": exc.message, "code": exc.code})

    def _check_host(self):
        try:
            host = urlsplit("//" + self.headers.get("Host", ""))
            valid = host.hostname in {"127.0.0.1", "localhost"} and (host.port or 80) == self.server.server_port
        except ValueError:
            valid = False
        if not valid:
            raise AppError("请使用本机 localhost 或 127.0.0.1 地址访问。", "invalid_host", 403)

    def _check_origin(self):
        # Only same-origin browser writes; command-line clients may omit Origin.
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme != "http" or parsed.netloc.lower() != self.headers.get("Host", "").lower():
                raise AppError("请从本机 CampusLens 页面进行操作。", "invalid_origin", 403)
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise AppError("请从本机 CampusLens 页面进行操作。", "invalid_origin", 403)

    def _read(self, max_length: int) -> bytes:
        if self.headers.get("Transfer-Encoding"):
            raise AppError("不支持此上传方式，请从页面重新上传。", "unsupported_transfer")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            raise AppError("上传请求缺少有效长度。", "invalid_content_length", 411) from None
        if length <= 0:
            raise AppError("请求内容为空。", "empty_body")
        if length > max_length:
            self.close_connection = True
            raise AppError("上传内容过大，请缩小图片或内容后重试。", "body_too_large", 413)
        try:
            body = self.rfile.read(length)
        except (socket.timeout, TimeoutError):
            raise AppError("上传超时，请重新上传。", "upload_timeout", 408) from None
        if len(body) != length:
            raise AppError("上传未完成，请重试。", "incomplete_upload")
        return body

    def do_GET(self):
        try:
            self._check_host()
            path = urlsplit(self.path).path
            if path == "/api/config":
                self._json(200, self.service.config())
            elif path == "/api/events":
                self._json(200, {"events": self.service.store.list()})
            elif path == "/api/health":
                self._json(200, {"status": "ok"})
            elif path.startswith("/api/"):
                raise AppError("找不到此 API。", "not_found", 404)
            elif path.startswith("/uploads/"):
                matched = UPLOAD_PATTERN.fullmatch(path)
                if not matched:
                    raise AppError("找不到这张海报。", "not_found", 404)
                self._file(self.service.settings.uploads / matched.group(1), "image/jpeg", cache="private, max-age=3600")
            else:
                target = safe_static_path(self.service.settings.root / "static", path)
                if target is None:
                    raise AppError("找不到此页面。", "not_found", 404)
                media_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                if media_type.startswith("text/") or media_type in ("application/javascript", "application/json"):
                    media_type += "; charset=utf-8"
                self._file(target, media_type)
        except AppError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._error(AppError("本机服务发生错误，请稍后重试。", "internal_error", 500))

    def _file(self, target: Path, media_type: str, *, cache: str = "no-cache"):
        if not target.is_file():
            raise AppError("找不到此文件。", "not_found", 404)
        payload = target.read_bytes()
        self._headers(200, media_type, len(payload), cache=cache)
        self.wfile.write(payload)

    def do_POST(self):
        try:
            self._check_host()
            self._check_origin()
            path = urlsplit(self.path).path
            if path == "/api/extract":
                if not self.extraction_slots.acquire(blocking=False):
                    raise AppError("正在分析其他海报，请稍后再试。", "extraction_busy", 429)
                try:
                    payload = self._read(MAX_UPLOAD_BYTES)
                    self._json(200, self.service.extract(payload, self.headers.get("Content-Type", "")))
                finally:
                    self.extraction_slots.release()
            elif path == "/api/upload":
                payload = self._read(MAX_UPLOAD_BYTES)
                self._json(201, self.service.upload(payload, self.headers.get("Content-Type", "")))
            elif path == "/api/events":
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise AppError("请以 JSON 格式提交活动。", "unsupported_content_type", 415)
                try:
                    payload = json.loads(self._read(128 * 1024).decode("utf-8"))
                except (UnicodeDecodeError, ValueError, RecursionError):
                    raise AppError("活动数据无法读取，请检查后重试。", "invalid_json") from None
                self._json(201, {"event": self.service.add_event(payload)})
            else:
                raise AppError("找不到此 API。", "not_found", 404)
        except AppError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._error(AppError("本机服务发生错误，请稍后重试。", "internal_error", 500))


def create_server(settings: Settings, host: str = "127.0.0.1", port: int = 8000) -> CampusHTTPServer:
    service = CampusService(settings)
    handler = partial(CampusHandler, service=service, extraction_slots=threading.BoundedSemaphore(2))
    return CampusHTTPServer((host, port), handler)


def main():
    parser = argparse.ArgumentParser(description="CampusLens local poster-to-campus-map app")
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not (1 <= args.port <= 65535):
        parser.error("port must be between 1 and 65535")
    settings = Settings(Path(__file__).resolve().parent.parent)
    try:
        server = create_server(settings, args.host, args.port)
    except OSError:
        parser.exit(1, f"无法启动本机服务，端口 {args.port} 可能已被占用。可尝试 --port 8001。\n")
    except (RuntimeError, AppError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"CampusLens: http://{args.host}:{args.port}")
    print("Gemma API: " + ("configured" if settings.credentials()[0] else "请在 .env 填写 GEMINI_API_KEY"))
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nCampusLens stopped.")
    finally:
        server.server_close()
