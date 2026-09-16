#!/usr/bin/env python3
"""TaskBoard — minimal demo app for verification skill development.

Isolation:
  TASKBOARD_PORT      listen port (default 8765)
  TASKBOARD_HOST      bind host (default 127.0.0.1)
  TASKBOARD_DATA_DIR  JSON store directory (default ./data)
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("TASKBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("TASKBOARD_PORT", "8765"))
DATA_DIR = Path(os.environ.get("TASKBOARD_DATA_DIR", str(Path(__file__).resolve().parent / "data")))
STATIC_DIR = Path(__file__).resolve().parent / "static"
BUILD_ID = os.environ.get("TASKBOARD_BUILD_ID", "demo-1")


def _tasks_path() -> Path:
    return DATA_DIR / "tasks.json"


def load_tasks() -> list[dict]:
    path = _tasks_path()
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _tasks_path().with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
        f.write("\n")
    tmp.replace(_tasks_path())


class Handler(BaseHTTPRequestHandler):
    server_version = f"TaskBoard/{BUILD_ID}"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[taskboard] {self.address_string()} {fmt % args}", flush=True)

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._json(
                200,
                {
                    "ok": True,
                    "app": "TaskBoard",
                    "build": BUILD_ID,
                    "port": PORT,
                    "data_dir": str(DATA_DIR.resolve()),
                    "task_count": len(load_tasks()),
                },
            )
            return

        if path == "/api/tasks":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0].strip().lower()
            tasks = load_tasks()
            if q:
                tasks = [
                    t
                    for t in tasks
                    if q in t.get("title", "").lower() or q in t.get("body", "").lower()
                ]
            self._json(200, {"tasks": tasks, "query": q})
            return

        if path == "/" or path == "/index.html":
            self._serve_static("index.html", "text/html; charset=utf-8")
            return

        if path.startswith("/static/"):
            name = path[len("/static/") :]
            if ".." in name or name.startswith("/"):
                self._json(400, {"error": "bad path"})
                return
            ctype = {
                ".js": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".html": "text/html; charset=utf-8",
            }.get(Path(name).suffix, "application/octet-stream")
            self._serve_static(name, ctype)
            return

        # convenience: /app.js /app.css at root too
        if path in ("/app.js", "/app.css"):
            ctype = (
                "application/javascript; charset=utf-8"
                if path.endswith(".js")
                else "text/css; charset=utf-8"
            )
            self._serve_static(path.lstrip("/"), ctype)
            return

        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            data = self._read_json()
            title = str(data.get("title", "")).strip()
            body = str(data.get("body", "")).strip()
            if not title:
                self._json(400, {"error": "title required"})
                return
            task = {
                "id": str(uuid.uuid4()),
                "title": title,
                "body": body,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            tasks = load_tasks()
            tasks.insert(0, task)
            save_tasks(tasks)
            self._json(201, {"task": task})
            return

        if parsed.path == "/api/seed":
            # verification helper: seed demo tasks into disposable data dir
            data = self._read_json()
            tasks = data.get("tasks")
            if not isinstance(tasks, list):
                self._json(400, {"error": "tasks array required"})
                return
            normalized = []
            for t in tasks:
                normalized.append(
                    {
                        "id": str(t.get("id") or uuid.uuid4()),
                        "title": str(t.get("title", "")).strip(),
                        "body": str(t.get("body", "")).strip(),
                        "created_at": str(t.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    }
                )
            save_tasks(normalized)
            self._json(200, {"ok": True, "count": len(normalized)})
            return

        self._json(404, {"error": "not found"})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        m = re.fullmatch(r"/api/tasks/([0-9a-fA-F-]{36})", parsed.path)
        if not m:
            self._json(404, {"error": "not found"})
            return
        tid = m.group(1)
        tasks = load_tasks()
        next_tasks = [t for t in tasks if t.get("id") != tid]
        if len(next_tasks) == len(tasks):
            self._json(404, {"error": "task not found"})
            return
        save_tasks(next_tasks)
        self._json(200, {"ok": True, "id": tid})

    def _serve_static(self, name: str, content_type: str) -> None:
        path = STATIC_DIR / name
        if not path.is_file():
            self._json(404, {"error": f"missing {name}"})
            return
        body = path.read_bytes()
        self._send(200, body, content_type)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _tasks_path().exists():
        save_tasks([])
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        f"[taskboard] ready url=http://{HOST}:{PORT} data_dir={DATA_DIR.resolve()} build={BUILD_ID}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[taskboard] shutting down", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    main()
