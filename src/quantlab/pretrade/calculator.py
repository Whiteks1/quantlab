from __future__ import annotations

from datetime import datetime

from quantlab.pretrade.models import PretradePlan, PretradeRequest
from quantlab.pretrade.policy_checks import require_valid_pretrade_request


def build_pretrade_plan(
    request: PretradeRequest,
    *,
    generated_at: datetime | None = None,
) -> PretradePlan:
    validation = require_valid_pretrade_request(request)
    created_at = (generated_at or datetime.now()).replace(microsecond=0).isoformat()

    risk_amount = request.capital * (request.risk_percent / 100.0)
    stop_distance = abs(request.entry_price - request.stop_price)
    target_distance = (
        abs(request.target_price - request.entry_price)
        if request.target_price is not None
        else None
    )
    total_cost_estimate = request.estimated_fees + request.estimated_slippage
    position_size = risk_amount / stop_distance
    notional = position_size * request.entry_price
    gross_loss_at_stop = position_size * stop_distance
    max_loss_at_stop = gross_loss_at_stop + total_cost_estimate

    gross_profit_at_target = (
        position_size * target_distance if target_distance is not None else None
    )
    net_profit_at_target = (
        gross_profit_at_target - total_cost_estimate
        if gross_profit_at_target is not None
        else None
    )
    risk_reward_ratio = (
        net_profit_at_target / max_loss_at_stop
        if net_profit_at_target is not None and max_loss_at_stop > 0
        else None
    )
    session_id = request.session_id or _default_session_id(created_at)

    return PretradePlan(
        session_id=session_id,
        request=request,
        validation=validation,
        risk_amount=risk_amount,
        stop_distance=stop_distance,
        target_distance=target_distance,
        position_size=position_size,
        notional=notional,
        gross_loss_at_stop=gross_loss_at_stop,
        max_loss_at_stop=max_loss_at_stop,
        gross_profit_at_target=gross_profit_at_target,
        net_profit_at_target=net_profit_at_target,
        risk_reward_ratio=risk_reward_ratio,
        total_cost_estimate=total_cost_estimate,
        generated_at=created_at,
    )


def _default_session_id(created_at: str) -> str:
    compact = created_at.replace("-", "").replace(":", "").replace("T", "_")
    return f"{compact}_pretrade"
