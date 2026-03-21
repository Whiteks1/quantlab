"""
report_summary.py — Standard indicators and summary schema for QuantLab reporting.

This module provides utilities to build a standardized machine-readable summary
block for every run, regardless of the session type.
"""

from typing import Any, Dict, Optional
import math

def build_standard_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a standardized KPI summary object from varying internal metric formats.
    
    Expected keys in input (mapping logic):
    - total_return / portfolio_summary.total_return
    - sharpe_simple / sharpe / equity_metrics.sharpe
    - max_drawdown / portfolio_summary.max_drawdown
    - trades / n_trades / trade_distribution.n_trades
    - win_rate / win_rate_trades / trade_distribution.win_rate
    """
    
    # helper to safely extract and float-ify
    def get_float(obj, keys, default=None):
        for k in keys:
            val = obj.get(k)
            if val is not None:
                try:
                    fval = float(val)
                    return fval if math.isfinite(fval) else None
                except (TypeError, ValueError):
                    continue
        return default

    # Flatten nested structures if present
    # (some modules provide summary vs metrics vs equity_metrics)
    flat = metrics.copy()
    if "portfolio_summary" in metrics:
        flat.update(metrics["portfolio_summary"])
    if "equity_metrics" in metrics:
        flat.update(metrics["equity_metrics"])
    if "trade_distribution" in metrics:
        flat.update(metrics["trade_distribution"])
    if "summary" in metrics and isinstance(metrics["summary"], dict):
        flat.update(metrics["summary"])

    summary = {
        "total_return": get_float(flat, ["total_return", "total_pnl_pct"]),
        "sharpe_simple": get_float(flat, ["sharpe_simple", "sharpe", "sharpe_ratio"]),
        "max_drawdown": get_float(flat, ["max_drawdown", "max_dd"]),
        "trades": int(flat.get("trades") or flat.get("n_trades") or flat.get("total_trades") or 0),
        "win_rate": get_float(flat, ["win_rate", "win_rate_trades", "win_rate_pct"]),
    }

    return summary
