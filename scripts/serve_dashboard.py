from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime, time as time_of_day, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - zoneinfo is expected on modern Python
    ZoneInfo = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_USERNAME = "dashboard"
DEFAULT_INDEX = ROOT / "dashboard" / "index.html"
DEFAULT_REBUILD_TIME = "13:45"
DEFAULT_REBUILD_TIMEZONE = "Asia/Shanghai"
DEFAULT_REBUILD_COMMAND = [
    sys.executable,
    str(ROOT / "src" / "risk_dashboard.py"),
    "--data-source",
    "twse",
    "--model-portfolio",
    "--model-build-date",
    "2026-06-03",
    "--model-method",
    "multi-factor-shrink",
    "--ai-tilt",
    "moderate",
    "--market-source",
    "public-close",
    "--market-mode",
    "close",
    "--execute-simulated-trades",
]


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "TWQuantDashboard/1.0"
    auth_realm: ClassVar[str] = "TWQuantDashboard"
    auth_username: ClassVar[str] = DEFAULT_USERNAME
    auth_password: ClassVar[str] = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    @staticmethod
    def _dashboard_version() -> dict[str, str | int]:
        content = DEFAULT_INDEX.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        modified_at = datetime.fromtimestamp(DEFAULT_INDEX.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        return {
            "version": digest,
            "generated_at": modified_at,
            "content_length": len(content),
        }

    def _send_dashboard_version(self) -> None:
        payload = json.dumps(self._dashboard_version(), ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_plain(self, status: HTTPStatus, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _require_auth(self) -> bool:
        if not self.auth_password:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            self._send_auth_request()
            return False
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        except Exception:
            self._send_auth_request()
            return False
        username, _, password = decoded.partition(":")
        if username != self.auth_username or password != self.auth_password:
            self._send_auth_request()
            return False
        return True

    def _send_auth_request(self) -> None:
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", f'Basic realm="{self.auth_realm}"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Authentication required.\n")

    def do_GET(self) -> None:  # noqa: N802
        if not self._require_auth():
            return
        path = urlparse(self.path).path
        if path == "/":
            return self._serve_index()
        if path == "/healthz":
            return self._send_plain(HTTPStatus.OK, "ok\n")
        if path == "/version.json":
            return self._send_dashboard_version()
        return super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._require_auth():
            return
        path = urlparse(self.path).path
        if path == "/":
            return self._serve_index(head_only=True)
        if path == "/healthz":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "3")
            self.end_headers()
            return
        if path == "/version.json":
            payload = json.dumps(self._dashboard_version(), ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            return
        return super().do_HEAD()

    def _serve_index(self, head_only: bool = False) -> None:
        content = DEFAULT_INDEX.read_bytes()
        version = hashlib.sha256(content).hexdigest()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("ETag", f'"{version}"')
        self.send_header("X-Dashboard-Version", version)
        self.end_headers()
        if not head_only:
            self.wfile.write(content)


def parse_time_of_day(value: str) -> time_of_day:
    try:
        hour_text, minute_text = value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except Exception as exc:
        raise ValueError("重建时间必须是 HH:MM 格式，例如 13:45。") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("重建时间必须落在 00:00 到 23:59 之间。")
    return time_of_day(hour=hour, minute=minute)


def load_timezone(name: str):
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(name)
    except Exception:
        return None


def parse_command(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_REBUILD_COMMAND)
    return shlex.split(value)


def run_rebuild(command: list[str]) -> None:
    print(f"[rebuild] 开始重建：{' '.join(command)}", flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout.rstrip(), flush=True)
    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr.rstrip(), flush=True)
        raise RuntimeError(f"Dashboard 重建失败，退出码 {completed.returncode}。")
    if completed.stderr:
        print(completed.stderr.rstrip(), flush=True)
    print("[rebuild] 重建完成。", flush=True)


def next_run_time(now: datetime, rebuild_clock: time_of_day):
    candidate = now.replace(
        hour=rebuild_clock.hour,
        minute=rebuild_clock.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def start_rebuild_loop(command: list[str], rebuild_clock: time_of_day, timezone_name: str) -> threading.Thread:
    timezone = load_timezone(timezone_name)

    def loop() -> None:
        while True:
            try:
                run_rebuild(command)
            except Exception as exc:
                print(f"[rebuild] {exc}", flush=True)

            now = datetime.now(timezone) if timezone else datetime.now()
            target = next_run_time(now, rebuild_clock)
            sleep_seconds = max(1.0, (target - now).total_seconds())
            print(f"[rebuild] 下次重建时间：{target.isoformat(timespec='minutes')}", flush=True)
            time.sleep(sleep_seconds)

    thread = threading.Thread(target=loop, name="dashboard-rebuild-loop", daemon=True)
    thread.start()
    return thread


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the generated dashboard HTML.")
    parser.add_argument("--host", default=os.getenv("DASHBOARD_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", DEFAULT_PORT)))
    parser.add_argument("--username", default=os.getenv("DASHBOARD_BASIC_AUTH_USER", DEFAULT_USERNAME))
    parser.add_argument("--password", default=os.getenv("DASHBOARD_BASIC_AUTH_PASSWORD", ""))
    parser.add_argument(
        "--rebuild-command",
        default=os.getenv("DASHBOARD_REBUILD_COMMAND", ""),
        help="重建 Dashboard 的命令；不填时使用默认公开收盘重建命令。",
    )
    parser.add_argument(
        "--rebuild-time",
        default=os.getenv("DASHBOARD_REBUILD_TIME", DEFAULT_REBUILD_TIME),
        help="每天固定重建的时间，格式 HH:MM。",
    )
    parser.add_argument(
        "--timezone",
        default=os.getenv("DASHBOARD_TIMEZONE", DEFAULT_REBUILD_TIMEZONE),
        help="重建时间对应的时区名称。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rebuild_clock = parse_time_of_day(args.rebuild_time)
    rebuild_command = parse_command(args.rebuild_command)
    DashboardHandler.auth_username = args.username
    DashboardHandler.auth_password = args.password
    start_rebuild_loop(rebuild_command, rebuild_clock, args.timezone)
    httpd = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving {DEFAULT_INDEX} on http://{args.host}:{args.port}")
    print(f"Daily rebuild scheduled at {rebuild_clock.strftime('%H:%M')} {args.timezone}.")
    if args.password:
        print("Basic auth enabled.")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
