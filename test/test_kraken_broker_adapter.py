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


def test_authenticated_preflight_reports_missing_credentials_cleanly(monkeypatch):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)
    adapter = KrakenBrokerAdapter()

    report = adapter.build_authenticated_preflight_report().to_dict()

    assert report["credentials_present"] is False
    assert report["authenticated"] is False
    assert "missing_api_key" in report["errors"]
    assert "missing_api_secret" in report["errors"]


def test_authenticated_preflight_extracts_key_info_from_mocked_response():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        assert path == "/0/private/GetAPIKeyInfo"
        return {
            "error": [],
            "result": {
                "name": "quantlab-demo",
                "permissions": {"orders": "read", "funds": "none"},
                "restrictions": {"ip": ["127.0.0.1"]},
                "created": "2026-03-25T12:00:00Z",
                "updated": "2026-03-25T13:00:00Z",
            },
        }

    report = adapter.build_authenticated_preflight_report(
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.kraken.auth_preflight"
    assert report["credentials_present"] is True
    assert report["authenticated"] is True
    assert report["key_name"] == "quantlab-demo"
    assert report["permissions"]["orders"] == "read"
    assert report["restrictions"]["ip"] == ["127.0.0.1"]


def test_authenticated_preflight_reports_probe_failure():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        raise RuntimeError("boom")

    report = adapter.build_authenticated_preflight_report(
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["credentials_present"] is True
    assert report["authenticated"] is False
    assert "auth_probe_failed:RuntimeError" in report["errors"]


def test_authenticated_preflight_reports_api_errors():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        return {"error": ["EGeneral:Permission denied"], "result": {}}

    report = adapter.build_authenticated_preflight_report(
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["credentials_present"] is True
    assert report["authenticated"] is False
    assert "EGeneral:Permission denied" in report["errors"]


def test_account_snapshot_reports_missing_credentials_cleanly(monkeypatch):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)

    report = adapter.build_account_snapshot_report(_make_intent(), policy).to_dict()

    assert report["artifact_type"] == "quantlab.kraken.account_snapshot"
    assert report["authenticated_preflight"]["authenticated"] is False
    assert report["account_snapshot_available"] is False
    assert report["intent_readiness"]["allowed"] is False
    assert "private_auth_not_ready" in report["intent_readiness"]["reasons"]


def test_account_snapshot_marks_buy_intent_fundable_with_sufficient_quote_balance():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XETHZUSD": {
                        "altname": "ETHUSD",
                        "wsname": "ETH/USD",
                        "base": "XETH",
                        "quote": "ZUSD",
                        "ordermin": "0.001",
                        "costmin": "0.5",
                        "tick_size": "0.01",
                        "status": "online",
                    }
                },
            }
        raise AssertionError(path)

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {"error": [], "result": {"name": "quantlab-demo", "permissions": {"funds": "query"}}}
        if path == "/0/private/BalanceEx":
            return {
                "error": [],
                "result": {
                    "ZUSD": {
                        "balance": "1200.0",
                        "credit": "0.0",
                        "credit_used": "0.0",
                        "hold_trade": "0.0",
                    }
                },
            }
        raise AssertionError(path)

    report = adapter.build_account_snapshot_report(
        _make_intent(symbol="ETH/USD", side="buy", notional=500.0, quantity=0.25),
        policy,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_json=fake_fetch_json,
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["account_snapshot_available"] is True
    assert report["intent_readiness"]["allowed"] is True
    assert report["intent_readiness"]["funding_asset"] == "ZUSD"
    assert report["intent_readiness"]["available_amount"] == 1200.0


def test_account_snapshot_marks_sell_intent_insufficient_when_base_balance_is_too_low():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XETHZUSD": {
                        "altname": "ETHUSD",
                        "wsname": "ETH/USD",
                        "base": "XETH",
                        "quote": "ZUSD",
                        "ordermin": "0.001",
                        "costmin": "0.5",
                        "tick_size": "0.01",
                        "status": "online",
                    }
                },
            }
        raise AssertionError(path)

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {"error": [], "result": {"name": "quantlab-demo", "permissions": {"funds": "query"}}}
        if path == "/0/private/BalanceEx":
            return {
                "error": [],
                "result": {
                    "XETH": {
                        "balance": "0.10",
                        "credit": "0.0",
                        "credit_used": "0.0",
                        "hold_trade": "0.0",
                    }
                },
            }
        raise AssertionError(path)

    report = adapter.build_account_snapshot_report(
        _make_intent(symbol="ETH/USD", side="sell", quantity=0.25, notional=500.0),
        policy,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_json=fake_fetch_json,
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["intent_readiness"]["allowed"] is False
    assert report["intent_readiness"]["funding_asset"] == "XETH"
    assert "insufficient_available_balance" in report["intent_readiness"]["reasons"]


def test_account_snapshot_respects_pair_minimums():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    def fake_fetch_json(path, **kwargs):
        if path == "/Time":
            return {"error": [], "result": {"unixtime": 1700000000, "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT"}}
        if path == "/AssetPairs":
            return {
                "error": [],
                "result": {
                    "XETHZUSD": {
                        "altname": "ETHUSD",
                        "wsname": "ETH/USD",
                        "base": "XETH",
                        "quote": "ZUSD",
                        "ordermin": "0.5",
                        "costmin": "100.0",
                        "tick_size": "0.01",
                        "status": "online",
                    }
                },
            }
        raise AssertionError(path)

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {"error": [], "result": {"name": "quantlab-demo", "permissions": {"funds": "query"}}}
        if path == "/0/private/BalanceEx":
            return {
                "error": [],
                "result": {
                    "ZUSD": {
                        "balance": "1200.0",
                        "credit": "0.0",
                        "credit_used": "0.0",
                        "hold_trade": "0.0",
                    }
                },
            }
        raise AssertionError(path)

    report = adapter.build_account_snapshot_report(
        _make_intent(symbol="ETH/USD", side="buy", quantity=0.25, notional=50.0),
        policy,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_json=fake_fetch_json,
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["intent_readiness"]["allowed"] is False
    assert "below_pair_costmin" in report["intent_readiness"]["reasons"]


def test_order_validate_reports_local_preflight_rejection_without_remote_call():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=100.0)

    report = adapter.build_order_validate_report(
        _make_intent(notional=500.0),
        policy,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.kraken.order_validate"
    assert report["remote_validation_called"] is False
    assert report["validation_accepted"] is False
    assert "max_notional_exceeded" in report["validation_reasons"]
    assert "local_preflight_rejected" in report["errors"]


def test_order_validate_accepts_successful_mocked_exchange_validation():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "create_modify"},
                },
            }
        if path == "/0/private/AddOrder":
            assert kwargs["payload"]["validate"] == "true"
            return {
                "error": [],
                "result": {
                    "descr": {"order": "buy 0.25 ETHUSD @ market"},
                },
            }
        raise AssertionError(path)

    report = adapter.build_order_validate_report(
        _make_intent(symbol="ETH/USD", side="buy", quantity=0.25, notional=500.0),
        policy,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["remote_validation_called"] is True
    assert report["validation_accepted"] is True
    assert report["validate_payload"]["validate"] == "true"
    assert report["exchange_response"]["result"]["descr"]["order"] == "buy 0.25 ETHUSD @ market"


def test_order_validate_reports_exchange_side_validation_errors():
    adapter = KrakenBrokerAdapter()
    policy = ExecutionPolicy(
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD"}),
        require_account_id=True,
    )

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "create_modify"},
                },
            }
        if path == "/0/private/AddOrder":
            return {
                "error": ["EOrder:Insufficient funds"],
                "result": {},
            }
        raise AssertionError(path)

    report = adapter.build_order_validate_report(
        _make_intent(symbol="ETH/USD", side="buy", quantity=0.25, notional=500.0),
        policy,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["remote_validation_called"] is True
    assert report["validation_accepted"] is False
    assert "EOrder:Insufficient funds" in report["validation_reasons"]
    assert "EOrder:Insufficient funds" in report["errors"]


def test_order_submit_builds_real_payload_without_validate_and_with_stable_userref():
    adapter = KrakenBrokerAdapter()

    payload = adapter.build_submit_payload(
        {
            "pair": "ETH/USD",
            "type": "buy",
            "ordertype": "market",
            "volume": "0.25",
            "validate": "true",
        },
        session_id="validate_001",
    )

    assert payload["pair"] == "ETH/USD"
    assert payload["type"] == "buy"
    assert payload["ordertype"] == "market"
    assert payload["volume"] == "0.25"
    assert "validate" not in payload
    assert payload["userref"].isdigit()


def test_order_submit_reports_missing_credentials_without_remote_call(monkeypatch):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)
    adapter = KrakenBrokerAdapter()

    report = adapter.build_order_submit_report(
        source_session_id="validate_001",
        validate_payload={"pair": "ETH/USD", "type": "buy", "ordertype": "market", "volume": "0.25"},
    ).to_dict()

    assert report["submitted"] is False
    assert report["remote_submit_called"] is False
    assert "missing_api_key" in report["errors"]
    assert "missing_api_secret" in report["errors"]
    assert "private_auth_not_ready" in report["errors"]


def test_order_submit_can_prepare_pending_remote_submit_without_hitting_exchange():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "create_modify"},
                },
            }
        raise AssertionError(path)

    report = adapter.build_order_submit_report(
        source_session_id="validate_001",
        validate_payload={"pair": "ETH/USD", "type": "buy", "ordertype": "market", "volume": "0.25"},
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
        remote_submit=False,
    ).to_dict()

    assert report["submit_state"] == "pending_remote_submit"
    assert report["remote_submit_called"] is False
    assert report["submitted"] is False
    assert report["userref"] is not None


def test_order_submit_accepts_successful_mocked_exchange_submit():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "create_modify"},
                },
            }
        if path == "/0/private/AddOrder":
            assert kwargs["payload"]["userref"].isdigit()
            assert "validate" not in kwargs["payload"]
            return {
                "error": [],
                "result": {
                    "descr": {"order": "buy 0.25 ETHUSD @ market"},
                    "txid": ["OABC-123-XYZ"],
                },
            }
        raise AssertionError(path)

    report = adapter.build_order_submit_report(
        source_session_id="validate_001",
        validate_payload={"pair": "ETH/USD", "type": "buy", "ordertype": "market", "volume": "0.25"},
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["remote_submit_called"] is True
    assert report["submitted"] is True
    assert report["txid"] == ["OABC-123-XYZ"]


def test_order_submit_reports_exchange_side_submit_errors():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "create_modify"},
                },
            }
        if path == "/0/private/AddOrder":
            return {
                "error": ["EOrder:Rate limit exceeded"],
                "result": {},
            }
        raise AssertionError(path)

    report = adapter.build_order_submit_report(
        source_session_id="validate_001",
        validate_payload={"pair": "ETH/USD", "type": "buy", "ordertype": "market", "volume": "0.25"},
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["remote_submit_called"] is True
    assert report["submitted"] is False
    assert "EOrder:Rate limit exceeded" in report["errors"]


def test_order_reconciliation_matches_orders_by_userref():
    adapter = KrakenBrokerAdapter()

    def fake_private_json(path, **kwargs):
        if path == "/0/private/GetAPIKeyInfo":
            return {
                "error": [],
                "result": {
                    "name": "quantlab-demo",
                    "permissions": {"orders": "query"},
                },
            }
        if path == "/0/private/OpenOrders":
            return {"error": [], "result": {"open": {}}}
        if path == "/0/private/ClosedOrders":
            return {
                "error": [],
                "result": {
                    "closed": {
                        "OABC-123-XYZ": {
                            "userref": 123456,
                            "status": "closed",
                            "descr": {"order": "buy 0.25 ETHUSD @ market"},
                        }
                    }
                },
            }
        raise AssertionError(path)

    report = adapter.build_order_reconciliation_report(
        source_session_id="validate_001",
        userref=123456,
        api_key="demo-key",
        api_secret="ZGVtby1zZWNyZXQ=",
        fetch_private_json=fake_private_json,
    ).to_dict()

    assert report["reconciliation_attempted"] is True
    assert report["matched"] is True
    assert report["matched_sources"] == ["closed"]
    assert report["matched_txid"] == ["OABC-123-XYZ"]


def test_order_reconciliation_reports_missing_credentials_cleanly(monkeypatch):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)
    adapter = KrakenBrokerAdapter()

    report = adapter.build_order_reconciliation_report(
        source_session_id="validate_001",
        userref=123456,
    ).to_dict()

    assert report["reconciliation_attempted"] is False
    assert report["matched"] is False
    assert "missing_api_key" in report["errors"]
    assert "missing_api_secret" in report["errors"]
