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
