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
from quantlab.cli.paper_sessions import build_paper_sessions_health


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/paper-sessions-health'):
            payload, status = build_paper_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if self.path.startswith('/api/broker-submissions-health'):
            payload, status = build_broker_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if self.path.startswith('/api/pretrade-plans'):
            payload, status = build_pretrade_payload(PROJECT_ROOT)
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


def build_pretrade_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    pretrade_root = root / "outputs" / "pretrade_sessions"

    if not pretrade_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(pretrade_root),
            "message": "No pre-trade session root found yet.",
            "total_sessions": 0,
            "execution_allowed_sessions": 0,
            "execution_rejected_sessions": 0,
            "latest_session_id": None,
            "latest_generated_at": None,
            "sessions": [],
        }, 200

    try:
        sessions = []
        for child in sorted(pretrade_root.iterdir()):
            if not child.is_dir():
                continue
            summary_path = child / "summary.json"
            plan_path = child / "plan.json"
            if not summary_path.exists() and not plan_path.exists():
                continue
            sessions.append(_load_pretrade_summary(child, root))

        sessions.sort(
            key=lambda item: item.get("generated_at") or "",
            reverse=True,
        )
        allowed_count = sum(1 for item in sessions if item.get("execution_allowed") is True)
        rejected_count = sum(1 for item in sessions if item.get("execution_allowed") is False)
        latest = sessions[0] if sessions else None

        return {
            "status": "ok",
            "available": True,
            "root_dir": str(pretrade_root),
            "message": "Pre-trade planning artifacts are available for bounded UI inspection.",
            "total_sessions": len(sessions),
            "execution_allowed_sessions": allowed_count,
            "execution_rejected_sessions": rejected_count,
            "latest_session_id": latest.get("session_id") if latest else None,
            "latest_generated_at": latest.get("generated_at") if latest else None,
            "sessions": sessions,
        }, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(pretrade_root),
            "message": str(exc),
            "sessions": [],
        }, 500


def build_hyperliquid_surface_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
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
                latest_artifacts["signed_action"],
                latest_artifacts["account_readiness"],
                latest_artifacts["preflight"],
            )
            if artifact
        ),
        None,
    )

    return {
        "status": "ok",
        "available": True,
        "message": "Hyperliquid runtime remains read-only and pre-submit only.",
        "search_roots": [str(path) for path in search_roots if path.exists()],
        "implemented_surfaces": {
            "preflight": True,
            "account_readiness": True,
            "signed_action_build": True,
            "cryptographic_signing": False,
            "order_submit": False,
        },
        "execution_context_pressure": {
            "signer_identity": True,
            "routing_target": True,
            "transport_preference": True,
            "nonce_hint": True,
            "expires_after": True,
        },
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


def _load_pretrade_summary(session_dir: Path, project_root: Path) -> dict[str, object]:
    summary = _read_json_if_exists(session_dir / "summary.json") or {}
    plan = _read_json_if_exists(session_dir / "plan.json") or {}
    bridge = _read_json_if_exists(session_dir / "execution_bridge.json") or {}

    request = plan.get("request", {}) if isinstance(plan.get("request"), dict) else {}
    plan_data = plan.get("plan", {}) if isinstance(plan.get("plan"), dict) else {}
    preflight = (
        bridge.get("execution_preflight", {})
        if isinstance(bridge.get("execution_preflight"), dict)
        else {}
    )

    return {
        "session_id": summary.get("session_id") or plan.get("session_id") or session_dir.name,
        "generated_at": summary.get("generated_at") or plan.get("generated_at"),
        "symbol": summary.get("symbol") or request.get("symbol"),
        "venue": summary.get("venue") or request.get("venue"),
        "side": summary.get("side") or request.get("side"),
        "accepted": summary.get("accepted"),
        "risk_amount": summary.get("risk_amount") or plan_data.get("risk_amount"),
        "position_size": summary.get("position_size") or plan_data.get("position_size"),
        "notional": summary.get("notional") or plan_data.get("notional"),
        "max_loss_at_stop": summary.get("max_loss_at_stop") or plan_data.get("max_loss_at_stop"),
        "net_profit_at_target": summary.get("net_profit_at_target") or plan_data.get("net_profit_at_target"),
        "risk_reward_ratio": summary.get("risk_reward_ratio") or plan_data.get("risk_reward_ratio"),
        "execution_bridge_present": bool(bridge),
        "execution_allowed": preflight.get("allowed") if bridge else None,
        "execution_reasons": preflight.get("reasons", []) if bridge else [],
        "session_dir": str(session_dir.relative_to(project_root)).replace("\\", "/"),
        "plan_path": str((session_dir / "plan.json").relative_to(project_root)).replace("\\", "/"),
        "summary_path": str((session_dir / "summary.json").relative_to(project_root)).replace("\\", "/"),
        "plan_markdown_path": str((session_dir / "plan.md").relative_to(project_root)).replace("\\", "/"),
        "execution_bridge_path": (
            str((session_dir / "execution_bridge.json").relative_to(project_root)).replace("\\", "/")
            if bridge
            else None
        ),
    }


def _read_json_if_exists(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
    }


def _is_hyperliquid_payload(filename: str, payload: dict[str, object]) -> bool:
    adapter_name = payload.get("adapter_name")
    if adapter_name == "hyperliquid":
        return True
    if filename == "hyperliquid_account_readiness.json":
        return "execution_account_role" in payload
    if filename == "hyperliquid_signed_action.json":
        return "signature_envelope" in payload
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
