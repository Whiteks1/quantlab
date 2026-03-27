from __future__ import annotations

from quantlab.errors import ConfigError
from quantlab.pretrade.models import PretradeRequest, PretradeValidation


def normalize_side(side: str) -> str:
    normalized = str(side or "").strip().lower()
    aliases = {
        "buy": "buy",
        "long": "buy",
        "sell": "sell",
        "short": "sell",
    }
    if normalized not in aliases:
        raise ConfigError("pretrade_side must be one of: buy, sell, long, short.")
    return aliases[normalized]


def validate_pretrade_request(request: PretradeRequest) -> PretradeValidation:
    reasons: list[str] = []

    if not request.symbol.strip():
        reasons.append("missing_symbol")
    if not request.venue.strip():
        reasons.append("missing_venue")
    if request.capital <= 0:
        reasons.append("non_positive_capital")
    if request.risk_percent <= 0 or request.risk_percent > 100:
        reasons.append("risk_percent_out_of_bounds")
    if request.entry_price <= 0:
        reasons.append("non_positive_entry_price")
    if request.stop_price <= 0:
        reasons.append("non_positive_stop_price")
    if request.target_price is not None and request.target_price <= 0:
        reasons.append("non_positive_target_price")
    if request.estimated_fees < 0:
        reasons.append("negative_estimated_fees")
    if request.estimated_slippage < 0:
        reasons.append("negative_estimated_slippage")

    if request.entry_price == request.stop_price:
        reasons.append("zero_stop_distance")
    elif request.side == "buy" and request.stop_price >= request.entry_price:
        reasons.append("invalid_buy_stop_direction")
    elif request.side == "sell" and request.stop_price <= request.entry_price:
        reasons.append("invalid_sell_stop_direction")

    if request.target_price is not None:
        if request.side == "buy" and request.target_price <= request.entry_price:
            reasons.append("invalid_buy_target_direction")
        elif request.side == "sell" and request.target_price >= request.entry_price:
            reasons.append("invalid_sell_target_direction")

    return PretradeValidation(accepted=not reasons, reasons=tuple(reasons))


def require_valid_pretrade_request(request: PretradeRequest) -> PretradeValidation:
    validation = validate_pretrade_request(request)
    if not validation.accepted:
        joined = ", ".join(validation.reasons)
        raise ConfigError(f"Invalid pre-trade request: {joined}")
    return validation
