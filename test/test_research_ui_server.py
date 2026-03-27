from __future__ import annotations

import importlib.util
import json
import os
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
    (session_dir / "hyperliquid_supervision.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.supervision",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:07:00",
                "supervision_state": "active",
                "attention_required": False,
                "polls_completed": 3,
                "monitoring_mode": "websocket_aware_rest_polling",
                "resolved_transport": "websocket",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )


def _write_validation_artifact(target: Path, *, accepted: bool, handoff_id: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.pretrade.handoff_validation",
                "generated_at": "2026-03-27T12:43:38",
                "source_artifact_path": "C:\\Users\\marce\\Documents\\meta_trade\\tests\\fixtures\\expected_quantlab_handoff.json",
                "accepted": accepted,
                "reasons": [] if accepted else ["pretrade_context_side_invalid"],
                "handoff_contract": {
                    "contract_type": "calculadora_riesgo.quantlab_handoff",
                    "contract_version": "1.0",
                    "handoff_id": handoff_id,
                    "generated_at": "2026-03-27T12:00:00.000Z",
                },
                "source": {
                    "planner": "contract-fixture",
                    "trade_plan_contract_type": "calculadora_riesgo.trade_plan",
                    "trade_plan_contract_version": "1.0",
                    "trade_plan_id": handoff_id,
                },
                "pretrade_context": {
                    "symbol": "ETH-USD",
                    "venue": "hyperliquid",
                    "side": "buy",
                    "accountId": "acct_demo_001",
                    "strategyId": "breakout_v1",
                },
                "quantlab_hints": {
                    "ready_for_draft_execution_intent": accepted,
                    "missing_fields": [],
                    "boundary_note": "This handoff artifact is for bounded QuantLab ingestion only.",
                },
                "trade_plan": {
                    "contract_type": "calculadora_riesgo.trade_plan",
                    "contract_version": "1.0",
                    "plan_id": handoff_id,
                },
                "quantlab_boundary": {
                    "ready_for_draft_execution_intent": accepted,
                    "policy_owner": "quantlab",
                    "execution_authority": "quantlab",
                    "submit_authority": "quantlab",
                },
            },
            indent=2,
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


def test_build_paper_alerts_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_paper_alerts_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0
    assert payload["has_alerts"] is False
    assert payload["alerts"] == []


def test_build_paper_alerts_payload_summarizes_existing_alerts(tmp_path: Path):
    paper_root = tmp_path / "outputs" / "paper_sessions"
    _write_session(paper_root, "paper_001", "success")
    _write_session(paper_root, "paper_002", "failed")

    payload, status = research_ui_server.build_paper_alerts_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 2
    assert payload["has_alerts"] is True
    assert payload["alert_status"] == "critical"
    assert payload["latest_success_session_id"] == "paper_001"
    assert payload["latest_alert_session_id"] == "paper_002"
    assert payload["latest_alert_code"] == "PAPER_SESSION_FAILED"
    assert payload["alert_counts"]["critical"] == 1


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
    assert payload["implemented_surfaces"]["continuous_supervision"] is True
    assert payload["submit_health"]["total_sessions"] == 1
    assert payload["submit_has_alerts"] is False
    assert payload["latest_artifacts"]["order_status"]["normalized_state"] == "open"
    assert payload["latest_ready_artifact_type"] == "quantlab.hyperliquid.supervision"
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
    (stepbit_app / "web" / "src" / "pages").mkdir(parents=True)
    (stepbit_app / "web" / "src" / "pages" / "Dashboard.tsx").write_text("export default null\n", encoding="utf-8")
    (stepbit_app / "web" / "src" / "pages" / "Pipelines.tsx").write_text("export default null\n", encoding="utf-8")
    (stepbit_core / "src" / "orchestrator").mkdir(parents=True)
    (stepbit_core / "src" / "pipelines").mkdir(parents=True)
    (stepbit_core / "src" / "api").mkdir(parents=True)

    payload, status = research_ui_server.build_stepbit_workspace_payload(project_root)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["repos"]["stepbit_app"]["present"] is True
    assert payload["repos"]["stepbit_core"]["present"] is True
    assert payload["workspace_summary"]["app_surfaces_present"] >= 2
    assert payload["workspace_summary"]["core_capabilities_present"] >= 2
    assert payload["workspace_summary"]["compatibility_surfaces_total"] >= 1
    assert "start_support" in payload
    assert "core_reachable" in payload["live_urls"]
    assert any(group["label"] == "Automation" for group in payload["app_surface_groups"])
    assert any(group["label"] == "Runtime" for group in payload["core_capability_groups"])


def test_build_meta_trade_workspace_payload_detects_external_repo(tmp_path: Path):
    project_root = tmp_path / "quant_lab"
    project_root.mkdir()
    meta_trade = tmp_path / "meta_trade"
    meta_trade.mkdir()
    (meta_trade / "README.md").write_text("# Trading Risk Calculator\n", encoding="utf-8")
    (meta_trade / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (meta_trade / "risk-core.js").write_text("module.exports = {};\n", encoding="utf-8")
    (meta_trade / "package.json").write_text(
        json.dumps({"scripts": {"dev": "node scripts/serve-static.js", "test": "node tests/run_js_tests.js"}}),
        encoding="utf-8",
    )
    (meta_trade / "web").mkdir()
    (meta_trade / "web" / "risk-ui.js").write_text("export {};\n", encoding="utf-8")
    (meta_trade / "cli").mkdir()
    (meta_trade / "cli" / "trade-plan.js").write_text("#!/usr/bin/env node\n", encoding="utf-8")
    (meta_trade / "tests" / "fixtures").mkdir(parents=True)
    (meta_trade / "tests" / "run_js_tests.js").write_text("console.log('ok')\n", encoding="utf-8")
    (meta_trade / "tests" / "fixtures" / "expected_quantlab_handoff.json").write_text("{}", encoding="utf-8")
    (meta_trade / "docs").mkdir()
    (meta_trade / "docs" / "quantlab-handoff-contract.md").write_text("# contract\n", encoding="utf-8")

    payload, status = research_ui_server.build_meta_trade_workspace_payload(project_root)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["repo"]["present"] is True
    assert payload["workspace_summary"]["product_surfaces_present"] >= 2
    assert payload["workspace_summary"]["engine_modules_present"] >= 2
    assert payload["workspace_summary"]["package_script_total"] == 2
    assert any(group["label"] == "Workspace" for group in payload["product_surface_groups"])
    assert any(group["label"] == "Core" for group in payload["engine_module_groups"])


def test_build_pretrade_handoff_payload_returns_empty_when_root_is_missing(tmp_path: Path):
    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is False
    assert payload["has_validation"] is False
    assert payload["validation_state"] == "empty"


def test_build_pretrade_handoff_payload_returns_empty_when_root_has_no_artifacts(tmp_path: Path):
    (tmp_path / "outputs" / "pretrade_handoff").mkdir(parents=True)

    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is True
    assert payload["has_validation"] is False
    assert payload["validation_state"] == "empty"


def test_build_pretrade_handoff_payload_selects_latest_validation_artifact(tmp_path: Path):
    older = tmp_path / "outputs" / "pretrade_handoff" / "older" / "pretrade_handoff_validation.json"
    newer = tmp_path / "outputs" / "pretrade_handoff" / "newer" / "pretrade_handoff_validation.json"

    _write_validation_artifact(older, accepted=False, handoff_id="handoff-older")
    _write_validation_artifact(newer, accepted=True, handoff_id="handoff-newer")

    os.utime(older, (older.stat().st_atime, older.stat().st_mtime - 30))
    os.utime(newer, None)

    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is True
    assert payload["has_validation"] is True
    assert payload["accepted"] is True
    assert payload["validation_state"] == "accepted"
    assert payload["handoff_id"] == "handoff-newer"
    assert payload["latest_validation_path"] == str(newer)
    assert payload["latest_validation_href"] == "/outputs/pretrade_handoff/newer/pretrade_handoff_validation.json"


def test_normalize_launch_request_accepts_run_payload():
    payload = research_ui_server._normalize_launch_request(
        {
            "command": "run",
            "params": {
                "ticker": "ETH-USD",
                "start": "2024-01-01",
                "end": "2024-12-31",
                "interval": "1d",
                "paper": True,
                "initial_cash": 2500,
            },
        }
    )

    assert payload["schema_version"] == "1.0"
    assert payload["command"] == "run"
    assert payload["params"]["ticker"] == "ETH-USD"
    assert payload["params"]["paper"] is True
    assert payload["params"]["initial_cash"] == 2500.0


def test_normalize_launch_request_rejects_invalid_sweep_payload():
    try:
        research_ui_server._normalize_launch_request(
            {
                "command": "sweep",
                "params": {},
            }
        )
    except ValueError as exc:
        assert "config_path" in str(exc)
    else:
        raise AssertionError("Expected invalid sweep payload to raise ValueError")


def test_build_launch_control_payload_reports_supported_commands(tmp_path: Path):
    payload, status = research_ui_server.build_launch_control_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["supported_commands"] == ["run", "sweep"]
    assert payload["jobs"] == []


def test_launch_quantlab_job_registers_running_job(tmp_path: Path, monkeypatch):
    class _FakeProcess:
        pid = 4321

        @staticmethod
        def poll():
            return None

    def _fake_popen(command, cwd, stdout, stderr, text):  # noqa: ANN001
        assert command[1] == "main.py"
        assert "--json-request" in command
        assert cwd == tmp_path
        return _FakeProcess()

    monkeypatch.setattr(research_ui_server, "_resolve_quantlab_python", lambda root: root / ".venv" / "Scripts" / "python.exe")
    monkeypatch.setattr(research_ui_server.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(research_ui_server, "LAUNCH_JOBS", [])

    response, status = research_ui_server.launch_quantlab_job(
        tmp_path,
        {
            "command": "run",
            "params": {
                "ticker": "BTC-USD",
                "start": "2024-01-01",
                "end": "2024-06-30",
            },
        },
    )

    assert status == 202
    assert response["status"] == "accepted"
    assert response["job"]["status"] == "running"
    assert response["job"]["command"] == "run"
    assert response["job"]["stdout_href"].startswith("/outputs/research_ui/launches/")


def test_start_stepbit_workspace_starts_missing_services(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "quant_lab"
    project_root.mkdir()
    stepbit_app = tmp_path / "stepbit-app"
    (stepbit_app / "web").mkdir(parents=True)

    monkeypatch.setattr(
        research_ui_server,
        "_detect_stepbit_live_urls",
        lambda: {
            "preferred_url": "http://127.0.0.1:5173/",
            "frontend_url": "http://127.0.0.1:5173/",
            "backend_url": "http://127.0.0.1:8080/",
            "frontend_reachable": False,
            "backend_reachable": False,
            "reachable": False,
        },
    )
    monkeypatch.setattr(
        research_ui_server,
        "_build_stepbit_start_support",
        lambda repo, live: {
            "can_start_backend": True,
            "can_start_frontend": True,
            "frontend_install_required": True,
            "frontend_command": "corepack pnpm",
            "backend_command": "go run ./cmd/stepbit-app",
            "frontend_running": False,
            "backend_running": False,
        },
    )
    monkeypatch.setattr(research_ui_server, "_wait_for_stepbit_backend", lambda timeout_seconds=12: True)
    monkeypatch.setattr(research_ui_server, "_stepbit_backend_binary_path", lambda root: root / "outputs" / "research_ui" / "stepbit" / "stepbit-app-runtime.exe")

    calls = []

    class _Completed:
        returncode = 0

    def _fake_spawn(command, cwd, stdout_path, stderr_path, env_overrides=None):  # noqa: ANN001
        calls.append((command, cwd, stdout_path, stderr_path, env_overrides))
        return 888

    def _fake_run(command, cwd, stdout_path, stderr_path, timeout_seconds=600):  # noqa: ANN001
        if "backend.build" in stdout_path.name:
            binary_path = project_root / "outputs" / "research_ui" / "stepbit" / "stepbit-app-runtime.exe"
            binary_path.parent.mkdir(parents=True, exist_ok=True)
            binary_path.write_text("binary", encoding="utf-8")
        calls.append((command, cwd, stdout_path, stderr_path, timeout_seconds))
        return _Completed()

    monkeypatch.setattr(research_ui_server, "_spawn_detached_process", _fake_spawn)
    monkeypatch.setattr(research_ui_server, "_run_hidden_command", _fake_run)

    payload, status = research_ui_server.start_stepbit_workspace(project_root, {})

    assert status == 202
    assert payload["status"] == "accepted"
    assert len(calls) == 4
    assert any("go" in str(call[0]) for call in calls)
    assert any(isinstance(call[0], list) and "install" in " ".join(call[0]) for call in calls)
    assert any(isinstance(call[0], list) and "build" in " ".join(call[0]) for call in calls)
    assert any(isinstance(call[4], dict) and call[4].get("VITE_API_BASE_URL") == "http://127.0.0.1:8080/api" for call in calls)


def test_start_stepbit_workspace_releases_lock_before_long_running_steps(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "quant_lab"
    project_root.mkdir()
    stepbit_app = tmp_path / "stepbit-app"
    (stepbit_app / "web").mkdir(parents=True)

    monkeypatch.setattr(
        research_ui_server,
        "_detect_stepbit_live_urls",
        lambda: {
            "preferred_url": "http://127.0.0.1:5173/",
            "frontend_url": "http://127.0.0.1:5173/",
            "backend_url": "http://127.0.0.1:8080/",
            "frontend_reachable": False,
            "backend_reachable": False,
            "reachable": False,
        },
    )
    monkeypatch.setattr(
        research_ui_server,
        "_build_stepbit_start_support",
        lambda repo, live: {
            "can_start_backend": True,
            "can_start_frontend": True,
            "frontend_install_required": False,
            "frontend_command": "pnpm",
            "backend_command": "go build ./cmd/stepbit-app + run built binary",
            "frontend_running": False,
            "backend_running": False,
        },
    )
    monkeypatch.setattr(research_ui_server, "_wait_for_stepbit_backend", lambda timeout_seconds=12: True)
    monkeypatch.setattr(
        research_ui_server,
        "_stepbit_backend_binary_path",
        lambda root: root / "outputs" / "research_ui" / "stepbit" / "stepbit-app-runtime.exe",
    )

    class _Completed:
        returncode = 0

    def _fake_run(command, cwd, stdout_path, stderr_path, timeout_seconds=600):  # noqa: ANN001
        acquired = research_ui_server.STEPBIT_START_LOCK.acquire(blocking=False)
        assert acquired, "_run_hidden_command should not execute while STEPBIT_START_LOCK is held"
        research_ui_server.STEPBIT_START_LOCK.release()
        if "backend.build" in stdout_path.name:
            binary_path = project_root / "outputs" / "research_ui" / "stepbit" / "stepbit-app-runtime.exe"
            binary_path.parent.mkdir(parents=True, exist_ok=True)
            binary_path.write_text("binary", encoding="utf-8")
        return _Completed()

    monkeypatch.setattr(research_ui_server, "_run_hidden_command", _fake_run)
    monkeypatch.setattr(research_ui_server, "_spawn_detached_process", lambda *args, **kwargs: 777)

    payload, status = research_ui_server.start_stepbit_workspace(project_root, {})

    assert status == 202
    assert payload["status"] == "accepted"
