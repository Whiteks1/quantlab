from __future__ import annotations

from dataclasses import dataclass

from quantlab.brokers.boundary import (
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)
from quantlab.pretrade.models import PretradePlan


@dataclass(frozen=True)
class PretradeExecutionBridge:
    source_session_id: str
    draft_execution_intent: ExecutionIntent
    execution_policy: ExecutionPolicy
    execution_preflight: ExecutionPreflight


def build_execution_policy(
    *,
    kill_switch_active: bool = False,
    max_notional_per_order: float | None = None,
    allowed_symbols: frozenset[str] | None = None,
    require_account_id: bool = True,
) -> ExecutionPolicy:
    return ExecutionPolicy(
        kill_switch_active=kill_switch_active,
        max_notional_per_order=max_notional_per_order,
        allowed_symbols=allowed_symbols or frozenset(),
        require_account_id=require_account_id,
    )


def build_pretrade_execution_bridge(
    plan: PretradePlan,
    *,
    broker_target: str,
    policy: ExecutionPolicy,
    request_id: str | None = None,
) -> PretradeExecutionBridge:
    intent = ExecutionIntent(
        broker_target=broker_target,
        symbol=plan.request.symbol,
        side=plan.request.side,
        quantity=plan.position_size,
        notional=plan.notional,
        account_id=plan.request.account_id,
        strategy_id=plan.request.strategy_id,
        request_id=request_id or plan.session_id,
        dry_run=True,
    )
    preflight = validate_execution_intent(intent, policy)
    return PretradeExecutionBridge(
        source_session_id=plan.session_id,
        draft_execution_intent=intent,
        execution_policy=policy,
        execution_preflight=preflight,
    )


def bridge_to_dict(bridge: PretradeExecutionBridge) -> dict[str, object]:
    return {
        "machine_contract": {
            "contract_type": "quantlab.pretrade.execution_bridge",
            "schema_version": "1.0",
        },
        "source_session_id": bridge.source_session_id,
        "draft_execution_intent": {
            "broker_target": bridge.draft_execution_intent.broker_target,
            "symbol": bridge.draft_execution_intent.symbol,
            "side": bridge.draft_execution_intent.side,
            "quantity": bridge.draft_execution_intent.quantity,
            "notional": bridge.draft_execution_intent.notional,
            "account_id": bridge.draft_execution_intent.account_id,
            "strategy_id": bridge.draft_execution_intent.strategy_id,
            "request_id": bridge.draft_execution_intent.request_id,
            "dry_run": bridge.draft_execution_intent.dry_run,
        },
        "execution_policy": {
            "kill_switch_active": bridge.execution_policy.kill_switch_active,
            "max_notional_per_order": bridge.execution_policy.max_notional_per_order,
            "allowed_symbols": sorted(bridge.execution_policy.allowed_symbols),
            "require_account_id": bridge.execution_policy.require_account_id,
        },
        "execution_preflight": {
            "allowed": bridge.execution_preflight.allowed,
            "reasons": list(bridge.execution_preflight.reasons),
        },
    }
