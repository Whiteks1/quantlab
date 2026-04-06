from __future__ import annotations

import json
import types

import pytest

from quantlab.cli.hyperliquid_submit_sessions import (
    handle_hyperliquid_submit_sessions_commands,
    load_hyperliquid_submit_summary,
)
from quantlab.errors import ConfigError


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "hyperliquid_submit_sessions_list": None,
        "hyperliquid_submit_sessions_show": None,
        "hyperliquid_submit_sessions_index": None,
        "hyperliquid_submit_sessions_supervise": None,
        "hyperliquid_submit_sessions_status": None,
        "hyperliquid_submit_sessions_reconcile": None,
        "hyperliquid_submit_sessions_fills": None,
        "hyperliquid_submit_sessions_cancel": None,
        "hyperliquid_submit_sessions_health": None,
        "hyperliquid_submit_sessions_alerts": None,
        "hyperliquid_supervision_polls": 3,
        "hyperliquid_supervision_interval_seconds": 2.0,
        "hyperliquid_cancel_reviewer": None,
        "hyperliquid_cancel_note": None,
        "hyperliquid_cancel_confirm": False,
        "hyperliquid_private_key": None,
        "hyperliquid_private_key_env": "HYPERLIQUID_PRIVATE_KEY",
        "hyperliquid_preflight_timeout": 10.0,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_session(tmp_path, name="20260327_hyperliquid_submit_demo"):
    session_dir = tmp_path / name
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": name,
                "status": "submitted",
                "created_at": "2026-03-27T12:00:00",
                "request_id": "req_demo",
                "source_artifact_path": "C:/tmp/hyperliquid_signed_action.json",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": name,
                "status": "submitted",
                "updated_at": "2026-03-27T12:01:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "account_readiness": {
                    "execution_context": {
                        "execution_account_id": "0x1111111111111111111111111111111111111111",
                    }
                },
                "action_payload": {"orders": [{"c": "abc123cloid"}]},
                "signature_envelope": {
                    "signer_id": "0x1111111111111111111111111111111111111111",
                    "signature_state": "signed",
                },
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_submit_response.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.submit_response",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "response_type": "resting",
                "oid": 12345,
                "cloid": "abc123cloid",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    return session_dir


def test_load_hyperliquid_submit_summary(tmp_path):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_reconciliation.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.reconciliation",
                "generated_at": "2026-03-27T12:06:00",
                "status_known": True,
                "normalized_state": "open",
                "close_state": "open",
                "fill_state": "partial",
                "fill_count": 1,
                "filled_size": "0.15",
                "remaining_size": "0.10",
                "average_fill_price": "2451",
                "last_fill_time": 1764000000100,
                "resolution_source": "open_orders",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    summary = load_hyperliquid_submit_summary(session_dir)

    assert summary["session_id"] == "20260327_hyperliquid_submit_demo"
    assert summary["status"] == "submitted"
    assert summary["submit_state"] == "submitted_remote"
    assert summary["submitted"] is True
    assert summary["signed_action_present"] is True
    assert summary["submit_response_present"] is True
    assert summary["alerts_present"] is False
    assert summary["alert_status"] == "ok"
    assert summary["latest_alert_code"] is None
    assert summary["reconciliation_fill_state"] == "partial"
    assert summary["reconciliation_filled_size"] == "0.15"


def test_list_hyperliquid_submit_sessions(tmp_path, capsys):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_list=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit sessions in" in output
    assert "alert_status" in output
    assert "warning" in output
    assert "submitted_remote" in output


def test_show_hyperliquid_submit_session(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_show=str(session_dir))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit session" in output
    assert "alert_status            : warning" in output
    assert "latest_alert_code       : HYPERLIQUID_ORDER_STATUS_MISSING" in output
    assert "submitted_remote" in output


def test_refresh_hyperliquid_submit_index(tmp_path):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_index=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    json_path = tmp_path / "hyperliquid_submits_index.json"
    csv_path = tmp_path / "hyperliquid_submits_index.csv"
    assert json_path.exists()
    assert csv_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["sessions"][0]["alert_status"] == "warning"
    assert payload["sessions"][0]["latest_alert_code"] == "HYPERLIQUID_ORDER_STATUS_MISSING"


def test_hyperliquid_submit_health_summary(tmp_path, capsys):
    _write_session(tmp_path)

    args = _make_args(hyperliquid_submit_sessions_health=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    output = capsys.readouterr().out
    assert "Hyperliquid submission health" in output
    assert "total_sessions" in output
    assert "reconciliation_sessions" in output
    assert "alert_status            : warning" in output
    assert "latest_alert_code       : HYPERLIQUID_ORDER_STATUS_MISSING" in output
    assert "latest_submit_id" in output


def test_hyperliquid_submit_alerts_snapshot(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_order_status.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.order_status",
                "generated_at": "2026-03-27T12:05:00",
                "status_known": False,
                "normalized_state": "unknown",
                "errors": ["missing_order"],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(hyperliquid_submit_sessions_alerts=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    payload = json.loads(capsys.readouterr().out)
    assert payload["alert_status"] == "critical"
    assert payload["has_alerts"] is True
    assert payload["alerts"][0]["alert_code"] == "HYPERLIQUID_ORDER_STATUS_UNKNOWN"


def test_refresh_hyperliquid_submit_status(monkeypatch, tmp_path):
    from quantlab.cli import hyperliquid_submit_sessions as module

    session_dir = _write_session(tmp_path)

    def fake_status(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.order_status",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:05:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "query_mode": "oid",
                    "query_identifier": "12345",
                    "query_attempted": True,
                    "status_known": True,
                    "normalized_state": "open",
                    "raw_status": "open",
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "order_status": {"status": "order", "order": {"status": "open"}},
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_order_status_report", fake_status)

    args = _make_args(hyperliquid_submit_sessions_status=str(session_dir))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    status_artifact = session_dir / "hyperliquid_order_status.json"
    assert status_artifact.exists()
    status_payload = json.loads(status_artifact.read_text(encoding="utf-8"))
    assert status_payload["normalized_state"] == "open"

    session_status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert session_status["status"] == "open"
    assert session_status["order_status_known"] is True
    assert session_status["order_status_state"] == "open"


def test_refresh_hyperliquid_submit_reconciliation(monkeypatch, tmp_path):
    from quantlab.cli import hyperliquid_submit_sessions as module

    session_dir = _write_session(tmp_path)

    def fake_reconciliation(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.reconciliation",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:06:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "status_known": True,
                    "normalized_state": "open",
                    "close_state": "open",
                    "fill_state": "partial",
                    "fill_count": 1,
                    "filled_size": "0.15",
                    "remaining_size": "0.10",
                    "average_fill_price": "2451",
                    "last_fill_time": 1764000000100,
                    "resolution_source": "open_orders",
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "order_status_report": {
                        "status_known": False,
                        "normalized_state": "unknown",
                    },
                    "matched_open_order": {"oid": 12345},
                    "matched_frontend_open_order": None,
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_reconciliation_report", fake_reconciliation)

    args = _make_args(hyperliquid_submit_sessions_reconcile=str(session_dir))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    reconciliation_artifact = session_dir / "hyperliquid_reconciliation.json"
    assert reconciliation_artifact.exists()
    reconciliation_payload = json.loads(reconciliation_artifact.read_text(encoding="utf-8"))
    assert reconciliation_payload["resolution_source"] == "open_orders"

    session_status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert session_status["status"] == "open"
    assert session_status["reconciliation_known"] is True
    assert session_status["reconciliation_state"] == "open"
    assert session_status["reconciliation_source"] == "open_orders"
    assert session_status["reconciliation_fill_state"] == "partial"
    assert session_status["reconciliation_filled_size"] == "0.15"


def test_refresh_hyperliquid_submit_cancel(monkeypatch, tmp_path):
    from quantlab.cli import hyperliquid_submit_sessions as module

    session_dir = _write_session(tmp_path)

    def fake_cancel(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.cancel_response",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:07:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "source_action_hash": "0xabc",
                    "source_signer_id": "0x1111111111111111111111111111111111111111",
                    "source_signing_payload_sha256": "abc123",
                    "source_submit_state": "submitted_remote",
                    "cancel_payload": {"action": {"type": "cancel"}},
                    "cancel_state": "canceled_remote",
                    "remote_cancel_called": True,
                    "cancel_accepted": True,
                    "response_type": "ok",
                    "asset": 1,
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "exchange_response": {"status": "ok"},
                    "reviewer": "marce",
                    "note": "stop it",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_cancel_report", fake_cancel)

    args = _make_args(
        hyperliquid_submit_sessions_cancel=str(session_dir),
        hyperliquid_cancel_reviewer="marce",
        hyperliquid_cancel_note="stop it",
        hyperliquid_cancel_confirm=True,
    )
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    cancel_artifact = session_dir / "hyperliquid_cancel_response.json"
    assert cancel_artifact.exists()
    cancel_payload = json.loads(cancel_artifact.read_text(encoding="utf-8"))
    assert cancel_payload["cancel_state"] == "canceled_remote"
    assert cancel_payload["cancel_accepted"] is True

    session_status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert session_status["status"] == "cancel_pending"
    assert session_status["cancel_state"] == "canceled_remote"
    assert session_status["cancel_accepted"] is True


def test_refresh_hyperliquid_submit_fill_summary(monkeypatch, tmp_path):
    from quantlab.cli import hyperliquid_submit_sessions as module

    session_dir = _write_session(tmp_path)

    def fake_fill_summary(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.fill_summary",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:08:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "fills_known": True,
                    "query_attempted": True,
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "fill_state": "partial",
                    "original_size": "0.25",
                    "filled_size": "0.15",
                    "remaining_size": "0.1",
                    "fill_count": 1,
                    "average_fill_price": "2451",
                    "total_fee": "0.2",
                    "total_builder_fee": "0.05",
                    "total_closed_pnl": None,
                    "first_fill_time": 1764000000000,
                    "last_fill_time": 1764000000000,
                    "matched_fill_sample": [{"oid": 12345}],
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_fill_summary_report", fake_fill_summary)

    args = _make_args(hyperliquid_submit_sessions_fills=str(session_dir))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    fill_artifact = session_dir / "hyperliquid_fill_summary.json"
    assert fill_artifact.exists()
    fill_payload = json.loads(fill_artifact.read_text(encoding="utf-8"))
    assert fill_payload["fill_state"] == "partial"
    assert fill_payload["filled_size"] == "0.15"

    session_status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert session_status["fill_summary_known"] is True
    assert session_status["fill_summary_state"] == "partial"
    assert session_status["fill_summary_filled_size"] == "0.15"


def test_refresh_hyperliquid_submit_supervision(monkeypatch, tmp_path):
    from quantlab.cli import hyperliquid_submit_sessions as module

    session_dir = _write_session(tmp_path)

    def fake_status(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.order_status",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:05:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "query_attempted": True,
                    "status_known": True,
                    "normalized_state": "open",
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "errors": [],
                }

        return _Fake()

    def fake_reconcile(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.reconciliation",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:06:00",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "status_known": True,
                    "normalized_state": "open",
                    "close_state": "open",
                    "fill_state": "partial",
                    "fill_count": 1,
                    "filled_size": "0.10",
                    "remaining_size": "0.15",
                    "average_fill_price": "2450.1",
                    "resolution_source": "open_orders",
                    "errors": [],
                }

        return _Fake()

    def fake_fill_summary(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.fill_summary",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:06:01",
                    "source_session_id": "20260327_hyperliquid_submit_demo",
                    "execution_account_id": "0x1111111111111111111111111111111111111111",
                    "fills_known": True,
                    "query_attempted": True,
                    "oid": 12345,
                    "cloid": "abc123cloid",
                    "fill_state": "partial",
                    "original_size": "0.25",
                    "filled_size": "0.10",
                    "remaining_size": "0.15",
                    "fill_count": 1,
                    "average_fill_price": "2450.1",
                    "total_fee": "0.15",
                    "total_builder_fee": "0.00",
                    "total_closed_pnl": "0.00",
                    "first_fill_time": 1764000000100,
                    "last_fill_time": 1764000000100,
                    "matched_fill_sample": [],
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_order_status_report", fake_status)
    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_reconciliation_report", fake_reconcile)
    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_fill_summary_report", fake_fill_summary)
    monkeypatch.setattr(module.time, "sleep", lambda *_args, **_kwargs: None)

    args = _make_args(
        hyperliquid_submit_sessions_supervise=str(session_dir),
        hyperliquid_supervision_polls=2,
        hyperliquid_supervision_interval_seconds=0.0,
    )
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    supervision_artifact = session_dir / "hyperliquid_supervision.json"
    assert supervision_artifact.exists()
    supervision_payload = json.loads(supervision_artifact.read_text(encoding="utf-8"))
    assert supervision_payload["supervision_state"] == "active"
    assert supervision_payload["polls_completed"] == 2
    assert supervision_payload["monitoring_mode"] == "rest_polling"

    session_status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert session_status["supervision_state"] == "active"
    assert session_status["supervision_poll_count"] == 2
    assert session_status["fill_summary_state"] == "partial"
    assert session_status["alert_status"] == "ok"
    assert session_status["alerts_present"] is False


def test_hyperliquid_submit_alerts_include_cancel_failures(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_cancel_response.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.cancel_response",
                "generated_at": "2026-03-27T12:07:00",
                "cancel_state": "cancel_request_failed",
                "cancel_accepted": False,
                "remote_cancel_called": True,
                "errors": ["cancel_request_failed:TimeoutError"],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(hyperliquid_submit_sessions_alerts=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    payload = json.loads(capsys.readouterr().out)
    assert payload["alert_status"] == "critical"
    assert any(alert["alert_code"] == "HYPERLIQUID_CANCEL_REQUEST_FAILED" for alert in payload["alerts"])


def test_hyperliquid_submit_alerts_include_supervision_attention(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_supervision.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.supervision",
                "generated_at": "2026-03-27T12:09:00",
                "supervision_state": "attention_required",
                "attention_required": True,
                "polls_completed": 3,
                "errors": ["order_status_probe_failed:TimeoutError"],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(hyperliquid_submit_sessions_alerts=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    payload = json.loads(capsys.readouterr().out)
    assert payload["has_alerts"] is True
    assert any(alert["alert_code"] == "HYPERLIQUID_SUPERVISION_ATTENTION" for alert in payload["alerts"])


def test_hyperliquid_submit_alerts_use_reconciliation_state(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_order_status.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.order_status",
                "generated_at": "2026-03-27T12:05:00",
                "status_known": False,
                "normalized_state": "unknown",
                "errors": ["missing_order"],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_reconciliation.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.reconciliation",
                "generated_at": "2026-03-27T12:06:00",
                "status_known": True,
                "normalized_state": "open",
                "resolution_source": "open_orders",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(hyperliquid_submit_sessions_alerts=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    payload = json.loads(capsys.readouterr().out)
    assert payload["alert_status"] == "ok"
    assert payload["has_alerts"] is False


def test_hyperliquid_submit_health_includes_fill_and_close_state_counts(tmp_path):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_reconciliation.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.reconciliation",
                "generated_at": "2026-03-27T12:06:00",
                "status_known": True,
                "normalized_state": "filled",
                "close_state": "closed",
                "fill_state": "filled",
                "fill_count": 1,
                "filled_size": "0.25",
                "remaining_size": "0",
                "average_fill_price": "2450.1",
                "last_fill_time": 1764000000300,
                "resolution_source": "user_fills",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    from quantlab.cli.hyperliquid_submit_sessions import build_hyperliquid_submission_health

    payload = build_hyperliquid_submission_health(tmp_path)
    assert payload["close_state_counts"]["closed"] == 1
    assert payload["fill_state_counts"]["filled"] == 1
    assert payload["latest_close_state"] == "closed"
    assert payload["latest_fill_state"] == "filled"


def test_load_hyperliquid_submit_summary_includes_fill_summary_fields(tmp_path):
    session_dir = _write_session(tmp_path, name="20260327_hyperliquid_fill_demo")
    (session_dir / "hyperliquid_fill_summary.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.fill_summary",
                "generated_at": "2026-03-27T12:08:00",
                "fills_known": True,
                "fill_state": "partial",
                "fill_count": 1,
                "filled_size": "0.15",
                "remaining_size": "0.10",
                "average_fill_price": "2451",
                "total_fee": "0.2",
                "total_builder_fee": "0.05",
                "total_closed_pnl": None,
                "first_fill_time": 1764000000000,
                "last_fill_time": 1764000000000,
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    summary = load_hyperliquid_submit_summary(session_dir)
    assert summary["fill_summary_present"] is True
    assert summary["fill_summary_state"] == "partial"
    assert summary["fill_summary_count"] == 1
    assert summary["fill_summary_total_fee"] == "0.2"


def test_load_hyperliquid_submit_summary_includes_supervision_fields(tmp_path):
    session_dir = _write_session(tmp_path, name="20260327_hyperliquid_supervision_demo")
    (session_dir / "hyperliquid_supervision.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.supervision",
                "generated_at": "2026-03-27T12:09:00",
                "supervision_state": "active",
                "attention_required": False,
                "polls_completed": 3,
                "polls_requested": 3,
                "monitoring_mode": "websocket_aware_rest_polling",
                "transport_preference": "websocket",
                "resolved_transport": "websocket",
                "last_observed_at": "2026-03-27T12:09:00",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    summary = load_hyperliquid_submit_summary(session_dir)
    assert summary["supervision_present"] is True
    assert summary["supervision_state"] == "active"
    assert summary["supervision_poll_count"] == 3
    assert summary["supervision_monitoring_mode"] == "websocket_aware_rest_polling"


def test_invalid_hyperliquid_submit_session_raises(tmp_path):
    session_dir = tmp_path / "bad_session"
    session_dir.mkdir()

    with pytest.raises(ConfigError):
        load_hyperliquid_submit_summary(session_dir)
