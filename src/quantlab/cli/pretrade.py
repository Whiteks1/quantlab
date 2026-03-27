from __future__ import annotations

from pathlib import Path

from quantlab.errors import ConfigError
from quantlab.pretrade.artifacts import default_pretrade_root, write_pretrade_artifacts
from quantlab.pretrade.calculator import build_pretrade_plan
from quantlab.pretrade.models import PretradeRequest
from quantlab.pretrade.policy_checks import normalize_side
from quantlab.pretrade.serializers import summary_to_dict


def handle_pretrade_commands(args, *, project_root: str | Path) -> dict[str, object] | bool:
    if not getattr(args, "pretrade_plan", False):
        return False

    request = PretradeRequest(
        symbol=_required_text(args.pretrade_symbol, "pretrade_symbol"),
        venue=_required_text(args.pretrade_venue, "pretrade_venue"),
        side=normalize_side(_required_text(args.pretrade_side, "pretrade_side")),
        capital=_required_float(args.pretrade_capital, "pretrade_capital"),
        risk_percent=_required_float(args.pretrade_risk_percent, "pretrade_risk_percent"),
        entry_price=_required_float(args.pretrade_entry_price, "pretrade_entry_price"),
        stop_price=_required_float(args.pretrade_stop_price, "pretrade_stop_price"),
        target_price=_optional_float(getattr(args, "pretrade_target_price", None), "pretrade_target_price"),
        estimated_fees=float(getattr(args, "pretrade_estimated_fees", 0.0) or 0.0),
        estimated_slippage=float(getattr(args, "pretrade_estimated_slippage", 0.0) or 0.0),
        account_id=_optional_text(getattr(args, "pretrade_account_id", None)),
        strategy_id=_optional_text(getattr(args, "pretrade_strategy_id", None)),
        notes=_optional_text(getattr(args, "pretrade_notes", None)),
        session_id=_optional_text(getattr(args, "pretrade_session_id", None)),
    )
    plan = build_pretrade_plan(request)

    root_dir = (
        Path(args.pretrade_sessions_root)
        if getattr(args, "pretrade_sessions_root", None)
        else default_pretrade_root(project_root)
    )
    paths = write_pretrade_artifacts(plan, root_dir=root_dir)
    summary = summary_to_dict(plan)

    print("\nPre-trade plan created:\n")
    print(f"  session_id         : {plan.session_id}")
    print(f"  session_dir        : {paths['session_dir']}")
    print(f"  symbol             : {plan.request.symbol}")
    print(f"  venue              : {plan.request.venue}")
    print(f"  side               : {plan.request.side}")
    print(f"  risk_amount        : {plan.risk_amount:.6f}")
    print(f"  position_size      : {plan.position_size:.6f}")
    print(f"  notional           : {plan.notional:.6f}")
    print(f"  max_loss_at_stop   : {plan.max_loss_at_stop:.6f}")
    if plan.net_profit_at_target is not None:
        print(f"  net_profit_target  : {plan.net_profit_at_target:.6f}")
    if plan.risk_reward_ratio is not None:
        print(f"  risk_reward_ratio  : {plan.risk_reward_ratio:.6f}")
    print(f"  plan_path          : {paths['plan_path']}")
    print(f"  summary_path       : {paths['summary_path']}")

    return {
        "status": "success",
        "mode": "pretrade",
        "session_id": plan.session_id,
        "pretrade_root": str(root_dir),
        "pretrade_session_dir": paths["session_dir"],
        "pretrade_plan_path": paths["plan_path"],
        "pretrade_summary_path": paths["summary_path"],
        "pretrade_summary": summary,
    }


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} is required.")
    return value.strip()


def _required_float(value: object, field_name: str) -> float:
    if value is None:
        raise ConfigError(f"{field_name} is required.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field_name} must be numeric.") from exc


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field_name} must be numeric when provided.") from exc
