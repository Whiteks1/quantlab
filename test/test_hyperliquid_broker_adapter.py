from __future__ import annotations

from quantlab.brokers import ExecutionContext, ExecutionIntent, ExecutionPolicy
from quantlab.brokers.hyperliquid import HyperliquidBrokerAdapter


def _make_intent(**overrides) -> ExecutionIntent:
    payload = {
        "broker_target": "hyperliquid",
        "symbol": "ETH",
        "side": "buy",
        "quantity": 0.25,
        "notional": 500.0,
        "account_id": "0x1111111111111111111111111111111111111111",
        "strategy_id": "trend_following_v1",
        "request_id": "req_hl_001",
        "dry_run": True,
    }
    payload.update(overrides)
    return ExecutionIntent(**payload)


def test_resolves_hyperliquid_execution_context_for_agent_wallet_subaccount():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "agent"}
        raise AssertionError(payload)

    resolved = adapter.resolve_execution_context(
        intent_account_id=None,
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert resolved["context_ready"] is True
    assert resolved["query_user"] == "0x1111111111111111111111111111111111111111"
    assert resolved["nonce_scope"] == "0x2222222222222222222222222222222222222222"
    assert resolved["resolved_transport"] == "websocket"
    assert resolved["execution_account_role"] == "subAccount"
    assert resolved["signer_role"] == "agent"


def test_hyperliquid_perp_preflight_matches_meta_and_all_mids():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1", "@107": "15.2"}
        if payload["type"] == "meta":
            return {
                "universe": [
                    {"name": "BTC", "szDecimals": 5},
                    {"name": "ETH", "szDecimals": 4},
                ]
            }
        raise AssertionError(payload)

    report = adapter.build_public_preflight_report("eth", fetch_json=fake_fetch_json).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.preflight"
    assert report["public_api_reachable"] is True
    assert report["market_supported"] is True
    assert report["market_type"] == "perp"
    assert report["resolved_coin"] == "ETH"
    assert report["resolved_asset"] == 1
    assert report["mid_price"] == "2450.1"


def test_hyperliquid_spot_preflight_resolves_btc_alias_to_ubtc():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"@142": "69157.5"}
        if payload["type"] == "spotMeta":
            return {
                "universe": [
                    {"name": "PURR/USDC", "index": 0, "isCanonical": True},
                    {"name": "UBTC/USDC", "index": 142, "isCanonical": True},
                ]
            }
        raise AssertionError(payload)

    report = adapter.build_public_preflight_report("BTC-USDC", fetch_json=fake_fetch_json).to_dict()

    assert report["normalized_symbol"] == "BTC/USDC"
    assert report["market_type"] == "spot"
    assert report["market_supported"] is True
    assert report["matched_name"] == "UBTC/USDC"
    assert report["resolved_coin"] == "@142"
    assert report["resolved_asset"] == 10142
    assert report["mid_price"] == "69157.5"


def test_hyperliquid_preflight_reports_invalid_context_inputs_cleanly():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="acct_demo",
        signer_id="agent_demo",
        signer_type="agent_wallet",
        routing_target="vault",
        transport_preference="websocket",
        expires_after=0,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        raise AssertionError(payload)

    report = adapter.build_public_preflight_report(
        "ETH",
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["market_supported"] is True
    assert report["execution_context"]["context_ready"] is False
    assert "invalid_execution_account_id" in report["execution_context"]["reasons"]
    assert "invalid_signer_id" in report["execution_context"]["reasons"]
    assert "non_positive_expires_after" in report["execution_context"]["reasons"]


def test_hyperliquid_preflight_can_pressure_shared_boundary_with_context():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
    )

    result = adapter.preflight(_make_intent(), policy, context=context)
    payload = adapter.build_order_payload(_make_intent(symbol="ETH"), context=context)

    assert result.allowed is True
    assert payload["asset"] == "ETH"
    assert payload["execution_context"]["resolved_transport"] == "websocket"
