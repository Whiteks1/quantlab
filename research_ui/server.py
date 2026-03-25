import http.server
import json
import socketserver
import os
import sys
from pathlib import Path

PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from quantlab.cli.paper_sessions import build_paper_sessions_health


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/paper-sessions-health'):
            payload, status = build_paper_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)

        # Redirect root to research_ui/index.html to ensure relative asset paths work
        if self.path == '/' or self.path == '':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        return super().do_GET()

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def build_paper_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    paper_root = root / "outputs" / "paper_sessions"

    if not paper_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(paper_root),
            "message": "No paper session root found yet.",
            "total_sessions": 0,
            "status_counts": {},
            "latest_session_id": None,
            "latest_session_status": None,
            "latest_session_at": None,
            "latest_issue_session_id": None,
            "latest_issue_status": None,
            "latest_issue_at": None,
            "latest_issue_error_type": None,
        }, 200

    try:
        payload = build_paper_sessions_health(paper_root)
        payload["status"] = "ok"
        payload["available"] = True
        return payload, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(paper_root),
            "message": str(exc),
        }, 500

def run_server():
    # Ensure we are in the project root
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "research_ui":
        os.chdir("..")
        print("Changed directory to project root.")
    
    port = PORT
    max_retries = 5
    httpd = None

    while max_retries > 0:
        try:
            httpd = socketserver.TCPServer(("", port), DashboardHandler)
            break
        except OSError:
            print(f"Port {port} is busy, trying {port + 1}...")
            port += 1
            max_retries -= 1

    if not httpd:
        print("Error: Could not find an available port.")
        sys.exit(1)

    print(f"\n--- QuantLab Research Dashboard Dev Server ---")
    print(f"Serving from: {os.getcwd()}")
    print(f"URL: http://localhost:{port}")
    print(f"Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    run_server()
