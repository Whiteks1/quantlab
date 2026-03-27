from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "research_ui" / "server.py"
SPEC = importlib.util.spec_from_file_location("research_ui_server", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
research_ui_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research_ui_server)


def _write_session(root: Path, session_id: str, status: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "artifacts").mkdir()
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": session_id,
                "mode": "paper",
                "command": "paper",
                "status": status,
                "created_at": "2026-03-25T18:00:00",
                "request_id": f"req_{session_id}",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "mode": "paper",
                "command": "paper",
                "status": status,
                "request_id": f"req_{session_id}",
                "updated_at": "2026-03-25T18:05:00",
                "error_type": "DataError" if status == "failed" else None,
                "message": "boom" if status == "failed" else None,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "report.json").write_text(
        json.dumps(
            {
                "status": status,
                "header": {"run_id": session_id, "mode": "paper"},
                "machine_contract": {"contract_type": "quantlab.paper.result"},
            }
        ),
        encoding="utf-8",
    )


def _write_broker_validation_session(root: Path, session_id: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "adapter_name": "kraken",
                "status": "submitted",
                "created_at": "2026-03-26T10:00:00",
                "request_id": f"req_{session_id}",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "submitted",
                "updated_at": "2026-03-26T10:05:00",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_order_validate.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.broker.order_validate",
                "adapter_name": "kraken",
                "remote_validation_called": True,
                "validation_accepted": True,
                "validation_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "approval.json").write_text(
        json.dumps(
            {
                "status": "approved",
                "reviewed_by": "marce",
                "reviewed_at": "2026-03-26T10:06:00",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_submit_gate.json").write_text(
        json.dumps(
            {
                "submit_state": "ready_for_supervised_submit_gate",
                "confirmed_by": "marce",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_submit_response.json").write_text(
        json.dumps(
            {
                "submit_state": "submitted",
                "generated_at": "2026-03-26T10:07:00",
                "submitted": True,
                "remote_submit_called": True,
                "txid": ["ABC123"],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_order_status.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-26T10:08:00",
                "status_known": True,
                "normalized_state": "open",
                "matched_txid": ["ABC123"],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )


def _write_hyperliquid_submit_session(root: Path, session_id: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "submitted",
                "created_at": "2026-03-27T12:00:00",
                "request_id": f"req_{session_id}",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "open",
                "updated_at": "2026-03-27T12:06:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "order_status_known": True,
                "order_status_state": "open",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:01:00",
                "readiness_allowed": True,
                "execution_context": {"resolved_transport": "websocket"},
                "signature_envelope": {"signature_state": "signed"},
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_submit_response.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.submit_response",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:05:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "response_type": "resting",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_order_status.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.order_status",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:06:00",
                "status_known": True,
                "normalized_state": "open",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )


def test_build_paper_health_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0


def test_build_paper_health_payload_summarizes_existing_sessions(tmp_path: Path):
    paper_root = tmp_path / "outputs" / "paper_sessions"
    _write_session(paper_root, "paper_001", "success")
    _write_session(paper_root, "paper_002", "failed")

    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 2
    assert payload["status_counts"]["success"] == 1
    assert payload["status_counts"]["failed"] == 1


def test_build_broker_health_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_broker_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0
    assert payload["has_alerts"] is False


def test_build_broker_health_payload_summarizes_existing_sessions(tmp_path: Path):
    broker_root = tmp_path / "outputs" / "broker_order_validations"
    _write_broker_validation_session(broker_root, "broker_001")

    payload, status = research_ui_server.build_broker_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 1
    assert payload["submitted_sessions"] == 1
    assert payload["order_status_known_sessions"] == 1
    assert payload["latest_submit_session_id"] == "broker_001"


def test_build_hyperliquid_surface_payload_detects_latest_artifacts(tmp_path: Path):
    outputs_root = tmp_path / "outputs" / "hyperliquid"
    outputs_root.mkdir(parents=True)
    (outputs_root / "hyperliquid_account_readiness.json").write_text(
        json.dumps(
            {
                "adapter_name": "hyperliquid",
                "artifact_type": "quantlab.hyperliquid.account_readiness",
                "generated_at": "2026-03-26T12:00:00",
                "readiness_allowed": True,
                "execution_account_role": "user",
            }
        ),
        encoding="utf-8",
    )
    (outputs_root / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "adapter_name": "hyperliquid",
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "generated_at": "2026-03-26T12:05:00",
                "readiness_allowed": True,
                "execution_context": {"resolved_transport": "websocket"},
                "signature_envelope": {"signature_state": "pending_signer_backend"},
            }
        ),
        encoding="utf-8",
    )
    _write_hyperliquid_submit_session(tmp_path / "outputs" / "hyperliquid_submits", "hyper_001")

    payload, status = research_ui_server.build_hyperliquid_surface_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["implemented_surfaces"]["signed_action_build"] is True
    assert payload["implemented_surfaces"]["order_submit"] is True
    assert payload["submit_health"]["total_sessions"] == 1
    assert payload["submit_has_alerts"] is False
    assert payload["latest_artifacts"]["order_status"]["normalized_state"] == "open"
    assert payload["latest_ready_artifact_type"] == "quantlab.hyperliquid.order_status"
    assert payload["signature_state"] in {"pending_signer_backend", "signed"}


def test_build_stepbit_workspace_payload_detects_local_repos(tmp_path: Path):
    project_root = tmp_path / "quant_lab"
    project_root.mkdir()
    stepbit_app = tmp_path / "stepbit-app"
    stepbit_core = tmp_path / "stepbit-core"
    stepbit_app.mkdir()
    stepbit_core.mkdir()
    (stepbit_app / "README.md").write_text("# stepbit-app\n", encoding="utf-8")
    (stepbit_core / "README.md").write_text("# stepbit-core\n", encoding="utf-8")

    payload, status = research_ui_server.build_stepbit_workspace_payload(project_root)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["repos"]["stepbit_app"]["present"] is True
    assert payload["repos"]["stepbit_core"]["present"] is True
