# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Live web dashboard for the test board.

    python3 -m gr00t_ready serve robots/<name> [--host 127.0.0.1] [--port 8321]

Stdlib-only HTTP server. Endpoints:
  GET  /                       the dashboard page (gr00t_ready/web/index.html — edit freely)
  GET  /api/board              board state as JSON, re-read from disk on every request
  POST /api/upload?item=<ID>&name=<filename>
                               save evidence media (raw request body) to
                               robots/<name>/results/media/<ID>/<filename>
  GET  /media/<ID>/<filename>  serve saved evidence media

Media lives under results/media/, one folder per criteria item, so the whole
evidence set can be synced to cloud storage as a single tree.

The page polls /api/board, so recording a result (or editing BLOCKERS.md /
adding a test file / uploading media) shows up live without restarting.
"""

from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO
from urllib.parse import parse_qs, unquote, urlparse

from .board import board_data
from .loader import load_criteria, load_results

WEB_DIR = Path(__file__).resolve().parent / "web"
ITEM_ID_RE = re.compile(r"^(?:HW|SW|NT)-[A-Z]+-\d+$")
MAX_UPLOAD_BYTES = 2 * 1024**3  # 2 GB — stability-run videos can be large


def _safe_filename(name: str) -> str:
    name = unquote(name).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return name or "upload.bin"


def _write_upload(body: BinaryIO, dest: Path, length: int) -> bool:
    """Write exactly length bytes, removing the destination on interruption."""
    remaining, chunk = length, 1024 * 1024
    try:
        with dest.open("wb") as f:
            while remaining > 0:
                data = body.read(min(chunk, remaining))
                if not data:
                    break
                f.write(data)
                remaining -= len(data)
    except (ConnectionError, OSError):
        dest.unlink(missing_ok=True)
        return False
    if remaining:
        dest.unlink(missing_ok=True)
        return False
    return True


def make_handler(robot_dir: Path, upload_password: str):
    media_root = robot_dir / "results" / "media"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/api/board":
                try:
                    categories = load_criteria()
                    evaluation = load_results(robot_dir)
                    payload = board_data(categories, evaluation, robot_dir)
                    self._send(200, "application/json",
                               json.dumps(payload).encode())
                except Exception as e:  # surface load errors in the UI
                    self._send(500, "application/json",
                               json.dumps({"error": str(e)}).encode())
            elif url.path == "/":
                self._send(200, "text/html; charset=utf-8",
                           (WEB_DIR / "index.html").read_bytes())
            elif url.path.startswith("/media/"):
                self._serve_media(url.path)
            elif url.path.startswith("/output/"):
                name = _safe_filename(url.path.split("/output/", 1)[1])
                target = robot_dir / "tests" / "output" / name
                if target.is_file() and target.suffix in (".txt", ".log"):
                    self._send(200, "text/plain; charset=utf-8", target.read_bytes())
                else:
                    self._send(404, "text/plain", b"not found")
            else:
                self._send(404, "text/plain", b"not found")

        def do_POST(self):
            url = urlparse(self.path)
            if url.path != "/api/upload":
                self._send(404, "application/json", b'{"error": "not found"}')
                return
            supplied = self.headers.get("X-Upload-Password") or ""
            if not hmac.compare_digest(supplied, upload_password):
                self._send(401, "application/json",
                           b'{"error": "invalid or missing upload password"}')
                return
            q = parse_qs(url.query)
            item_id = (q.get("item") or [""])[0]
            filename = _safe_filename((q.get("name") or [""])[0])
            if not ITEM_ID_RE.match(item_id):
                self._send(400, "application/json",
                           b'{"error": "invalid or missing item id"}')
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_UPLOAD_BYTES:
                self._send(400, "application/json",
                           b'{"error": "missing or oversized body"}')
                return
            dest_dir = media_root / item_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
            stem, suffix, n = dest.stem, dest.suffix, 1
            while dest.exists():  # never overwrite existing evidence
                dest = dest_dir / f"{stem}_{n}{suffix}"
                n += 1
            if not _write_upload(self.rfile, dest, length):
                self._send(400, "application/json",
                           b'{"error": "incomplete upload body"}')
                return
            self._send(200, "application/json", json.dumps(
                {"saved": f"/media/{item_id}/{dest.name}"}).encode())

        def _serve_media(self, path: str):
            parts = [unquote(p) for p in path.split("/")[2:]]
            if len(parts) != 2 or not ITEM_ID_RE.match(parts[0]):
                self._send(404, "text/plain", b"not found")
                return
            target = media_root / parts[0] / _safe_filename(parts[1])
            if not target.is_file():
                self._send(404, "text/plain", b"not found")
                return
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            size = target.stat().st_size
            start, end = 0, size - 1
            rng = self.headers.get("Range")
            m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
            partial = bool(m and rng)
            if partial:
                if m.group(1):
                    start = int(m.group(1))
                    if m.group(2):
                        end = min(int(m.group(2)), size - 1)
                elif m.group(2):  # suffix range: last N bytes
                    start = max(0, size - int(m.group(2)))
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if partial:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with target.open("rb") as f:  # stream in chunks; files can be GBs
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    data = f.read(min(1024 * 1024, remaining))
                    if not data:
                        break
                    try:
                        self.wfile.write(data)
                    except (BrokenPipeError, ConnectionResetError):
                        return  # client stopped the video / closed the tab
                    remaining -= len(data)

        def _send(self, code: int, ctype: str, body: bytes):
            # A polling dashboard cancels in-flight fetches every 2 s, so the
            # client often closes the socket before we finish writing. That
            # surfaces as BrokenPipe/ConnectionReset — normal, not an error.
            try:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # client disconnected mid-response

        def log_message(self, fmt, *args):  # quiet the request log
            pass

    return Handler


def serve(robot_dir: Path, host: str = "127.0.0.1", port: int = 8321,
          upload_password: str | None = None) -> None:
    evaluation = load_results(robot_dir)
    if not upload_password:
        upload_password = secrets.token_urlsafe(9)
        print(f"upload password (auto-generated, no --upload-password given): {upload_password}",
              flush=True)
    server = ThreadingHTTPServer((host, port),
                                 make_handler(robot_dir, upload_password))
    display_host = "localhost" if host in ("127.0.0.1", "::1") else host
    print(
        f"Dashboard for {robot_dir.name} (evaluation v{evaluation.evaluation_version}): "
        f"http://{display_host}:{port}/  (Ctrl-C to stop)",
        flush=True,
    )
    print("uploads require the password (📎 button will prompt once per browser session)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
