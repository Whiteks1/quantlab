import http.server
import json
import socketserver
import os
import subprocess
import sys
from pathlib import Path

PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from quantlab.cli.broker_order_validations import (
    build_broker_submission_alerts,
    build_broker_submission_health,
)
from quantlab.cli.hyperliquid_submit_sessions import (
    build_hyperliquid_submission_alerts,
    build_hyperliquid_submission_health,
)
from quantlab.cli.paper_sessions import build_paper_sessions_health


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/paper-sessions-health'):
            payload, status = build_paper_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if self.path.startswith('/api/broker-submissions-health'):
            payload, status = build_broker_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if self.path.startswith('/api/hyperliquid-surface'):
            payload, status = build_hyperliquid_surface_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if self.path.startswith('/api/stepbit-workspace'):
            payload, status = build_stepbit_workspace_payload(PROJECT_ROOT)
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


def build_broker_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    broker_root = root / "outputs" / "broker_order_validations"

    if not broker_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(broker_root),
            "message": "No broker order-validation root found yet.",
            "total_sessions": 0,
            "approved_sessions": 0,
            "submit_gate_sessions": 0,
            "submit_response_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "alerts": [],
        }, 200

    try:
        health = build_broker_submission_health(broker_root)
        alerts = build_broker_submission_alerts(broker_root)
        return {
            **health,
            "status": "ok",
            "available": True,
            "alert_status": alerts.get("alert_status", "ok"),
            "has_alerts": alerts.get("has_alerts", False),
            "alert_counts": alerts.get("alert_counts", {}),
            "alerts": alerts.get("alerts", []),
        }, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(broker_root),
            "message": str(exc),
        }, 500


def build_hyperliquid_surface_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    submit_root = root / "outputs" / "hyperliquid_submits"
    search_roots = [
        root / "outputs",
        root / "tmp",
        root.parent / "tmp",
    ]

    surfaces = {
        "preflight": {
            "implemented": True,
            "artifact_name": "broker_preflight.json",
            "summary_key": "market_supported",
        },
        "account_readiness": {
            "implemented": True,
            "artifact_name": "hyperliquid_account_readiness.json",
            "summary_key": "readiness_allowed",
        },
        "signed_action": {
            "implemented": True,
            "artifact_name": "hyperliquid_signed_action.json",
            "summary_key": "readiness_allowed",
        },
        "submit_response": {
            "implemented": True,
            "artifact_name": "hyperliquid_submit_response.json",
            "summary_key": "submit_state",
        },
        "order_status": {
            "implemented": True,
            "artifact_name": "hyperliquid_order_status.json",
            "summary_key": "normalized_state",
        },
        "continuous_supervision": {
            "implemented": True,
            "artifact_name": "hyperliquid_supervision.json",
            "summary_key": "supervision_state",
        },
    }

    latest_artifacts: dict[str, dict[str, object] | None] = {}
    for key, spec in surfaces.items():
        latest_artifacts[key] = _find_latest_hyperliquid_artifact(
            search_roots,
            spec["artifact_name"],
        )

    latest_ready_artifact = next(
        (
            artifact
            for artifact in (
                latest_artifacts["continuous_supervision"],
                latest_artifacts["order_status"],
                latest_artifacts["submit_response"],
                latest_artifacts["signed_action"],
                latest_artifacts["account_readiness"],
                latest_artifacts["preflight"],
            )
            if artifact
        ),
        None,
    )

    if submit_root.exists():
        try:
            submit_health = build_hyperliquid_submission_health(submit_root)
            submit_alerts = build_hyperliquid_submission_alerts(submit_root)
        except Exception as exc:  # noqa: BLE001
            submit_health = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_status_known_sessions": 0,
                "status_counts": {},
                "submit_state_counts": {},
                "order_state_counts": {},
                "latest_submit_session_id": None,
                "latest_submit_state": None,
                "latest_order_state": None,
                "latest_submit_at": None,
                "latest_issue_session_id": None,
                "latest_issue_code": None,
                "latest_issue_at": None,
            }
            submit_alerts = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "generated_at": None,
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_state_counts": {},
                "alert_status": "error",
                "has_alerts": False,
                "alert_counts": {},
                "latest_alert_session_id": None,
                "latest_alert_code": None,
                "latest_alert_at": None,
                "alerts": [],
            }
    else:
        submit_health = {
            "root_dir": str(submit_root),
            "message": "No Hyperliquid submit root found yet.",
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
        }
        submit_alerts = {
            "root_dir": str(submit_root),
            "generated_at": None,
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_state_counts": {},
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "latest_alert_session_id": None,
            "latest_alert_code": None,
            "latest_alert_at": None,
            "alerts": [],
        }

    return {
        "status": "ok",
        "available": True,
        "message": "Hyperliquid now spans venue preflight, signer readiness, local signing, supervised submit, and bounded post-submit supervision.",
        "search_roots": [str(path) for path in search_roots if path.exists()],
        "implemented_surfaces": {
            "preflight": True,
            "account_readiness": True,
            "signed_action_build": True,
            "cryptographic_signing": True,
            "order_submit": True,
            "submit_sessions": True,
            "post_submit_status": True,
            "continuous_supervision": True,
            "submission_health": True,
        },
        "execution_context_pressure": {
            "signer_identity": True,
            "routing_target": True,
            "transport_preference": True,
            "nonce_hint": True,
            "expires_after": True,
        },
        "submit_sessions_available": submit_root.exists(),
        "submit_sessions_root": str(submit_root),
        "submit_health": submit_health,
        "submit_alert_status": submit_alerts.get("alert_status", "ok"),
        "submit_has_alerts": submit_alerts.get("has_alerts", False),
        "submit_alert_counts": submit_alerts.get("alert_counts", {}),
        "submit_alerts": submit_alerts.get("alerts", []),
        "latest_artifacts": latest_artifacts,
        "latest_ready_artifact_type": latest_ready_artifact.get("artifact_type") if latest_ready_artifact else None,
        "latest_ready_generated_at": latest_ready_artifact.get("generated_at") if latest_ready_artifact else None,
        "signature_state": (
            latest_artifacts["signed_action"].get("signature_state")
            if latest_artifacts["signed_action"]
            else "pending_local_artifact"
        ),
    }, 200


def build_stepbit_workspace_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    workspace_root = root.parent
    app_repo = workspace_root / "stepbit-app"
    core_repo = workspace_root / "stepbit-core"

    app_summary = _build_workspace_repo_summary(app_repo, "control_plane")
    core_summary = _build_workspace_repo_summary(core_repo, "runtime_core")
    connected = app_summary["present"] and core_summary["present"]

    return {
        "status": "ok",
        "available": connected,
        "workspace_root": str(workspace_root),
        "connection_mode": "workspace_boundary" if connected else "workspace_incomplete",
        "boundary_note": "Stepbit remains an external connected surface. QuantLab stays sovereign over runtime and execution safety.",
        "repos": {
            "stepbit_app": app_summary,
            "stepbit_core": core_summary,
        },
        "surface_model": {
            "quantlab_role": "execution_and_research_sovereign",
            "stepbit_app_role": "control_plane",
            "stepbit_core_role": "reasoning_runtime",
        },
    }, 200


def _build_workspace_repo_summary(path: Path, role: str) -> dict[str, object]:
    summary: dict[str, object] = {
        "present": path.exists() and path.is_dir(),
        "role": role,
        "path": str(path),
        "branch": None,
        "dirty": None,
        "headline": None,
    }
    if not summary["present"]:
        return summary

    branch, dirty = _read_git_branch_state(path)
    summary["branch"] = branch
    summary["dirty"] = dirty
    summary["headline"] = _read_readme_headline(path)
    return summary


def _read_git_branch_state(repo_path: Path) -> tuple[str | None, bool | None]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), "status", "--short", "--branch"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except Exception:  # noqa: BLE001
        return None, None

    branch = None
    if output:
        first = output[0].strip()
        if first.startswith("## "):
            branch = first[3:].split("...")[0].strip() or None
    dirty = any(line.strip() and not line.startswith("## ") for line in output)
    return branch, dirty


def _read_readme_headline(repo_path: Path) -> str | None:
    for candidate in ("README.md", "README.MD"):
        readme_path = repo_path / candidate
        if not readme_path.exists():
            continue
        try:
            for line in readme_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
        except Exception:  # noqa: BLE001
            return None
    return None


def _find_latest_hyperliquid_artifact(search_roots: list[Path], filename: str) -> dict[str, object] | None:
    candidates: list[Path] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        candidates.extend(search_root.rglob(filename))

    ranked: list[tuple[float, Path, dict[str, object]]] = []
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not _is_hyperliquid_payload(filename, payload):
            continue
        ranked.append((candidate.stat().st_mtime, candidate, payload))

    if not ranked:
        return None

    _, path, payload = max(ranked, key=lambda item: item[0])
    return {
        "path": str(path),
        "artifact_type": payload.get("artifact_type"),
        "generated_at": payload.get("generated_at"),
        "market_supported": payload.get("market_supported"),
        "readiness_allowed": payload.get("readiness_allowed"),
        "signature_state": payload.get("signature_envelope", {}).get("signature_state"),
        "resolved_transport": payload.get("execution_context", {}).get("resolved_transport"),
        "execution_account_role": payload.get("execution_account_role"),
        "submit_state": payload.get("submit_state"),
        "submitted": payload.get("submitted"),
        "response_type": payload.get("response_type"),
        "remote_submit_called": payload.get("remote_submit_called"),
        "order_status_known": payload.get("status_known"),
        "normalized_state": payload.get("normalized_state"),
    }


def _is_hyperliquid_payload(filename: str, payload: dict[str, object]) -> bool:
    adapter_name = payload.get("adapter_name")
    if adapter_name == "hyperliquid":
        return True
    if filename == "hyperliquid_account_readiness.json":
        return "execution_account_role" in payload
    if filename == "hyperliquid_signed_action.json":
        return "signature_envelope" in payload
    if filename == "hyperliquid_submit_response.json":
        return "submit_state" in payload
    if filename == "hyperliquid_order_status.json":
        return "normalized_state" in payload or "status_known" in payload
    if filename == "hyperliquid_supervision.json":
        return "supervision_state" in payload or "polls_completed" in payload
    return False

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
