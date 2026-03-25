from __future__ import annotations

from quantlab.brokers import ExecutionIntent, ExecutionPolicy
from quantlab.brokers.kraken import KrakenBrokerAdapter


def _make_intent(**overrides) -> ExecutionIntent:
    payload = {
        "broker_target": "kraken",
        "symbol": "ETH/USD",
        "side": "buy",
        "quantity": 0.25,
        "notional": 500.0,
        "account_id": "acct_demo",
        "strategy_id": "rsi_ma_cross_v2",
        "request_id": "req_kraken_001",
        "dry_run": True,
    }
    payload.update(overrides)
    return ExecutionIntent(**payload)


def test_builds_deterministic_kraken_payload_for_valid_intent():
    adapter = KrakenBrokerAdapter()

    payload = adapter.build_order_payload(_make_intent(symbol="eth-usd"))

    assert payload["pair"] == "ETH/USD"
    assert payload["type"] == "buy"
    assert payload["ordertype"] == "market"
    assert payload["volume"] == "0.25"
    assert payload["dry_run"] is True
    assert payload["request_id"] == "req_kraken_001"


def test_preflight_reuses_shared_boundary_validation():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=100.0)

    result = adapter.preflight(_make_intent(notional=500.0), policy)

    assert result.allowed is False
    assert "max_notional_exceeded" in result.reasons


def test_dry_run_audit_includes_payload_when_preflight_passes():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    audit = adapter.build_dry_run_audit(_make_intent(), policy).to_dict()

    assert audit["adapter_name"] == "kraken"
    assert audit["preflight"]["allowed"] is True
    assert audit["payload"]["pair"] == "ETH/USD"
    assert audit["payload"]["type"] == "buy"
    assert audit["intent"]["broker_target"] == "kraken"


def test_dry_run_audit_omits_payload_when_preflight_fails():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        kill_switch_active=True,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    audit = adapter.build_dry_run_audit(_make_intent(), policy).to_dict()

    assert audit["preflight"]["allowed"] is False
    assert "kill_switch_active" in audit["preflight"]["reasons"]
    assert audit["payload"] is None


def test_preflight_report_marks_supported_pair_with_public_data():
    adapter = KrakenBrokerAdapter()

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XETHZUSD": {"altname": "ETHUSD", "wsname": "ETH/USD"},
                    "XXBTZUSD": {"altname": "XBTUSD", "wsname": "XBT/USD"},
                },
            }
        raise AssertionError(path)

    report = adapter.build_public_preflight_report("ETH-USD", fetch_json=fake_fetch_json).to_dict()

    assert report["artifact_type"] == "quantlab.kraken.preflight"
    assert report["public_api_reachable"] is True
    assert report["pair_supported"] is True
    assert report["normalized_symbol"] == "ETH/USD"
    assert report["matched_pair_key"] == "XETHZUSD"
    assert report["matched_pair_wsname"] == "ETH/USD"
    assert report["errors"] == []


def test_preflight_report_supports_btc_alias_mapping():
    adapter = KrakenBrokerAdapter()

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XXBTZUSD": {"altname": "XBTUSD", "wsname": "XBT/USD"},
                },
            }
        raise AssertionError(path)

    report = adapter.build_public_preflight_report("BTC-USD", fetch_json=fake_fetch_json).to_dict()

    assert report["normalized_symbol"] == "XBT/USD"
    assert report["pair_supported"] is True
    assert report["matched_pair_wsname"] == "XBT/USD"


def test_preflight_report_marks_unsupported_pair_cleanly():
    adapter = KrakenBrokerAdapter()

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XETHZUSD": {"altname": "ETHUSD", "wsname": "ETH/USD"},
                },
            }
        raise AssertionError(path)

    report = adapter.build_public_preflight_report("SOL-USD", fetch_json=fake_fetch_json).to_dict()

    assert report["public_api_reachable"] is True
    assert report["pair_supported"] is False
    assert "pair_not_supported" in report["errors"]
