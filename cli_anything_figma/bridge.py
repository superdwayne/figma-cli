"""Figma Plugin Bridge — local relay server for CLI ↔ Figma plugin communication.

Architecture:
  1. CLI posts commands to localhost relay server
  2. Figma plugin (running in browser) polls the relay for pending commands
  3. Plugin executes commands in Figma and posts results back
  4. CLI picks up results

This enables creating/modifying actual Figma design nodes from the terminal.
"""
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from collections import deque

# Shared state between server threads
_command_queue: deque[dict] = deque()
_result_store: dict[str, dict] = {}
_server_instance: HTTPServer | None = None
_cmd_counter = 0


def _next_cmd_id() -> str:
    global _cmd_counter
    _cmd_counter += 1
    return f"cmd-{_cmd_counter}-{int(time.time())}"


class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for the bridge relay server."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, status: int, data: Any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok", "pending": len(_command_queue)})

        elif self.path == "/poll":
            # Plugin polls for pending commands
            if _command_queue:
                cmd = _command_queue.popleft()
                self._json_response(200, cmd)
            else:
                self._json_response(200, {"type": "noop"})

        elif self.path.startswith("/result/"):
            cmd_id = self.path.split("/result/")[1]
            if cmd_id in _result_store:
                self._json_response(200, _result_store.pop(cmd_id))
            else:
                self._json_response(404, {"error": "Not found"})

        else:
            self._json_response(404, {"error": "Unknown endpoint"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if self.path == "/command":
            # CLI posts a command
            try:
                data = json.loads(body)
                cmd_id = _next_cmd_id()
                data["id"] = cmd_id
                _command_queue.append(data)
                self._json_response(200, {"id": cmd_id, "queued": True})
            except json.JSONDecodeError:
                self._json_response(400, {"error": "Invalid JSON"})

        elif self.path == "/result":
            # Plugin posts a result
            try:
                data = json.loads(body)
                cmd_id = data.get("id")
                if cmd_id:
                    _result_store[cmd_id] = data
                    self._json_response(200, {"received": True})
                else:
                    self._json_response(400, {"error": "Missing command id"})
            except json.JSONDecodeError:
                self._json_response(400, {"error": "Invalid JSON"})

        else:
            self._json_response(404, {"error": "Unknown endpoint"})


def start_bridge(port: int = 9480) -> HTTPServer:
    """Start the bridge relay server."""
    global _server_instance
    server = HTTPServer(("127.0.0.1", port), BridgeHandler)
    _server_instance = server
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def stop_bridge():
    """Stop the bridge relay server."""
    global _server_instance
    if _server_instance:
        _server_instance.shutdown()
        _server_instance = None


def send_command(cmd_type: str, params: dict, port: int = 9480, timeout: float = 30.0) -> dict:
    """Send a command to the bridge and wait for the result."""
    import requests

    # Post the command
    resp = requests.post(
        f"http://127.0.0.1:{port}/command",
        json={"type": cmd_type, "params": params},
        timeout=5,
    )
    resp.raise_for_status()
    cmd_id = resp.json()["id"]

    # Poll for result
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/result/{cmd_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        time.sleep(0.3)

    return {"error": "Timeout waiting for plugin response", "id": cmd_id}
