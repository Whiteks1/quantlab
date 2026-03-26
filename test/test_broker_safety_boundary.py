from __future__ import annotations

from quantlab.brokers.boundary import (
    ExecutionContext,
    ExecutionIntent,
    ExecutionPolicy,
    validate_execution_intent,
)


def _make_intent(**overrides) -> ExecutionIntent:
    payload = {
        "broker_target": "kraken",
        "symbol": "ETH/USD",
        "side": "buy",
        "quantity": 0.25,
        "notional": 500.0,
        "account_id": "acct_demo",
        "strategy_id": "rsi_ma_cross_v2",
        "request_id": "req_d0_001",
        "dry_run": True,
    }
    payload.update(overrides)
    return ExecutionIntent(**payload)


def test_allows_safe_execution_intent():
    policy = ExecutionPolicy(
        kill_switch_active=False,
        max_notional_per_order=1000.0,
        allowed_symbols=frozenset({"ETH/USD", "BTC/USD"}),
        require_account_id=True,
    )

    result = validate_execution_intent(_make_intent(), policy)

    assert result.allowed is True
    assert result.reasons == ()


def test_rejects_when_kill_switch_is_active():
    result = validate_execution_intent(
        _make_intent(),
        ExecutionPolicy(kill_switch_active=True),
    )

    assert result.allowed is False
    assert "kill_switch_active" in result.reasons


def test_rejects_when_order_notional_exceeds_policy():
    result = validate_execution_intent(
        _make_intent(notional=1500.0),
        ExecutionPolicy(max_notional_per_order=1000.0),
    )

    assert result.allowed is False
    assert "max_notional_exceeded" in result.reasons


def test_rejects_symbol_outside_allowed_universe():
    result = validate_execution_intent(
        _make_intent(symbol="SOL/USD"),
        ExecutionPolicy(allowed_symbols=frozenset({"ETH/USD"})),
    )

    assert result.allowed is False
    assert "symbol_not_allowed" in result.reasons


def test_rejects_missing_account_id_when_required():
    result = validate_execution_intent(
        _make_intent(account_id=None),
        ExecutionPolicy(require_account_id=True),
    )

    assert result.allowed is False
    assert "missing_account_id" in result.reasons


def test_accumulates_multiple_rejection_reasons():
    result = validate_execution_intent(
        _make_intent(symbol="SOL/USD", side="hold", quantity=0.0, notional=-10.0, account_id=None),
        ExecutionPolicy(
            kill_switch_active=True,
            max_notional_per_order=1000.0,
            allowed_symbols=frozenset({"ETH/USD"}),
            require_account_id=True,
        ),
    )

    assert result.allowed is False
    assert set(result.reasons) == {
        "kill_switch_active",
        "missing_account_id",
        "non_positive_quantity",
        "non_positive_notional",
        "symbol_not_allowed",
        "unsupported_side",
    }


def test_execution_context_defaults_to_direct_account_rest_agnostic_shape():
    context = ExecutionContext()

    assert context.execution_account_id is None
    assert context.signer_id is None
    assert context.signer_type == "direct"
    assert context.routing_target == "account"
    assert context.transport_preference == "either"
    assert context.expires_after is None


def test_execution_context_can_model_hyperliquid_style_signer_and_routing():
    context = ExecutionContext(
        execution_account_id="0xsubaccount",
        signer_id="0xagentwallet",
        signer_type="agent_wallet",
        routing_target="subaccount",
        transport_preference="websocket",
        expires_after=1710000000000,
    )

    assert context.execution_account_id == "0xsubaccount"
    assert context.signer_id == "0xagentwallet"
    assert context.signer_type == "agent_wallet"
    assert context.routing_target == "subaccount"
    assert context.transport_preference == "websocket"
    assert context.expires_after == 1710000000000
