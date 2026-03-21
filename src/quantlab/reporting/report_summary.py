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
    if "metrics" in metrics and isinstance(metrics["metrics"], dict):
        flat.update(metrics["metrics"])
    if "backtest_metrics" in metrics and isinstance(metrics["backtest_metrics"], dict):
        flat.update(metrics["backtest_metrics"])
    if "portfolio_summary" in metrics and isinstance(metrics["portfolio_summary"], dict):
        flat.update(metrics["portfolio_summary"])
    if "equity_metrics" in metrics and isinstance(metrics["equity_metrics"], dict):
        flat.update(metrics["equity_metrics"])
    if "trade_distribution" in metrics and isinstance(metrics["trade_distribution"], dict):
        flat.update(metrics["trade_distribution"])
    if "summary" in metrics and isinstance(metrics["summary"], dict):
        flat.update(metrics["summary"])
    if "meta" in metrics and isinstance(metrics["meta"], dict):
        # some keys might be inside meta (e.g. backtest_metrics)
        m = metrics["meta"]
        if "backtest_metrics" in m and isinstance(m["backtest_metrics"], dict):
            flat.update(m["backtest_metrics"])

    # Helper to safely extract integer count for trades
    def get_int_count(obj, keys):
        for k in keys:
            val = obj.get(k)
            if val is not None and not isinstance(val, (list, tuple, dict)):
                try:
                    return int(val)
                except (TypeError, ValueError):
                    continue
        # Fallback: if 'trades' is a list/tuple, return its length
        t_val = obj.get("trades")
        if isinstance(t_val, (list, tuple)):
            return len(t_val)
        return 0

    summary = {
        "total_return": get_float(flat, ["total_return", "total_pnl_pct"]),
        "sharpe_simple": get_float(flat, ["sharpe_simple", "sharpe", "sharpe_ratio"]),
        "max_drawdown": get_float(flat, ["max_drawdown", "max_dd"]),
        "trades": get_int_count(flat, ["n_trades", "total_trades", "trades"]),
        "win_rate": get_float(flat, ["win_rate", "win_rate_trades", "win_rate_pct"]),
    }

    return summary
