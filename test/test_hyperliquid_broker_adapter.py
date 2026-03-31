from __future__ import annotations

from quantlab.brokers import ExecutionContext, ExecutionIntent, ExecutionPolicy
from quantlab.brokers.hyperliquid import (
    HyperliquidBrokerAdapter,
    recover_hyperliquid_l1_action_signer,
)


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


def _extract_cloid(signed_action: dict[str, object]) -> str | None:
    action_payload = signed_action.get("action_payload")
    if not isinstance(action_payload, dict):
        return None
    orders = action_payload.get("orders")
    if not isinstance(orders, list) or not orders:
        return None
    first_order = orders[0]
    if not isinstance(first_order, dict):
        return None
    value = first_order.get("c")
    return str(value) if value is not None else None


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


def test_hyperliquid_account_readiness_marks_agent_subaccount_setup_ready():
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
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.account_readiness"
    assert report["readiness_allowed"] is True
    assert report["account_visibility_available"] is True
    assert report["open_orders_count"] == 0
    assert report["execution_context"]["signer_role"] == "agent"


def test_hyperliquid_account_readiness_rejects_agent_wallet_without_execution_account():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="account",
        transport_preference="websocket",
    )

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=lambda payload, **kwargs: {"role": "agent"},
    ).to_dict()

    assert report["readiness_allowed"] is False
    assert "missing_execution_account_id" in report["readiness_reasons"]


def test_hyperliquid_account_readiness_allows_visible_account_route_when_role_is_missing():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_type="direct",
        routing_target="account",
        transport_preference="websocket",
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole":
            return {"role": "missing"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["account_visibility_available"] is True
    assert report["readiness_allowed"] is True
    assert "execution_account_missing" not in report["readiness_reasons"]


def test_hyperliquid_account_readiness_rejects_signer_role_mismatch():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "user"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["readiness_allowed"] is False
    assert "signer_role_mismatch" in report["readiness_reasons"]


def test_hyperliquid_account_readiness_still_rejects_signer_mismatch_when_account_route_is_visible():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="account",
        transport_preference="websocket",
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "missing"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "user"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["account_visibility_available"] is True
    assert report["readiness_allowed"] is False
    assert "execution_account_missing" not in report["readiness_reasons"]
    assert "signer_role_mismatch" in report["readiness_reasons"]


def test_hyperliquid_account_readiness_marks_missing_delegated_signer_role_unknown():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="account",
        transport_preference="websocket",
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "missing"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "missing"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["account_visibility_available"] is True
    assert report["readiness_allowed"] is False
    assert "signer_role_unknown" in report["readiness_reasons"]
    assert "signer_role_mismatch" not in report["readiness_reasons"]


def test_hyperliquid_account_readiness_reports_visibility_probe_failure():
    adapter = HyperliquidBrokerAdapter()
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_type="direct",
        routing_target="account",
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userRole":
            return {"role": "user"}
        if payload["type"] == "openOrders":
            raise RuntimeError("boom")
        raise AssertionError(payload)

    report = adapter.build_account_readiness_report(
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["readiness_allowed"] is False
    assert report["account_visibility_available"] is False
    assert "account_visibility_unavailable" in report["readiness_reasons"]
    assert "account_visibility_probe_failed:RuntimeError" in report["errors"]


def test_hyperliquid_signed_action_report_builds_deterministic_payload_and_envelope():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
        nonce_hint=1700000000000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "agent"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_signed_action_report(
        _make_intent(),
        policy,
        context=context,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.signed_action"
    assert report["readiness_allowed"] is True
    assert report["nonce"] == 1700000000000
    assert report["expires_after"] == 1700000060000
    assert report["expires_after_mode"] == "relative_ms"
    assert report["action_payload"]["type"] == "order"
    assert report["action_payload"]["orders"][0]["a"] == 0
    assert report["action_payload"]["orders"][0]["b"] is True
    assert report["signature_envelope"]["signature_present"] is False
    assert report["signature_envelope"]["signature_state"] == "pending_signer_backend"


def test_hyperliquid_signed_action_report_rejects_when_account_readiness_is_not_ready():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    context = ExecutionContext(
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="account",
        nonce_hint=1700000000000,
    )

    report = adapter.build_signed_action_report(
        _make_intent(account_id=None),
        policy,
        context=context,
        fetch_json=lambda payload, **kwargs: {"role": "agent"} if payload["type"] == "userRole" else [],
    ).to_dict()

    assert report["readiness_allowed"] is False
    assert report["action_payload"] is None
    assert "missing_execution_account_id" in report["readiness_reasons"]
    assert "action_payload_not_ready" in report["errors"]


def test_hyperliquid_signed_action_report_signs_with_local_private_key():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    signer_private_key = "0x59c6995e998f97a5a0044966f0945382d7f6f9d5c4bbf34c95a98e2ce42928f1"
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x4ad91849099DcD0E9e4b80214D8B4969a69f1861",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
        nonce_hint=1700000000000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x4ad91849099DcD0E9e4b80214D8B4969a69f1861":
            return {"role": "agent"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_signed_action_report(
        _make_intent(),
        policy,
        context=context,
        fetch_json=fake_fetch_json,
        signing_private_key=signer_private_key,
    ).to_dict()

    assert report["readiness_allowed"] is True
    assert report["signer_backend"] == "hyperliquid_local_private_key"
    assert report["signature_envelope"]["signature_state"] == "signed"
    assert report["signature_envelope"]["signature_present"] is True
    recovered = recover_hyperliquid_l1_action_signer(
        action_payload=report["action_payload"],
        signature=report["signature_envelope"]["signature"],
        vault_address=report["signature_envelope"]["signing_payload"]["vaultAddress"],
        nonce=report["nonce"],
        expires_after=report["expires_after"],
    )
    assert recovered.lower() == report["signature_envelope"]["derived_signer_address"].lower()
    assert recovered.lower() == context.signer_id.lower()


def test_hyperliquid_signed_action_report_flags_signer_identity_mismatch():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    signer_private_key = "0x59c6995e998f97a5a0044966f0945382d7f6f9d5c4bbf34c95a98e2ce42928f1"
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x2222222222222222222222222222222222222222",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
        nonce_hint=1700000000000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x2222222222222222222222222222222222222222":
            return {"role": "agent"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    report = adapter.build_signed_action_report(
        _make_intent(),
        policy,
        context=context,
        fetch_json=fake_fetch_json,
        signing_private_key=signer_private_key,
    ).to_dict()

    assert report["readiness_allowed"] is False
    assert "signer_identity_mismatch" in report["readiness_reasons"]
    assert "signer_identity_mismatch" in report["errors"]


def test_hyperliquid_reconciliation_report_prefers_known_order_status():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "orderStatus":
            return {
                "status": "order",
                "order": {
                    "order": {"origSz": "0.25", "sz": "0.0", "oid": 12345},
                    "status": "filled",
                },
            }
        if payload["type"] == "userFills":
            return [{"oid": 12345, "sz": "0.25", "px": "2450.1", "time": 1764000000000}]
        raise AssertionError(payload)

    report = adapter.build_reconciliation_report(
        source_session_id="hl_submit_demo_001",
        execution_account_id="0x1111111111111111111111111111111111111111",
        oid=12345,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["status_known"] is True
    assert report["normalized_state"] == "filled"
    assert report["close_state"] == "closed"
    assert report["fill_state"] == "filled"
    assert report["filled_size"] == "0.25"
    assert report["fill_count"] == 1
    assert report["resolution_source"] == "order_status"
    assert report["matched_open_order"] is None


def test_hyperliquid_reconciliation_report_falls_back_to_open_orders():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "orderStatus":
            return {"status": "missing"}
        if payload["type"] == "openOrders":
            return [{"oid": 12345, "coin": "ETH", "origSz": "0.25", "sz": "0.10"}]
        if payload["type"] == "frontendOpenOrders":
            return []
        if payload["type"] == "historicalOrders":
            return []
        if payload["type"] == "userFills":
            return [{"oid": 12345, "sz": "0.15", "px": "2451.0", "time": 1764000000100}]
        raise AssertionError(payload)

    report = adapter.build_reconciliation_report(
        source_session_id="hl_submit_demo_002",
        execution_account_id="0x1111111111111111111111111111111111111111",
        oid=12345,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["status_known"] is True
    assert report["normalized_state"] == "open"
    assert report["close_state"] == "open"
    assert report["fill_state"] == "partial"
    assert report["filled_size"] == "0.15"
    assert report["remaining_size"] == "0.1"
    assert report["resolution_source"] == "open_orders"
    assert report["matched_open_order"]["oid"] == 12345


def test_hyperliquid_reconciliation_report_uses_historical_orders_for_closed_partial():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "orderStatus":
            return {"status": "missing"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        if payload["type"] == "historicalOrders":
            return [
                {
                    "order": {"oid": 12345, "origSz": "0.25", "sz": "0.0", "cloid": "abc123cloid"},
                    "status": "canceled",
                }
            ]
        if payload["type"] == "userFills":
            return [{"oid": 12345, "sz": "0.10", "px": "2449.5", "time": 1764000000200}]
        raise AssertionError(payload)

    report = adapter.build_reconciliation_report(
        source_session_id="hl_submit_demo_003",
        execution_account_id="0x1111111111111111111111111111111111111111",
        oid=12345,
        cloid="abc123cloid",
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["status_known"] is True
    assert report["normalized_state"] == "canceled"
    assert report["close_state"] == "closed"
    assert report["fill_state"] == "partial"
    assert report["fill_count"] == 1
    assert report["matched_historical_order"]["status"] == "canceled"
    assert report["resolution_source"] == "historical_orders"


def test_hyperliquid_fill_summary_report_aggregates_fee_and_pnl():
    adapter = HyperliquidBrokerAdapter()
    signed_action = {
        "action_payload": {
            "orders": [{"s": "0.25", "c": "abc123cloid"}],
        }
    }

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userFills":
            return [
                {
                    "oid": 12345,
                    "sz": "0.10",
                    "px": "2450.0",
                    "fee": "0.2",
                    "builderFee": "0.05",
                    "closedPnl": "1.0",
                    "time": 1764000000000,
                },
                {
                    "oid": 12345,
                    "sz": "0.15",
                    "px": "2460.0",
                    "fee": "0.3",
                    "builderFee": "0.00",
                    "closedPnl": "2.0",
                    "time": 1764000001000,
                },
            ]
        raise AssertionError(payload)

    report = adapter.build_fill_summary_report(
        source_session_id="hl_submit_demo_004",
        execution_account_id="0x1111111111111111111111111111111111111111",
        oid=12345,
        cloid="abc123cloid",
        signed_action_artifact=signed_action,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["fills_known"] is True
    assert report["fill_state"] == "filled"
    assert report["fill_count"] == 2
    assert report["filled_size"] == "0.25"
    assert report["remaining_size"] == "0"
    assert report["average_fill_price"] == "2456"
    assert report["total_fee"] == "0.5"
    assert report["total_builder_fee"] == "0.05"
    assert report["total_closed_pnl"] == "3"
    assert report["first_fill_time"] == 1764000000000
    assert report["last_fill_time"] == 1764000001000


def test_hyperliquid_fill_summary_report_handles_no_fills():
    adapter = HyperliquidBrokerAdapter()
    signed_action = {
        "action_payload": {
            "orders": [{"s": "0.25", "c": "abc123cloid"}],
        }
    }

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "userFills":
            return []
        raise AssertionError(payload)

    report = adapter.build_fill_summary_report(
        source_session_id="hl_submit_demo_005",
        execution_account_id="0x1111111111111111111111111111111111111111",
        oid=12345,
        cloid="abc123cloid",
        signed_action_artifact=signed_action,
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["fills_known"] is True
    assert report["fill_state"] == "none"
    assert report["fill_count"] == 0
    assert report["filled_size"] is None
    assert report["remaining_size"] == "0.25"


def test_hyperliquid_submit_report_submits_signed_action():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    signer_private_key = "0x59c6995e998f97a5a0044966f0945382d7f6f9d5c4bbf34c95a98e2ce42928f1"
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x4ad91849099DcD0E9e4b80214D8B4969a69f1861",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
        nonce_hint=1700000000000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x4ad91849099DcD0E9e4b80214D8B4969a69f1861":
            return {"role": "agent"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    signed_action = adapter.build_signed_action_report(
        _make_intent(),
        policy,
        context=context,
        fetch_json=fake_fetch_json,
        signing_private_key=signer_private_key,
    ).to_dict()

    def fake_post_json(payload, **kwargs):
        assert payload["action"]["type"] == "order"
        assert payload["nonce"] == 1700000000000
        assert isinstance(payload["signature"], dict)
        assert payload["vaultAddress"] == "0x1111111111111111111111111111111111111111"
        return {
            "status": "ok",
            "response": {
                "type": "resting",
                "data": {"statuses": [{"resting": {"oid": 12345}}]},
            },
        }

    report = adapter.build_submit_report(
        source_artifact_path="C:/tmp/hyperliquid_signed_action.json",
        signed_action_artifact=signed_action,
        reviewer="marce",
        note="ready",
        post_json=fake_post_json,
        remote_submit=True,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.submit_response"
    assert report["submitted"] is True
    assert report["remote_submit_called"] is True
    assert report["submit_state"] == "submitted_remote"
    assert report["response_type"] == "resting"
    assert report["reviewer"] == "marce"


def test_hyperliquid_submit_report_rejects_unsigned_artifact():
    adapter = HyperliquidBrokerAdapter()
    unsigned_artifact = {
        "artifact_type": "quantlab.hyperliquid.signed_action",
        "readiness_allowed": True,
        "action_payload": {"type": "order", "orders": [], "grouping": "na"},
        "nonce": 1700000000000,
        "signature_envelope": {
            "signer_id": "0x1111111111111111111111111111111111111111",
            "signing_payload_sha256": "abc123",
            "signature_state": "pending_signer_backend",
            "signature_present": False,
            "signature": None,
        },
    }

    report = adapter.build_submit_report(
        source_artifact_path="C:/tmp/hyperliquid_signed_action.json",
        signed_action_artifact=unsigned_artifact,
        reviewer="marce",
        remote_submit=True,
    ).to_dict()

    assert report["submitted"] is False
    assert report["remote_submit_called"] is False
    assert report["submit_state"] == "signed_action_not_signed"
    assert "signed_action_not_signed" in report["errors"]


def test_hyperliquid_cancel_report_submits_signed_cancel():
    adapter = HyperliquidBrokerAdapter()
    policy = ExecutionPolicy(max_notional_per_order=1000.0)
    signer_private_key = "0x59c6995e998f97a5a0044966f0945382d7f6f9d5c4bbf34c95a98e2ce42928f1"
    context = ExecutionContext(
        execution_account_id="0x1111111111111111111111111111111111111111",
        signer_id="0x4ad91849099DcD0E9e4b80214D8B4969a69f1861",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=60000,
        nonce_hint=1700000000000,
    )

    def fake_fetch_json(payload, **kwargs):
        if payload["type"] == "allMids":
            return {"ETH": "2450.1"}
        if payload["type"] == "meta":
            return {"universe": [{"name": "ETH", "szDecimals": 4}]}
        if payload["type"] == "userRole" and payload["user"] == "0x1111111111111111111111111111111111111111":
            return {"role": "subAccount"}
        if payload["type"] == "userRole" and payload["user"] == "0x4ad91849099DcD0E9e4b80214D8B4969a69f1861":
            return {"role": "agent"}
        if payload["type"] == "openOrders":
            return []
        if payload["type"] == "frontendOpenOrders":
            return []
        raise AssertionError(payload)

    signed_action = adapter.build_signed_action_report(
        _make_intent(),
        policy,
        context=context,
        fetch_json=fake_fetch_json,
        signing_private_key=signer_private_key,
    ).to_dict()
    submit_response = {
        "artifact_type": "quantlab.hyperliquid.submit_response",
        "submit_state": "submitted_remote",
        "remote_submit_called": True,
        "submitted": True,
        "oid": 12345,
        "cloid": _extract_cloid(signed_action),
    }

    def fake_post_json(payload, **kwargs):
        assert payload["action"]["type"] == "cancel"
        assert payload["action"]["cancels"][0]["a"] == signed_action["action_payload"]["orders"][0]["a"]
        assert payload["action"]["cancels"][0]["o"] == 12345
        assert isinstance(payload["signature"], dict)
        assert payload["vaultAddress"] == "0x1111111111111111111111111111111111111111"
        return {"status": "ok", "response": {"data": {"statuses": [{"success": True}]}}}

    report = adapter.build_cancel_report(
        source_session_id="hl_submit_demo_003",
        signed_action_artifact=signed_action,
        submit_response_artifact=submit_response,
        reviewer="marce",
        note="cancel now",
        signing_private_key=signer_private_key,
        post_json=fake_post_json,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.cancel_response"
    assert report["cancel_accepted"] is True
    assert report["remote_cancel_called"] is True
    assert report["cancel_state"] == "canceled_remote"
    assert report["oid"] == 12345


def test_hyperliquid_cancel_report_rejects_missing_order_identifier():
    adapter = HyperliquidBrokerAdapter()
    signed_action = {
        "artifact_type": "quantlab.hyperliquid.signed_action",
        "readiness_allowed": True,
        "action_payload": {"type": "order", "orders": [{"a": 1}], "grouping": "na"},
        "signature_envelope": {
            "signature_state": "signed",
            "signature_present": True,
            "signer_id": "0x1111111111111111111111111111111111111111",
            "signing_payload_sha256": "abc123",
            "signing_payload": {"vaultAddress": "0x1111111111111111111111111111111111111111"},
        },
    }
    submit_response = {
        "artifact_type": "quantlab.hyperliquid.submit_response",
        "submit_state": "submitted_remote",
        "remote_submit_called": True,
        "submitted": True,
    }

    report = adapter.build_cancel_report(
        source_session_id="hl_submit_demo_004",
        signed_action_artifact=signed_action,
        submit_response_artifact=submit_response,
        reviewer="marce",
        signing_private_key="0x59c6995e998f97a5a0044966f0945382d7f6f9d5c4bbf34c95a98e2ce42928f1",
        remote_cancel=True,
    ).to_dict()

    assert report["cancel_accepted"] is False
    assert report["remote_cancel_called"] is False
    assert report["cancel_state"] == "missing_order_identifier"
    assert "missing_order_identifier" in report["errors"]


def test_hyperliquid_order_status_report_tracks_open_order_by_cloid():
    adapter = HyperliquidBrokerAdapter()

    def fake_fetch_json(payload, **kwargs):
        assert payload["type"] == "orderStatus"
        assert payload["user"] == "0x1111111111111111111111111111111111111111"
        assert payload["oid"] == "abc123cloid"
        return {
            "status": "order",
            "order": {
                "status": "open",
                "order": {"oid": 12345, "cloid": "abc123cloid"},
            },
        }

    report = adapter.build_order_status_report(
        source_session_id="hl_submit_demo",
        execution_account_id="0x1111111111111111111111111111111111111111",
        cloid="abc123cloid",
        fetch_json=fake_fetch_json,
    ).to_dict()

    assert report["artifact_type"] == "quantlab.hyperliquid.order_status"
    assert report["query_attempted"] is True
    assert report["status_known"] is True
    assert report["raw_status"] == "open"
    assert report["normalized_state"] == "open"
    assert report["query_mode"] == "cloid"
    assert report["query_identifier"] == "abc123cloid"


def test_hyperliquid_order_status_report_requires_query_identifier():
    adapter = HyperliquidBrokerAdapter()

    report = adapter.build_order_status_report(
        source_session_id="hl_submit_demo",
        execution_account_id="0x1111111111111111111111111111111111111111",
    ).to_dict()

    assert report["query_attempted"] is False
    assert report["status_known"] is False
    assert report["normalized_state"] is None
    assert "missing_order_identifier" in report["errors"]
