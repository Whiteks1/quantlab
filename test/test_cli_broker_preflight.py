from __future__ import annotations

import json
import types

import pytest

from quantlab.cli.broker_preflight import handle_broker_preflight_commands
from quantlab.errors import ConfigError


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "hyperliquid_preflight_outdir": None,
        "hyperliquid_account_readiness_outdir": None,
        "hyperliquid_signed_action_outdir": None,
        "hyperliquid_submit_signed_action": None,
        "hyperliquid_submit_session": None,
        "hyperliquid_submit_reviewer": None,
        "hyperliquid_submit_note": None,
        "hyperliquid_submit_confirm": False,
        "hyperliquid_submit_sessions_root": None,
        "hyperliquid_submit_sessions_list": None,
        "hyperliquid_submit_sessions_show": None,
        "hyperliquid_submit_sessions_index": None,
        "hyperliquid_private_key": None,
        "hyperliquid_private_key_env": "HYPERLIQUID_PRIVATE_KEY",
        "kraken_preflight_outdir": None,
        "kraken_auth_preflight_outdir": None,
        "kraken_account_readiness_outdir": None,
        "kraken_order_validate_outdir": None,
        "kraken_order_validate_session": False,
        "kraken_preflight_timeout": 10.0,
        "hyperliquid_preflight_timeout": 10.0,
        "broker_symbol": None,
        "ticker": None,
        "broker_side": None,
        "broker_quantity": None,
        "broker_notional": None,
        "broker_account_id": None,
        "broker_strategy_id": None,
        "broker_max_notional": None,
        "broker_allowed_symbols": None,
        "broker_order_validations_root": None,
        "broker_order_validations_list": None,
        "broker_order_validations_show": None,
        "broker_order_validations_index": None,
        "broker_kill_switch": False,
        "broker_allow_missing_account_id": False,
        "kraken_api_key": None,
        "kraken_api_secret": None,
        "kraken_api_key_env": "KRAKEN_API_KEY",
        "kraken_api_secret_env": "KRAKEN_API_SECRET",
        "execution_account_id": None,
        "execution_signer_id": None,
        "execution_signer_type": None,
        "execution_routing_target": None,
        "execution_transport_preference": None,
        "execution_expires_after": None,
        "execution_nonce": None,
        "_request_id": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_writes_preflight_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, symbol, *, timeout_seconds=10.0):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.preflight",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-25T12:00:00",
                    "symbol_input": symbol,
                    "normalized_symbol": "ETH/USD",
                    "public_api_reachable": True,
                    "pair_supported": True,
                    "server_time_unix": 1700000000,
                    "server_time_rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT",
                    "matched_pair_key": "XETHZUSD",
                    "matched_pair_wsname": "ETH/USD",
                    "matched_pair_altname": "ETHUSD",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_public_preflight_report", fake_report)

    outdir = tmp_path / "preflight"
    args = _make_args(kraken_preflight_outdir=str(outdir), broker_symbol="ETH-USD")
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["pair_supported"] is True
    artifact_path = outdir / "broker_preflight.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.kraken.preflight"
    assert payload["pair_supported"] is True


def test_writes_hyperliquid_preflight_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, symbol, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.preflight",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-26T12:00:00",
                    "symbol_input": symbol,
                    "normalized_symbol": "ETH",
                    "market_type": "perp",
                    "metadata_type": "meta",
                    "public_api_reachable": True,
                    "market_supported": True,
                    "matched_name": "ETH",
                    "resolved_coin": "ETH",
                    "resolved_asset": 1,
                    "mid_price": "2450.1",
                    "rest_info_url": "https://api.hyperliquid.xyz/info",
                    "websocket_url": "wss://api.hyperliquid.xyz/ws",
                    "execution_context": {
                        "execution_account_id": "0x1111111111111111111111111111111111111111",
                        "query_user": "0x1111111111111111111111111111111111111111",
                        "signer_id": "0x2222222222222222222222222222222222222222",
                        "signer_type": "agent_wallet",
                        "routing_target": "subaccount",
                        "transport_preference": "websocket",
                        "resolved_transport": "websocket",
                        "expires_after": 60000,
                        "nonce_scope": "0x2222222222222222222222222222222222222222",
                        "query_address_matches_signer": False,
                        "execution_account_role": "subAccount",
                        "signer_role": "agent",
                        "context_ready": True,
                        "reasons": [],
                    },
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_public_preflight_report", fake_report)

    outdir = tmp_path / "hyperliquid_preflight"
    args = _make_args(
        hyperliquid_preflight_outdir=str(outdir),
        broker_symbol="ETH",
        execution_account_id="0x1111111111111111111111111111111111111111",
        execution_signer_id="0x2222222222222222222222222222222222222222",
        execution_signer_type="agent_wallet",
        execution_routing_target="subaccount",
        execution_transport_preference="websocket",
        execution_expires_after=60000,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["market_supported"] is True
    assert result["resolved_transport"] == "websocket"

    artifact_path = outdir / "broker_preflight.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.hyperliquid.preflight"
    assert payload["execution_context"]["signer_type"] == "agent_wallet"


def test_writes_hyperliquid_account_readiness_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.account_readiness",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-26T12:00:00",
                    "execution_context": {
                        "execution_account_id": "0x1111111111111111111111111111111111111111",
                        "query_user": "0x1111111111111111111111111111111111111111",
                        "signer_id": "0x2222222222222222222222222222222222222222",
                        "signer_type": "agent_wallet",
                        "routing_target": "subaccount",
                        "transport_preference": "websocket",
                        "resolved_transport": "websocket",
                        "expires_after": 60000,
                        "nonce_scope": "0x2222222222222222222222222222222222222222",
                        "query_address_matches_signer": False,
                        "execution_account_role": "subAccount",
                        "signer_role": "agent",
                        "context_ready": True,
                        "reasons": [],
                    },
                    "account_visibility_available": True,
                    "open_orders_count": 0,
                    "frontend_open_orders_count": 0,
                    "open_orders_sample": [],
                    "frontend_open_orders_sample": [],
                    "readiness_allowed": True,
                    "readiness_reasons": [],
                    "rest_info_url": "https://api.hyperliquid.xyz/info",
                    "websocket_url": "wss://api.hyperliquid.xyz/ws",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_account_readiness_report", fake_report)

    outdir = tmp_path / "hyperliquid_account_readiness"
    args = _make_args(
        hyperliquid_account_readiness_outdir=str(outdir),
        execution_account_id="0x1111111111111111111111111111111111111111",
        execution_signer_id="0x2222222222222222222222222222222222222222",
        execution_signer_type="agent_wallet",
        execution_routing_target="subaccount",
        execution_transport_preference="websocket",
        execution_expires_after=60000,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["readiness_allowed"] is True
    assert result["account_visibility_available"] is True

    artifact_path = outdir / "hyperliquid_account_readiness.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.hyperliquid.account_readiness"
    assert payload["execution_context"]["execution_account_role"] == "subAccount"


def test_writes_hyperliquid_signed_action_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, intent, policy, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.signed_action",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-26T12:00:00",
                    "intent": {
                        "broker_target": "hyperliquid",
                        "symbol": intent.symbol,
                        "side": intent.side,
                        "quantity": intent.quantity,
                        "notional": intent.notional,
                        "account_id": intent.account_id,
                        "strategy_id": intent.strategy_id,
                        "request_id": intent.request_id,
                        "dry_run": True,
                    },
                    "policy": {
                        "kill_switch_active": False,
                        "max_notional_per_order": None,
                        "allowed_symbols": [],
                        "require_account_id": True,
                    },
                    "local_preflight": {"allowed": True, "reasons": []},
                    "public_preflight": {
                        "artifact_type": "quantlab.hyperliquid.preflight",
                        "adapter_name": "hyperliquid",
                        "generated_at": "2026-03-26T12:00:00",
                        "symbol_input": intent.symbol,
                        "normalized_symbol": "ETH",
                        "market_type": "perp",
                        "metadata_type": "meta",
                        "public_api_reachable": True,
                        "market_supported": True,
                        "matched_name": "ETH",
                        "resolved_coin": "ETH",
                        "resolved_asset": 1,
                        "mid_price": "2450.1",
                        "rest_info_url": "https://api.hyperliquid.xyz/info",
                        "websocket_url": "wss://api.hyperliquid.xyz/ws",
                        "execution_context": {},
                        "errors": [],
                    },
                    "account_readiness": {
                        "artifact_type": "quantlab.hyperliquid.account_readiness",
                        "adapter_name": "hyperliquid",
                        "generated_at": "2026-03-26T12:00:00",
                        "execution_context": {
                            "execution_account_id": "0x1111111111111111111111111111111111111111",
                            "query_user": "0x1111111111111111111111111111111111111111",
                            "signer_id": "0x2222222222222222222222222222222222222222",
                            "signer_type": "agent_wallet",
                            "routing_target": "subaccount",
                            "transport_preference": "websocket",
                            "resolved_transport": "websocket",
                            "expires_after": 60000,
                            "nonce_scope": "0x2222222222222222222222222222222222222222",
                            "query_address_matches_signer": False,
                            "execution_account_role": "subAccount",
                            "signer_role": "agent",
                            "context_ready": True,
                            "reasons": [],
                        },
                        "account_visibility_available": True,
                        "open_orders_count": 0,
                        "frontend_open_orders_count": 0,
                        "open_orders_sample": [],
                        "frontend_open_orders_sample": [],
                        "readiness_allowed": True,
                        "readiness_reasons": [],
                        "rest_info_url": "https://api.hyperliquid.xyz/info",
                        "websocket_url": "wss://api.hyperliquid.xyz/ws",
                        "errors": [],
                    },
                    "nonce": 1700000000000,
                    "nonce_source": "context_nonce_hint",
                    "expires_after": 1700000060000,
                    "expires_after_mode": "relative_ms",
                    "signature_envelope": {
                        "signer_id": "0x2222222222222222222222222222222222222222",
                        "nonce_scope": "0x2222222222222222222222222222222222222222",
                        "signing_scheme": "hyperliquid_l1_action",
                        "signature_state": "signed",
                        "signature_present": True,
                        "signature_reason": None,
                        "signing_payload": {},
                        "signing_payload_sha256": "abc123",
                        "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    },
                    "action_payload": {
                        "type": "order",
                        "orders": [{"a": 1, "b": True, "p": "2450.1", "s": "0.25", "r": False, "t": {"limit": {"tif": "Ioc"}}}],
                        "grouping": "na",
                    },
                    "readiness_allowed": True,
                    "readiness_reasons": [],
                    "signer_backend": "hyperliquid_local_private_key",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_signed_action_report", fake_report)

    outdir = tmp_path / "hyperliquid_signed_action"
    args = _make_args(
        hyperliquid_signed_action_outdir=str(outdir),
        broker_symbol="ETH",
        broker_side="buy",
        broker_quantity=0.25,
        broker_notional=500.0,
        execution_account_id="0x1111111111111111111111111111111111111111",
        execution_signer_id="0x2222222222222222222222222222222222222222",
        execution_signer_type="agent_wallet",
        execution_routing_target="subaccount",
        execution_transport_preference="websocket",
        execution_expires_after=60000,
        execution_nonce=1700000000000,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["readiness_allowed"] is True
    assert result["signature_state"] == "signed"

    artifact_path = outdir / "hyperliquid_signed_action.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.hyperliquid.signed_action"
    assert payload["nonce"] == 1700000000000
    assert payload["signature_envelope"]["signature_present"] is True
    assert payload["signer_backend"] == "hyperliquid_local_private_key"


def test_writes_hyperliquid_submit_response_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    signed_action_path = tmp_path / "hyperliquid_signed_action.json"
    signed_action_path.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "readiness_allowed": True,
                "action_payload": {"type": "order", "orders": [], "grouping": "na"},
                "nonce": 1700000000000,
                "signature_envelope": {
                    "signature_state": "signed",
                    "signature_present": True,
                    "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    "signer_id": "0x2222222222222222222222222222222222222222",
                    "signing_payload_sha256": "abc123",
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_submit(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.submit_response",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:00:00",
                    "source_artifact_path": str(signed_action_path),
                    "source_action_hash": "0xabc",
                    "source_signer_id": "0x2222222222222222222222222222222222222222",
                    "source_signing_payload_sha256": "abc123",
                    "submit_payload": {
                        "action": {"type": "order"},
                        "nonce": 1700000000000,
                        "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    },
                    "submit_state": "submitted_remote",
                    "remote_submit_called": True,
                    "submitted": True,
                    "response_type": "resting",
                    "exchange_response": {"status": "ok"},
                    "reviewer": "marce",
                    "note": "go",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_submit_report", fake_submit)

    args = _make_args(
        hyperliquid_submit_signed_action=str(signed_action_path),
        hyperliquid_submit_reviewer="marce",
        hyperliquid_submit_note="go",
        hyperliquid_submit_confirm=True,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["submitted"] is True
    assert result["submit_state"] == "submitted_remote"

    artifact_path = tmp_path / "hyperliquid_submit_response.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.hyperliquid.submit_response"
    assert payload["reviewer"] == "marce"


def test_hyperliquid_submit_requires_confirmation(tmp_path):
    signed_action_path = tmp_path / "hyperliquid_signed_action.json"
    signed_action_path.write_text("{}", encoding="utf-8")

    args = _make_args(
        hyperliquid_submit_signed_action=str(signed_action_path),
        hyperliquid_submit_reviewer="marce",
        hyperliquid_submit_confirm=False,
    )

    with pytest.raises(ConfigError):
        handle_broker_preflight_commands(args)


def test_writes_hyperliquid_submit_session(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    signed_action_path = tmp_path / "hyperliquid_signed_action.json"
    signed_action_path.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "readiness_allowed": True,
                "intent": {"symbol": "ETH", "side": "buy"},
                "nonce": 1700000000000,
                "signature_envelope": {
                    "signature_state": "signed",
                    "signature_present": True,
                    "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    "signer_id": "0x2222222222222222222222222222222222222222",
                    "signing_payload_sha256": "abc123",
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_submit(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.submit_response",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:00:00",
                    "source_artifact_path": str(signed_action_path),
                    "source_action_hash": "0xabc",
                    "source_signer_id": "0x2222222222222222222222222222222222222222",
                    "source_signing_payload_sha256": "abc123",
                    "submit_payload": {
                        "action": {"type": "order"},
                        "nonce": 1700000000000,
                        "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    },
                    "submit_state": "submitted_remote",
                    "remote_submit_called": True,
                    "submitted": True,
                    "response_type": "resting",
                    "exchange_response": {"status": "ok"},
                    "reviewer": "marce",
                    "note": "go",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_submit_report", fake_submit)

    root_dir = tmp_path / "hyperliquid_submits"
    args = _make_args(
        hyperliquid_submit_session=str(signed_action_path),
        hyperliquid_submit_reviewer="marce",
        hyperliquid_submit_note="go",
        hyperliquid_submit_confirm=True,
        hyperliquid_submit_sessions_root=str(root_dir),
        _request_id="req_hl_submit_001",
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["submitted"] is True
    assert result["submit_state"] == "submitted_remote"

    session_dirs = [child for child in root_dir.iterdir() if child.is_dir()]
    assert len(session_dirs) == 1
    session_dir = session_dirs[0]
    assert (session_dir / "hyperliquid_signed_action.json").exists()
    assert (session_dir / "hyperliquid_submit_response.json").exists()
    assert (session_dir / "session_metadata.json").exists()
    assert (session_dir / "session_status.json").exists()
    assert (root_dir / "hyperliquid_submits_index.json").exists()
    assert (root_dir / "hyperliquid_submits_index.csv").exists()


def test_hyperliquid_submit_session_refuses_duplicate_replay(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    signed_action_path = tmp_path / "hyperliquid_signed_action.json"
    signed_action_path.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "readiness_allowed": True,
                "intent": {"symbol": "ETH", "side": "buy"},
                "nonce": 1700000000000,
                "signature_envelope": {
                    "signature_state": "signed",
                    "signature_present": True,
                    "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    "signer_id": "0x2222222222222222222222222222222222222222",
                    "signing_payload_sha256": "abc123",
                },
            }
        ),
        encoding="utf-8",
    )

    calls = {"count": 0}

    def fake_submit(self, **kwargs):
        calls["count"] += 1

        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.hyperliquid.submit_response",
                    "adapter_name": "hyperliquid",
                    "generated_at": "2026-03-27T12:00:00",
                    "source_artifact_path": str(signed_action_path),
                    "source_action_hash": "0xabc",
                    "source_signer_id": "0x2222222222222222222222222222222222222222",
                    "source_signing_payload_sha256": "abc123",
                    "submit_payload": {
                        "action": {"type": "order"},
                        "nonce": 1700000000000,
                        "signature": {"r": "0x1", "s": "0x2", "v": 27},
                    },
                    "submit_state": "submitted_remote",
                    "remote_submit_called": True,
                    "submitted": True,
                    "response_type": "resting",
                    "exchange_response": {"status": "ok"},
                    "reviewer": "marce",
                    "note": "go",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.HyperliquidBrokerAdapter, "build_submit_report", fake_submit)

    root_dir = tmp_path / "hyperliquid_submits"
    args = _make_args(
        hyperliquid_submit_session=str(signed_action_path),
        hyperliquid_submit_reviewer="marce",
        hyperliquid_submit_note="go",
        hyperliquid_submit_confirm=True,
        hyperliquid_submit_sessions_root=str(root_dir),
        _request_id="req_hl_submit_001",
    )

    first = handle_broker_preflight_commands(args)
    assert first["status"] == "success"
    assert calls["count"] == 1

    with pytest.raises(ConfigError, match="already has a persisted submit response"):
        handle_broker_preflight_commands(args)

    assert calls["count"] == 1


def test_missing_symbol_raises_config_error(tmp_path):
    args = _make_args(kraken_preflight_outdir=str(tmp_path / "preflight"))
    with pytest.raises(ConfigError):
        handle_broker_preflight_commands(args)


def test_no_command_returns_false():
    assert handle_broker_preflight_commands(_make_args()) is False


def test_writes_auth_preflight_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.auth_preflight",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-25T12:00:00",
                    "credentials_present": True,
                    "authenticated": True,
                    "api_key_env": "KRAKEN_API_KEY",
                    "api_secret_env": "KRAKEN_API_SECRET",
                    "key_name": "quantlab-demo",
                    "permissions": {"orders": "read"},
                    "restrictions": {"ip": ["127.0.0.1"]},
                    "created_at": "2026-03-25T12:00:00Z",
                    "updated_at": "2026-03-25T13:00:00Z",
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_authenticated_preflight_report", fake_report)

    outdir = tmp_path / "auth_preflight"
    args = _make_args(
        kraken_auth_preflight_outdir=str(outdir),
        kraken_api_key_env="KRAKEN_API_KEY",
        kraken_api_secret_env="KRAKEN_API_SECRET",
        kraken_api_key=None,
        kraken_api_secret=None,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["authenticated"] is True
    artifact_path = outdir / "broker_auth_preflight.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.kraken.auth_preflight"
    assert payload["authenticated"] is True


def test_writes_auth_preflight_artifact_when_credentials_missing(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.auth_preflight",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-25T12:00:00",
                    "credentials_present": False,
                    "authenticated": False,
                    "api_key_env": "KRAKEN_API_KEY",
                    "api_secret_env": "KRAKEN_API_SECRET",
                    "key_name": None,
                    "permissions": None,
                    "restrictions": None,
                    "created_at": None,
                    "updated_at": None,
                    "errors": ["missing_api_key", "missing_api_secret"],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_authenticated_preflight_report", fake_report)

    outdir = tmp_path / "auth_preflight_missing"
    args = _make_args(
        kraken_auth_preflight_outdir=str(outdir),
        kraken_api_key_env="KRAKEN_API_KEY",
        kraken_api_secret_env="KRAKEN_API_SECRET",
        kraken_api_key=None,
        kraken_api_secret=None,
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["authenticated"] is False
    artifact_path = outdir / "broker_auth_preflight.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["credentials_present"] is False
    assert "missing_api_key" in payload["errors"]


def test_writes_account_readiness_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, intent, policy, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.account_snapshot",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-25T12:00:00",
                    "symbol_input": intent.symbol,
                    "normalized_symbol": "ETH/USD",
                    "public_api_reachable": True,
                    "pair_supported": True,
                    "matched_pair_key": "XETHZUSD",
                    "matched_pair_wsname": "ETH/USD",
                    "matched_pair_altname": "ETHUSD",
                    "base_asset": "XETH",
                    "quote_asset": "ZUSD",
                    "pair_status": "online",
                    "ordermin": 0.001,
                    "costmin": 0.5,
                    "tick_size": 0.01,
                    "account_snapshot_available": True,
                    "balances": [
                        {
                            "asset": "ZUSD",
                            "balance": 1000.0,
                            "credit": 0.0,
                            "credit_used": 0.0,
                            "hold_trade": 0.0,
                            "available": 1000.0,
                        }
                    ],
                    "authenticated_preflight": {
                        "artifact_type": "quantlab.kraken.auth_preflight",
                        "adapter_name": "kraken",
                        "generated_at": "2026-03-25T12:00:00",
                        "credentials_present": True,
                        "authenticated": True,
                        "api_key_env": "KRAKEN_API_KEY",
                        "api_secret_env": "KRAKEN_API_SECRET",
                        "key_name": "quantlab-demo",
                        "permissions": {"funds": "query"},
                        "restrictions": {},
                        "created_at": None,
                        "updated_at": None,
                        "errors": [],
                    },
                    "intent": {
                        "broker_target": "kraken",
                        "symbol": intent.symbol,
                        "side": intent.side,
                        "quantity": intent.quantity,
                        "notional": intent.notional,
                        "account_id": intent.account_id,
                        "strategy_id": intent.strategy_id,
                        "request_id": intent.request_id,
                        "dry_run": True,
                    },
                    "policy": {
                        "kill_switch_active": False,
                        "max_notional_per_order": None,
                        "allowed_symbols": [],
                        "require_account_id": True,
                    },
                    "local_preflight": {"allowed": True, "reasons": []},
                    "intent_readiness": {
                        "allowed": True,
                        "reasons": [],
                        "funding_asset": "ZUSD",
                        "funding_basis": "notional",
                        "required_amount": 500.0,
                        "available_amount": 1000.0,
                    },
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_account_snapshot_report", fake_report)

    outdir = tmp_path / "account_readiness"
    args = _make_args(
        kraken_account_readiness_outdir=str(outdir),
        broker_symbol="ETH-USD",
        broker_side="buy",
        broker_quantity=0.25,
        broker_notional=500.0,
        broker_account_id="acct_demo",
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["readiness_allowed"] is True
    artifact_path = outdir / "broker_account_snapshot.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.kraken.account_snapshot"
    assert payload["intent_readiness"]["allowed"] is True
    assert payload["authenticated_preflight"]["authenticated"] is True


def test_account_readiness_requires_intent_inputs(tmp_path):
    args = _make_args(kraken_account_readiness_outdir=str(tmp_path / "account_readiness"))
    with pytest.raises(ConfigError):
        handle_broker_preflight_commands(args)


def test_writes_order_validate_artifact(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, intent, policy, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.order_validate",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-26T08:00:00",
                    "authenticated_preflight": {
                        "artifact_type": "quantlab.kraken.auth_preflight",
                        "adapter_name": "kraken",
                        "generated_at": "2026-03-26T08:00:00",
                        "credentials_present": True,
                        "authenticated": True,
                        "api_key_env": "KRAKEN_API_KEY",
                        "api_secret_env": "KRAKEN_API_SECRET",
                        "key_name": "quantlab-demo",
                        "permissions": {"orders": "create_modify"},
                        "restrictions": {},
                        "created_at": None,
                        "updated_at": None,
                        "errors": [],
                    },
                    "intent": {
                        "broker_target": "kraken",
                        "symbol": intent.symbol,
                        "side": intent.side,
                        "quantity": intent.quantity,
                        "notional": intent.notional,
                        "account_id": intent.account_id,
                        "strategy_id": intent.strategy_id,
                        "request_id": intent.request_id,
                        "dry_run": True,
                    },
                    "policy": {
                        "kill_switch_active": False,
                        "max_notional_per_order": None,
                        "allowed_symbols": [],
                        "require_account_id": True,
                    },
                    "local_preflight": {"allowed": True, "reasons": []},
                    "validate_payload": {
                        "pair": "ETH/USD",
                        "type": "buy",
                        "ordertype": "market",
                        "volume": "0.25",
                        "validate": "true",
                    },
                    "remote_validation_called": True,
                    "validation_accepted": True,
                    "validation_reasons": [],
                    "exchange_response": {"error": [], "result": {"descr": {"order": "buy 0.25 ETHUSD @ market"}}},
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_order_validate_report", fake_report)

    outdir = tmp_path / "order_validate"
    args = _make_args(
        kraken_order_validate_outdir=str(outdir),
        broker_symbol="ETH-USD",
        broker_side="buy",
        broker_quantity=0.25,
        broker_notional=500.0,
        broker_account_id="acct_demo",
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["validation_accepted"] is True
    artifact_path = outdir / "broker_order_validate.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.kraken.order_validate"
    assert payload["remote_validation_called"] is True
    assert payload["validation_accepted"] is True


def test_order_validate_requires_intent_inputs(tmp_path):
    args = _make_args(kraken_order_validate_outdir=str(tmp_path / "order_validate"))
    with pytest.raises(ConfigError):
        handle_broker_preflight_commands(args)


def test_writes_order_validate_session_and_index(monkeypatch, tmp_path):
    from quantlab.cli import broker_preflight as module

    def fake_report(self, intent, policy, **kwargs):
        class _Fake:
            def to_dict(self):
                return {
                    "artifact_type": "quantlab.kraken.order_validate",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-26T08:00:00",
                    "authenticated_preflight": {
                        "artifact_type": "quantlab.kraken.auth_preflight",
                        "adapter_name": "kraken",
                        "generated_at": "2026-03-26T08:00:00",
                        "credentials_present": True,
                        "authenticated": True,
                        "api_key_env": "KRAKEN_API_KEY",
                        "api_secret_env": "KRAKEN_API_SECRET",
                        "key_name": "quantlab-demo",
                        "permissions": {"orders": "create_modify"},
                        "restrictions": {},
                        "created_at": None,
                        "updated_at": None,
                        "errors": [],
                    },
                    "intent": {
                        "broker_target": "kraken",
                        "symbol": intent.symbol,
                        "side": intent.side,
                        "quantity": intent.quantity,
                        "notional": intent.notional,
                        "account_id": intent.account_id,
                        "strategy_id": intent.strategy_id,
                        "request_id": intent.request_id,
                        "dry_run": True,
                    },
                    "policy": {
                        "kill_switch_active": False,
                        "max_notional_per_order": None,
                        "allowed_symbols": [],
                        "require_account_id": True,
                    },
                    "local_preflight": {"allowed": True, "reasons": []},
                    "validate_payload": {
                        "pair": "ETH/USD",
                        "type": "buy",
                        "ordertype": "market",
                        "volume": "0.25",
                        "validate": "true",
                    },
                    "remote_validation_called": True,
                    "validation_accepted": True,
                    "validation_reasons": [],
                    "exchange_response": {"error": [], "result": {"descr": {"order": "buy 0.25 ETHUSD @ market"}}},
                    "errors": [],
                }

        return _Fake()

    monkeypatch.setattr(module.KrakenBrokerAdapter, "build_order_validate_report", fake_report)

    root = tmp_path / "broker_order_validations"
    args = _make_args(
        kraken_order_validate_session=True,
        broker_order_validations_root=str(root),
        broker_symbol="ETH-USD",
        broker_side="buy",
        broker_quantity=0.25,
        broker_notional=500.0,
        broker_account_id="acct_demo",
    )
    result = handle_broker_preflight_commands(args)

    assert isinstance(result, dict)
    assert result["validation_accepted"] is True
    assert result["session_id"]
    session_dir = root / result["session_id"]
    assert (session_dir / "broker_order_validate.json").exists()
    assert (session_dir / "session_metadata.json").exists()
    assert (session_dir / "session_status.json").exists()
    assert (root / "broker_order_validations_index.csv").exists()
    assert (root / "broker_order_validations_index.json").exists()
