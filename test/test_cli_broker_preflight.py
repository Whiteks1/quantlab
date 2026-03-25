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
        "kraken_preflight_timeout": 10.0,
        "broker_symbol": None,
        "ticker": None,
        "kraken_api_key": None,
        "kraken_api_secret": None,
        "kraken_api_key_env": "KRAKEN_API_KEY",
        "kraken_api_secret_env": "KRAKEN_API_SECRET",
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
