import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from backend.server import Handler


def send(url, payload):
    request = urllib.request.Request(
        url, json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read().decode())


def test_http_runs_loop_and_reports_synthetic_mode():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(base + "/api/health") as response:
            assert json.loads(response.read())["mode"] == "synthetic"
        code, result = send(base + "/api/run", {"topic": "example"})
        assert code == 200
        assert result["mode"] == "synthetic"
        assert result["result"]["stop_reason"] == "condition_met"
        assert len(result["result"]["rounds"]) == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_invalid_payload():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            send(base + "/api/run", {"topic": "", "max_rounds": 500})
            assert False, "expected HTTP 400"
        except urllib.error.HTTPError as error:
            assert error.code == 400
            assert "error" in json.loads(error.read())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_http_serves_ui_and_rejects_unknown_paths():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        for path, text in [("/", "LOOP"), ("/app.js", "render"), ("/styles.css", "body")]:
            with urllib.request.urlopen(base + path) as response:
                assert response.status == 200
                assert text.encode() in response.read()
        for path in ("/unknown", "/../README.md"):
            try:
                urllib.request.urlopen(base + path)
                assert False, "expected 404"
            except urllib.error.HTTPError as exc:
                assert exc.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_rejects_non_integer_rounds():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        for invalid in ("5", True, 0, 11):
            try:
                send(base + "/api/run", {"topic": "example", "max_rounds": invalid})
                assert False, "expected HTTP 400"
            except urllib.error.HTTPError as exc:
                assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
