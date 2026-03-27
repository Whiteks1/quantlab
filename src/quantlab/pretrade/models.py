from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


PretradeSide = Literal["buy", "sell"]


@dataclass(frozen=True)
class PretradeRequest:
    symbol: str
    venue: str
    side: PretradeSide
    capital: float
    risk_percent: float
    entry_price: float
    stop_price: float
    target_price: float | None = None
    estimated_fees: float = 0.0
    estimated_slippage: float = 0.0
    account_id: str | None = None
    strategy_id: str | None = None
    notes: str | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class PretradeValidation:
    accepted: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class PretradePlan:
    session_id: str
    request: PretradeRequest
    validation: PretradeValidation
    risk_amount: float
    stop_distance: float
    target_distance: float | None
    position_size: float
    notional: float
    gross_loss_at_stop: float
    max_loss_at_stop: float
    gross_profit_at_target: float | None
    net_profit_at_target: float | None
    risk_reward_ratio: float | None
    total_cost_estimate: float
    generated_at: str
    contract_type: str = field(default="quantlab.pretrade.plan")
