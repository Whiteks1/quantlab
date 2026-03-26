from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from quantlab.cli.broker_order_validations import (
    handle_broker_order_validations_commands,
    load_broker_order_validation_summary,
)
from quantlab.errors import ConfigError
from quantlab.reporting.broker_order_validation_index import build_broker_order_validations_index


@pytest.fixture()
def broker_order_validations_root(tmp_path: Path) -> Path:
    root = tmp_path / "broker_order_validations"
    root.mkdir()

    for session_id, status, accepted, remote_called in [
        ("validate_001", "validated", True, True),
        ("validate_002", "rejected_remote", False, True),
    ]:
        session_dir = root / session_id
        session_dir.mkdir()
        (session_dir / "session_metadata.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "adapter_name": "kraken",
                    "status": status,
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
                    "status": status,
                    "updated_at": "2026-03-26T10:05:00",
                    "remote_validation_called": remote_called,
                    "validation_accepted": accepted,
                    "validation_reasons": [] if accepted else ["EOrder:Insufficient funds"],
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "broker_order_validate.json").write_text(
            json.dumps(
                {
                    "artifact_type": "quantlab.kraken.order_validate",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-26T10:05:00",
                    "authenticated_preflight": {"authenticated": True},
                    "intent": {"request_id": f"req_{session_id}"},
                    "local_preflight": {"allowed": True, "reasons": []},
                    "validate_payload": {
                        "pair": "ETH/USD",
                        "type": "buy",
                        "ordertype": "market",
                        "volume": "0.25",
                        "validate": "true",
                    },
                    "remote_validation_called": remote_called,
                    "validation_accepted": accepted,
                    "validation_reasons": [] if accepted else ["EOrder:Insufficient funds"],
                    "exchange_response": {"error": [] if accepted else ["EOrder:Insufficient funds"]},
                    "errors": [] if accepted else ["EOrder:Insufficient funds"],
                }
            ),
            encoding="utf-8",
        )

    return root


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "broker_order_validations_list": None,
        "broker_order_validations_show": None,
        "broker_order_validations_index": None,
        "broker_order_validations_approve": None,
        "broker_order_validations_bundle": None,
        "broker_order_validations_submit_gate": None,
        "broker_order_validations_submit_stub": None,
        "broker_order_validations_submit_real": None,
        "broker_order_validations_reconcile": None,
        "broker_approval_reviewer": None,
        "broker_approval_note": None,
        "broker_submit_reviewer": None,
        "broker_submit_note": None,
        "broker_submit_confirm": False,
        "broker_submit_live": False,
        "kraken_api_key": None,
        "kraken_api_secret": None,
        "kraken_api_key_env": "KRAKEN_API_KEY",
        "kraken_api_secret_env": "KRAKEN_API_SECRET",
        "kraken_preflight_timeout": 10.0,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_lists_broker_order_validation_sessions(broker_order_validations_root: Path, capsys):
    args = _make_args(broker_order_validations_list=str(broker_order_validations_root))
    result = handle_broker_order_validations_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "validate_001" in out
    assert "validate_002" in out
    assert "validated" in out
    assert "rejected_remote" in out


def test_shows_single_broker_order_validation_session(broker_order_validations_root: Path, capsys):
    args = _make_args(broker_order_validations_show=str(broker_order_validations_root / "validate_002"))
    result = handle_broker_order_validations_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "validate_002" in out
    assert "EOrder:Insufficient funds" in out
    assert "quantlab.kraken.order_validate" in out


def test_builds_broker_order_validations_index(broker_order_validations_root: Path):
    payload = build_broker_order_validations_index(broker_order_validations_root)

    assert payload["n_sessions"] == 2
    assert payload["sessions"][0]["session_id"] == "validate_001"
    assert payload["sessions"][1]["validation_accepted"] is False


def test_invalid_session_dir_raises_config_error(broker_order_validations_root: Path):
    invalid_dir = broker_order_validations_root / "not_a_session"
    invalid_dir.mkdir()
    args = _make_args(broker_order_validations_show=str(invalid_dir))
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_load_summary_requires_valid_dir(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_broker_order_validation_summary(tmp_path / "missing")


def test_approves_broker_order_validation_session(broker_order_validations_root: Path, capsys):
    args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
        broker_approval_note="Approved after validate-only review",
    )
    result = handle_broker_order_validations_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker order validation approved" in out

    approval_path = broker_order_validations_root / "validate_001" / "approval.json"
    assert approval_path.exists()

    payload = json.loads(approval_path.read_text(encoding="utf-8"))
    assert payload["status"] == "approved"
    assert payload["reviewed_by"] == "marce"
    assert payload["note"] == "Approved after validate-only review"


def test_show_includes_approval_state_after_approval(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    show_args = _make_args(broker_order_validations_show=str(broker_order_validations_root / "validate_001"))
    result = handle_broker_order_validations_commands(show_args)
    assert result is True

    out = capsys.readouterr().out
    assert "approval_status" in out
    assert "approved" in out
    assert "marce" in out


def test_approve_requires_reviewer(broker_order_validations_root: Path):
    args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer=None,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_generates_pre_submit_bundle_from_approved_session(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    result = handle_broker_order_validations_commands(bundle_args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker pre-submit bundle generated" in out

    bundle_path = broker_order_validations_root / "validate_001" / "broker_pre_submit_bundle.json"
    assert bundle_path.exists()
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.broker.pre_submit_bundle"
    assert payload["source_session_id"] == "validate_001"
    assert payload["approval"]["status"] == "approved"
    assert payload["bundle_state"] == "ready_for_supervised_submit"


def test_bundle_requires_approved_session(broker_order_validations_root: Path):
    args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_002"),
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_generates_supervised_submit_gate_from_bundle(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(bundle_args) is True
    _ = capsys.readouterr()

    gate_args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_note="Ready for supervised submit review",
        broker_submit_confirm=True,
    )
    result = handle_broker_order_validations_commands(gate_args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker supervised submit gate generated" in out

    gate_path = broker_order_validations_root / "validate_001" / "broker_submit_gate.json"
    assert gate_path.exists()
    payload = json.loads(gate_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.broker.submit_gate"
    assert payload["source_session_id"] == "validate_001"
    assert payload["confirmed_by"] == "marce"
    assert payload["submit_state"] == "ready_for_supervised_submit_gate"


def test_submit_gate_requires_pre_submit_bundle(broker_order_validations_root: Path):
    args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_submit_gate_requires_explicit_confirmation(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(bundle_args) is True
    _ = capsys.readouterr()

    gate_args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=False,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(gate_args)


def test_generates_supervised_submit_stub_from_submit_gate(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(bundle_args) is True
    _ = capsys.readouterr()

    gate_args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
    )
    assert handle_broker_order_validations_commands(gate_args) is True
    _ = capsys.readouterr()

    stub_args = _make_args(
        broker_order_validations_submit_stub=str(broker_order_validations_root / "validate_001"),
    )
    result = handle_broker_order_validations_commands(stub_args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker supervised submit stub generated" in out

    attempt_path = broker_order_validations_root / "validate_001" / "broker_submit_attempt.json"
    assert attempt_path.exists()
    payload = json.loads(attempt_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.broker.submit_attempt"
    assert payload["submit_mode"] == "stub"
    assert payload["would_submit"] is True
    assert payload["source_session_id"] == "validate_001"


def test_submit_stub_requires_submit_gate(broker_order_validations_root: Path):
    args = _make_args(
        broker_order_validations_submit_stub=str(broker_order_validations_root / "validate_001"),
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_generates_real_submit_response_from_submit_gate(broker_order_validations_root: Path, capsys, monkeypatch):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(bundle_args) is True
    _ = capsys.readouterr()

    gate_args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
    )
    assert handle_broker_order_validations_commands(gate_args) is True
    _ = capsys.readouterr()

    def fake_submit(self, **kwargs):
        if kwargs.get("remote_submit") is False:
            return types.SimpleNamespace(
                to_dict=lambda: {
                    "artifact_type": "quantlab.kraken.submit_response",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-26T10:09:59",
                    "authenticated_preflight": {"authenticated": True},
                    "source_session_id": "validate_001",
                    "submit_payload": {
                        "pair": "ETH/USD",
                        "type": "buy",
                        "ordertype": "market",
                        "volume": "0.25",
                        "userref": "123456",
                    },
                    "userref": 123456,
                    "submit_state": "pending_remote_submit",
                    "remote_submit_called": False,
                    "submitted": False,
                    "txid": [],
                    "exchange_response": None,
                    "errors": [],
                }
            )
        return types.SimpleNamespace(
            to_dict=lambda: {
                "artifact_type": "quantlab.kraken.submit_response",
                "adapter_name": "kraken",
                "generated_at": "2026-03-26T10:10:00",
                "authenticated_preflight": {"authenticated": True},
                "source_session_id": "validate_001",
                "submit_payload": {
                    "pair": "ETH/USD",
                    "type": "buy",
                    "ordertype": "market",
                    "volume": "0.25",
                    "userref": "123456",
                },
                "userref": 123456,
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "txid": ["OABC-123-XYZ"],
                "exchange_response": {"error": [], "result": {"txid": ["OABC-123-XYZ"]}},
                "errors": [],
            }
        )

    monkeypatch.setattr(
        "quantlab.cli.broker_order_validations.KrakenBrokerAdapter.build_order_submit_report",
        fake_submit,
    )

    submit_args = _make_args(
        broker_order_validations_submit_real=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_note="Submit after supervised review",
        broker_submit_confirm=True,
        broker_submit_live=True,
    )
    result = handle_broker_order_validations_commands(submit_args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker supervised submit response generated" in out

    response_path = broker_order_validations_root / "validate_001" / "broker_submit_response.json"
    assert response_path.exists()
    payload = json.loads(response_path.read_text(encoding="utf-8"))
    assert payload["submitted"] is True
    assert payload["txid"] == ["OABC-123-XYZ"]
    assert payload["submitted_by"] == "marce"

    show_args = _make_args(
        broker_order_validations_show=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(show_args) is True
    show_out = capsys.readouterr().out
    assert "submit_response_present" in show_out
    assert "submit_response_submitted" in show_out
    assert "OABC-123-XYZ" in show_out


def test_real_submit_requires_submit_gate(broker_order_validations_root: Path):
    args = _make_args(
        broker_order_validations_submit_real=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
        broker_submit_live=True,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)


def test_real_submit_requires_live_flag(broker_order_validations_root: Path, capsys):
    approve_args = _make_args(
        broker_order_validations_approve=str(broker_order_validations_root / "validate_001"),
        broker_approval_reviewer="marce",
    )
    assert handle_broker_order_validations_commands(approve_args) is True
    _ = capsys.readouterr()

    bundle_args = _make_args(
        broker_order_validations_bundle=str(broker_order_validations_root / "validate_001"),
    )
    assert handle_broker_order_validations_commands(bundle_args) is True
    _ = capsys.readouterr()

    gate_args = _make_args(
        broker_order_validations_submit_gate=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
    )
    assert handle_broker_order_validations_commands(gate_args) is True
    _ = capsys.readouterr()

    submit_args = _make_args(
        broker_order_validations_submit_real=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
        broker_submit_live=False,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(submit_args)


def test_reconcile_updates_existing_submit_response(broker_order_validations_root: Path, capsys, monkeypatch):
    response_path = broker_order_validations_root / "validate_001" / "broker_submit_response.json"
    response_path.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.kraken.submit_response",
                "adapter_name": "kraken",
                "generated_at": "2026-03-26T10:10:00",
                "authenticated_preflight": {"authenticated": True},
                "source_session_id": "validate_001",
                "submit_payload": {"pair": "ETH/USD", "userref": "123456"},
                "userref": 123456,
                "submit_state": "pending_remote_submit",
                "remote_submit_called": False,
                "submitted": False,
                "txid": [],
                "exchange_response": None,
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    def fake_reconcile(self, **kwargs):
        return types.SimpleNamespace(
            to_dict=lambda: {
                "artifact_type": "quantlab.kraken.submit_reconciliation",
                "adapter_name": "kraken",
                "generated_at": "2026-03-26T10:11:00",
                "authenticated_preflight": {"authenticated": True},
                "source_session_id": "validate_001",
                "userref": 123456,
                "reconciliation_attempted": True,
                "matched": True,
                "matched_sources": ["closed"],
                "matched_txid": ["OABC-123-XYZ"],
                "matched_statuses": ["closed"],
                "matched_orders": [{"source": "closed", "txid": "OABC-123-XYZ", "status": "closed"}],
                "errors": [],
            }
        )

    monkeypatch.setattr(
        "quantlab.cli.broker_order_validations.KrakenBrokerAdapter.build_order_reconciliation_report",
        fake_reconcile,
    )

    args = _make_args(
        broker_order_validations_reconcile=str(broker_order_validations_root / "validate_001"),
    )
    result = handle_broker_order_validations_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "Broker submit reconciliation completed" in out

    payload = json.loads(response_path.read_text(encoding="utf-8"))
    assert payload["reconciled"] is True
    assert payload["submit_state"] == "reconciled_closed"
    assert payload["txid"] == ["OABC-123-XYZ"]


def test_real_submit_refuses_blind_resubmit_when_response_already_exists(broker_order_validations_root: Path):
    response_path = broker_order_validations_root / "validate_001" / "broker_submit_response.json"
    response_path.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.kraken.submit_response",
                "submit_state": "pending_remote_submit",
                "remote_submit_called": False,
                "submitted": False,
                "userref": 123456,
                "txid": [],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )

    args = _make_args(
        broker_order_validations_submit_real=str(broker_order_validations_root / "validate_001"),
        broker_submit_reviewer="marce",
        broker_submit_confirm=True,
        broker_submit_live=True,
    )
    with pytest.raises(ConfigError):
        handle_broker_order_validations_commands(args)
