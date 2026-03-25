from __future__ import annotations

import json
import types

import pytest

from quantlab.cli.broker_preflight import handle_broker_preflight_commands
from quantlab.errors import ConfigError


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "kraken_preflight_outdir": None,
        "kraken_auth_preflight_outdir": None,
        "kraken_account_readiness_outdir": None,
        "kraken_order_validate_outdir": None,
        "kraken_preflight_timeout": 10.0,
        "broker_symbol": None,
        "ticker": None,
        "broker_side": None,
        "broker_quantity": None,
        "broker_notional": None,
        "broker_account_id": None,
        "broker_strategy_id": None,
        "broker_max_notional": None,
        "broker_allowed_symbols": None,
        "broker_kill_switch": False,
        "broker_allow_missing_account_id": False,
        "kraken_api_key": None,
        "kraken_api_secret": None,
        "kraken_api_key_env": "KRAKEN_API_KEY",
        "kraken_api_secret_env": "KRAKEN_API_SECRET",
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
