"""Local-only HTTP API to demonstrate independent LOOP behavior.

No company endpoints, model APIs or real project data are used.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .examples.run_demo import run

UI = Path(__file__).resolve().parents[1] / "ui-demo"
MAX_BODY = 8192


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self._json(200, {"status": "ok", "mode": "synthetic"})
        allowed = {"/": "index.html", "/styles.css": "styles.css", "/app.js": "app.js"}
        name = allowed.get(path)
        if not name:
            return self._json(404, {"error": "Not found"})
        try:
            data = (UI / name).read_bytes()
        except OSError:
            return self._json(500, {"error": "Missing demo asset"})
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(name)[0] or "text/plain")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/run":
            return self._json(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= MAX_BODY:
                raise ValueError("Request size must be 1..8192 bytes")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object")
            topic = payload.get("topic")
            if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 300:
                raise ValueError("topic must be 1..300 characters")
            max_rounds = payload.get("max_rounds", 5)
            if isinstance(max_rounds, bool) or not isinstance(max_rounds, int) or not 1 <= max_rounds <= 10:
                raise ValueError("max_rounds must be an integer 1..10")
            result = run(topic.strip(), max_rounds)
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        return self._json(200, {"mode": "synthetic", "result": result.__dict__})


def serve(host="127.0.0.1", port=8080):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"LOOP demo at http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    serve(port=args.port)
