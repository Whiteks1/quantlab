"""
portfolio_report.py – Stage M: portfolio aggregation and reporting for QuantLab.

Aggregates multiple forward evaluation sessions into a single portfolio-level view.
Produces:
- ``portfolio_report.json``
- ``portfolio_report.md``
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from quantlab.reporting.forward_report import _sanitize, _fmt

def aggregate_portfolio(session_dirs: List[str | Path]) -> Dict[str, Any]:
    """
    Aggregate multiple forward evaluation sessions into a portfolio payload.
    """
    candidates_data = []
    equity_series_list = []
    
    for d in session_dirs:
        p = Path(d)
        state_path = p / "portfolio_state.json"
        eq_path = p / "forward_equity_curve.csv"
        
        if not state_path.exists() or not eq_path.exists():
            continue
            
        try:
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
            
            df_eq = pd.read_csv(eq_path)
            if df_eq.empty or "timestamp" not in df_eq.columns or "equity" not in df_eq.columns:
                continue
                
            df_eq["timestamp"] = pd.to_datetime(df_eq["timestamp"])
            df_eq = df_eq.set_index("timestamp")
            
            # Use absolute equity for aggregation
            # In Stage L, forward_equity_curve.csv is normalized (starts at 1.0)
            initial_cash = float(state.get("starting_cash", 10_000.0))
            abs_equity = df_eq["equity"] * initial_cash
            abs_equity.name = state.get("session_id", p.name)
            
            equity_series_list.append(abs_equity)
            
            # Gather candidate info
            candidate = state.get("candidate", {})
            candidates_data.append({
                "session_id": state.get("session_id"),
                "ticker": candidate.get("ticker", "N/A"),
                "strategy": candidate.get("strategy_name", "N/A"),
                "starting_cash": initial_cash,
                "ending_equity": float(abs_equity.iloc[-1]),
                "total_pnl": float(abs_equity.iloc[-1] - initial_cash),
                "total_return": float(abs_equity.iloc[-1] / initial_cash - 1.0) if initial_cash > 0 else 0.0
            })
            
        except Exception as e:
            import warnings
            warnings.warn(f"[portfolio_report] Skipping {d}: {e}")

    if not equity_series_list:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "n_candidates": 0,
            "candidates": [],
            "portfolio_summary": {}
        }

    # Align all equity curves
    portfolio_df = pd.concat(equity_series_list, axis=1)
    
    # Correct staggered starts: fill leading NaNs with starting cash for each candidate
    # This prevents fake initial drawdowns when one candidate starts later than others.
    for col in portfolio_df.columns:
        # Match col back to candidate starting cash
        matching_c = next(c for c in candidates_data if c["session_id"] == col)
        start_cash = matching_c["starting_cash"]
        
        # Fill leading NaNs ONLY
        first_valid_idx = portfolio_df[col].first_valid_index()
        if first_valid_idx is not None:
            portfolio_df.loc[:first_valid_idx, col] = portfolio_df.loc[:first_valid_idx, col].fillna(start_cash)

    # Forward fill trailing gaps (standard QuantLab research assumption)
    portfolio_df = portfolio_df.ffill()
    
    # Portfolio equity is the sum of all components
    portfolio_equity = portfolio_df.sum(axis=1)
    
    # Portfolio Metrics
    starting_value = sum(c["starting_cash"] for c in candidates_data)
    ending_value = portfolio_equity.iloc[-1]
    
    total_return = (ending_value / starting_value - 1.0) if starting_value > 0 else 0.0
    
    peak = portfolio_equity.cummax()
    dd = (portfolio_equity / peak) - 1.0
    max_dd = float(dd.min())
    
    # Contribution analysis
    total_portfolio_pnl = ending_value - starting_value
    for c in candidates_data:
        c["contribution_pct"] = (c["total_pnl"] / total_portfolio_pnl) if abs(total_portfolio_pnl) > 1e-6 else 0.0

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_candidates": len(candidates_data),
        "candidates": candidates_data,
        "portfolio_summary": {
            "starting_value": starting_value,
            "ending_value": ending_value,
            "total_pnl": total_portfolio_pnl,
            "total_return": total_return,
            "max_drawdown": max_dd,
            "n_bars": len(portfolio_equity)
        }
    }
    
    return _sanitize(payload)

def render_portfolio_md(payload: Dict[str, Any]) -> str:
    """
    Render portfolio aggregation payload to Markdown.
    """
    summary = payload.get("portfolio_summary", {})
    candidates = payload.get("candidates", [])
    
    lines = [
        "# Portfolio Aggregation Report",
        "",
        f"- **Generated At:** {payload.get('generated_at', '—')}",
        f"- **Candidate Count:** {payload.get('n_candidates', 0)}",
        "",
        "## Portfolio Summary",
        "",
        f"- **Starting Value:** {_fmt(summary.get('starting_value'), ',.2f')}",
        f"- **Ending Value:** {_fmt(summary.get('ending_value'), ',.2f')}",
        f"- **Total PnL:** {_fmt(summary.get('total_pnl'), ',.2f')}",
        f"- **Total Return:** {_fmt(summary.get('total_return'), '.2%')}",
        f"- **Max Drawdown:** {_fmt(summary.get('max_drawdown'), '.2%')}",
        f"- **Aggregate Bars:** {summary.get('n_bars', 0)}",
        "",
        "## Candidate Breakdown",
        "",
        "| Session ID | Ticker | Strategy | Start Cash | End Equity | PnL | Return | Contribution |",
        "|------------|--------|----------|------------|------------|-----|--------|--------------|",
    ]
    
    for c in candidates:
        lines.append(
            f"| `{c.get('session_id')}` | {c.get('ticker')} | {c.get('strategy')} | "
            f"{_fmt(c.get('starting_cash'), ',.0f')} | {_fmt(c.get('ending_equity'), ',.2f')} | "
            f"{_fmt(c.get('total_pnl'), ',.2f')} | {_fmt(c.get('total_return'), '.2%')} | "
            f"{_fmt(c.get('contribution_pct'), '.1%')} |"
        )
        
    return "\n".join(lines)

def write_portfolio_report(session_dirs: List[str | Path], out_dir: str | Path) -> Tuple[str, str]:
    """
    Write portfolio report artifacts to *out_dir*.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    payload = aggregate_portfolio(session_dirs)
    
    json_path = out_path / "portfolio_report.json"
    md_path = out_path / "portfolio_report.md"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_portfolio_md(payload))
        
    return str(json_path), str(md_path)
