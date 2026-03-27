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
        "hyperliquid_submit_sessions_status": None,
        "hyperliquid_submit_sessions_reconcile": None,
        "hyperliquid_submit_sessions_health": None,
        "hyperliquid_submit_sessions_alerts": None,
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
    summary = load_hyperliquid_submit_summary(session_dir)

    assert summary["session_id"] == "20260327_hyperliquid_submit_demo"
    assert summary["status"] == "submitted"
    assert summary["submit_state"] == "submitted_remote"
    assert summary["submitted"] is True
    assert summary["signed_action_present"] is True
    assert summary["submit_response_present"] is True


def test_list_hyperliquid_submit_sessions(tmp_path, capsys):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_list=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit sessions in" in output
    assert "submitted_remote" in output


def test_show_hyperliquid_submit_session(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_show=str(session_dir))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit session" in output
    assert "submitted_remote" in output


def test_refresh_hyperliquid_submit_index(tmp_path):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_index=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    assert (tmp_path / "hyperliquid_submits_index.json").exists()
    assert (tmp_path / "hyperliquid_submits_index.csv").exists()


def test_hyperliquid_submit_health_summary(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    (session_dir / "hyperliquid_order_status.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.order_status",
                "generated_at": "2026-03-27T12:05:00",
                "status_known": True,
                "normalized_state": "open",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(hyperliquid_submit_sessions_health=str(tmp_path))
    assert handle_hyperliquid_submit_sessions_commands(args) is True

    output = capsys.readouterr().out
    assert "Hyperliquid submission health" in output
    assert "total_sessions" in output
    assert "reconciliation_sessions" in output
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


def test_invalid_hyperliquid_submit_session_raises(tmp_path):
    session_dir = tmp_path / "bad_session"
    session_dir.mkdir()

    with pytest.raises(ConfigError):
        load_hyperliquid_submit_summary(session_dir)
