from __future__ import annotations

from quantlab.pretrade.models import PretradePlan


def plan_to_dict(plan: PretradePlan) -> dict[str, object]:
    request = plan.request
    return {
        "machine_contract": {
            "contract_type": plan.contract_type,
            "schema_version": "1.0",
        },
        "generated_at": plan.generated_at,
        "session_id": plan.session_id,
        "request": {
            "symbol": request.symbol,
            "venue": request.venue,
            "side": request.side,
            "capital": request.capital,
            "risk_percent": request.risk_percent,
            "entry_price": request.entry_price,
            "stop_price": request.stop_price,
            "target_price": request.target_price,
            "estimated_fees": request.estimated_fees,
            "estimated_slippage": request.estimated_slippage,
            "account_id": request.account_id,
            "strategy_id": request.strategy_id,
            "notes": request.notes,
        },
        "plan": {
            "risk_amount": plan.risk_amount,
            "stop_distance": plan.stop_distance,
            "target_distance": plan.target_distance,
            "position_size": plan.position_size,
            "notional": plan.notional,
            "gross_loss_at_stop": plan.gross_loss_at_stop,
            "max_loss_at_stop": plan.max_loss_at_stop,
            "gross_profit_at_target": plan.gross_profit_at_target,
            "net_profit_at_target": plan.net_profit_at_target,
            "risk_reward_ratio": plan.risk_reward_ratio,
            "total_cost_estimate": plan.total_cost_estimate,
        },
        "policy_checks": {
            "accepted": plan.validation.accepted,
            "reasons": list(plan.validation.reasons),
        },
    }


def summary_to_dict(plan: PretradePlan) -> dict[str, object]:
    return {
        "machine_contract": {
            "contract_type": "quantlab.pretrade.summary",
            "schema_version": "1.0",
        },
        "generated_at": plan.generated_at,
        "session_id": plan.session_id,
        "symbol": plan.request.symbol,
        "venue": plan.request.venue,
        "side": plan.request.side,
        "accepted": plan.validation.accepted,
        "risk_amount": plan.risk_amount,
        "position_size": plan.position_size,
        "notional": plan.notional,
        "max_loss_at_stop": plan.max_loss_at_stop,
        "net_profit_at_target": plan.net_profit_at_target,
        "risk_reward_ratio": plan.risk_reward_ratio,
    }


def markdown_summary(plan: PretradePlan) -> str:
    target_price = (
        f"{plan.request.target_price:.6f}"
        if plan.request.target_price is not None
        else "n/a"
    )
    rr_ratio = (
        f"{plan.risk_reward_ratio:.4f}"
        if plan.risk_reward_ratio is not None
        else "n/a"
    )
    target_profit = (
        f"{plan.net_profit_at_target:.6f}"
        if plan.net_profit_at_target is not None
        else "n/a"
    )
    return "\n".join(
        [
            "# QuantLab Pre-Trade Plan",
            "",
            f"- session_id: `{plan.session_id}`",
            f"- generated_at: `{plan.generated_at}`",
            f"- symbol: `{plan.request.symbol}`",
            f"- venue: `{plan.request.venue}`",
            f"- side: `{plan.request.side}`",
            f"- capital: `{plan.request.capital:.6f}`",
            f"- risk_percent: `{plan.request.risk_percent:.6f}`",
            f"- entry_price: `{plan.request.entry_price:.6f}`",
            f"- stop_price: `{plan.request.stop_price:.6f}`",
            f"- target_price: `{target_price}`",
            f"- position_size: `{plan.position_size:.6f}`",
            f"- notional: `{plan.notional:.6f}`",
            f"- max_loss_at_stop: `{plan.max_loss_at_stop:.6f}`",
            f"- net_profit_at_target: `{target_profit}`",
            f"- risk_reward_ratio: `{rr_ratio}`",
            f"- policy_accepted: `{str(plan.validation.accepted).lower()}`",
        ]
    ) + "\n"
