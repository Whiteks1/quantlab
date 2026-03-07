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

def _resolve_ticker(state: Dict[str, Any]) -> str:
    """
    Resolve ticker from portfolio state using a fallback chain.
    """
    candidate = state.get("candidate", {})
    params = candidate.get("params", {})
    
    ticker = (
        state.get("ticker") or 
        candidate.get("ticker") or 
        params.get("ticker")
    )
    if not ticker or str(ticker).strip() == "":
        return "N/A"
    return str(ticker)

def _get_dedup_key(sess: Dict[str, Any]) -> Tuple:
    """
    Generate a stable key for duplicate session detection.
    """
    return (
        sess.get("source_run_id", "N/A"),
        sess.get("ticker", "N/A"),
        sess.get("strategy", "N/A"),
        sess.get("eval_start", "N/A"),
        sess.get("eval_end", "N/A"),
        round(float(sess.get("starting_cash", 0.0)), 2),
        round(float(sess.get("ending_equity", 0.0)), 2),
    )

def aggregate_portfolio(
    session_dirs: List[str | Path], 
    mode: str = "raw_capital", 
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Aggregate multiple forward evaluation sessions into a portfolio payload.
    Applies deduplication, metadata normalization, and weighted allocation.
    """
    scanned_count = 0
    excluded_incomplete = 0
    
    raw_sessions: List[Dict[str, Any]] = []
    
    for d in session_dirs:
        scanned_count += 1
        p = Path(d)
        state_path = p / "portfolio_state.json"
        eq_path = p / "forward_equity_curve.csv"
        
        if not state_path.exists() or not eq_path.exists():
            excluded_incomplete += 1
            continue
            
        try:
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
            
            df_eq = pd.read_csv(eq_path)
            if df_eq.empty or "timestamp" not in df_eq.columns or "equity" not in df_eq.columns:
                excluded_incomplete += 1
                continue
                
            df_eq["timestamp"] = pd.to_datetime(df_eq["timestamp"])
            df_eq = df_eq.set_index("timestamp")
            
            candidate = state.get("candidate", {})
            initial_cash = float(state.get("starting_cash", 10_000.0))
            
            # Metadata normalization
            ticker = _resolve_ticker(state)
            strategy = candidate.get("strategy_name") or state.get("strategy_name") or "N/A"
            source_run_id = candidate.get("source_run_id") or state.get("source_run_id") or "N/A"
            
            raw_sessions.append({
                "session_id": state.get("session_id"),
                "ticker": ticker,
                "strategy": strategy,
                "source_run_id": source_run_id,
                "starting_cash": initial_cash,
                "ending_equity": float(df_eq["equity"].iloc[-1] * initial_cash),
                "total_pnl": float((df_eq["equity"].iloc[-1] - 1.0) * initial_cash),
                "total_return": float(df_eq["equity"].iloc[-1] - 1.0),
                "eval_start": state.get("eval_start", "N/A"),
                "eval_end": state.get("eval_end", "N/A"),
                "updated_at": state.get("updated_at", ""),
                "equity_norm": df_eq["equity"]  # Normalized 1.0-based series
            })
            
        except Exception as e:
            import warnings
            warnings.warn(f"[portfolio_report] Skipping {d}: {e}")
            excluded_incomplete += 1

    # Deduplication
    dedup_map: Dict[Tuple, Dict[str, Any]] = {}
    for sess in raw_sessions:
        key = _get_dedup_key(sess)
        if key not in dedup_map:
            dedup_map[key] = sess
        else:
            # Prefer the most recently updated
            existing = dedup_map[key]
            if sess.get("updated_at", "") > existing.get("updated_at", ""):
                dedup_map[key] = sess
                
    candidates_data = list(dedup_map.values())
    dropped_as_dupes = len(raw_sessions) - len(candidates_data)
    
    stats = {
        "sessions_scanned": scanned_count,
        "sessions_included": len(candidates_data),
        "sessions_excluded_incomplete": excluded_incomplete,
        "sessions_collapsed_duplicates": dropped_as_dupes
    }

    if not candidates_data:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "n_candidates": 0,
            "candidates": [],
            "portfolio_summary": {},
            **stats,
            "scanning_stats": stats
        }

    # Weight resolution
    target_weights = {}
    if mode == "equal_weight":
        n = len(candidates_data)
        for c in candidates_data:
            target_weights[c["session_id"]] = 1.0 / n
    elif mode == "custom_weight":
        if not weights:
            raise ValueError("custom_weight mode requires a weights mapping.")
        
        # Filter weights for included sessions only
        valid_weights = {sid: w for sid, w in weights.items() if any(c["session_id"] == sid for c in candidates_data)}
        if not valid_weights:
            raise ValueError("Custom weights refer only to excluded or nonexistent sessions.")

        # Validate: No negative weights
        if any(w < 0 for w in valid_weights.values()):
            raise ValueError("Custom weights cannot be negative.")
        
        total_w = sum(valid_weights.values())
        if total_w <= 0:
            raise ValueError("Total custom weight must be positive.")
            
        # Default others to zero, and normalize
        for c in candidates_data:
            sid = c["session_id"]
            target_weights[sid] = (valid_weights.get(sid, 0.0) / total_w)
    else: # raw_capital
        # In raw_capital, "weight" is the share of starting cash
        total_start_cash = sum(c["starting_cash"] for c in candidates_data)
        for c in candidates_data:
            target_weights[c["session_id"]] = (c["starting_cash"] / total_start_cash) if total_start_cash > 0 else 0.0

    # Apply resolved weights to candidates for metadata
    for c in candidates_data:
        c["assigned_weight"] = target_weights.get(c["session_id"], 0.0)

    # Weighted Equity Construction
    # Align all normalized (1.0 based) curves
    equity_norm_list = [c.get("equity_norm") for c in candidates_data]
    for i, s in enumerate(equity_norm_list):
        s.name = candidates_data[i]["session_id"]
        
    aligned_df = pd.concat(equity_norm_list, axis=1)
    
    # Handle staggered starts in weighted modes: before inception, weight = 0
    # Actually, if we multiply by weight directly, we need to handle when sum(weights) at t < 1.0
    # The requirement says "do NOT fabricate exposure before inception".
    # We'll build the weighted sum bar by bar.
    
    # For raw_capital, we continue with the absolute sum approach to stay consistent
    if mode == "raw_capital":
        # absolute sum logic (Stage M fix)
        abs_list = []
        for c in candidates_data:
            abs_eq = c["equity_norm"] * c["starting_cash"]
            abs_eq.name = c["session_id"]
            abs_list.append(abs_eq)
        
        portfolio_df = pd.concat(abs_list, axis=1)
        # Correct staggered starts: fill leading NaNs with starting cash
        for col in portfolio_df.columns:
            matching_c = next(c for c in candidates_data if c["session_id"] == col)
            sc = matching_c["starting_cash"]
            fv = portfolio_df[col].first_valid_index()
            if fv is not None:
                portfolio_df.loc[:fv, col] = portfolio_df.loc[:fv, col].fillna(sc)
        
        portfolio_df = portfolio_df.ffill()
        portfolio_equity = portfolio_df.sum(axis=1)
        starting_value = float(sum(c["starting_cash"] for c in candidates_data))
        ending_value = float(portfolio_equity.iloc[-1])
    else:
        # Weighted normalized logic
        # Before a session starts, its weight in the sum is essentially 0 or it's not present.
        # But if it hasn't started, the "portfolio" is composed of other things.
        # We will fill leading NaNs with 1.0 (neutral) so the weighted sum works correctly.
        # This treats a non-active session as "holding cash (1.0) with its assigned weight".
        for col in aligned_df.columns:
            # Find the first valid index (inception)
            fv = aligned_df[col].first_valid_index()
            if fv is not None:
                # Use .loc to fill everything before (and including) the first valid index
                # with 1.0 if it's currently NaN.
                aligned_df.loc[:fv, col] = aligned_df.loc[:fv, col].fillna(1.0)
        
        aligned_df = aligned_df.ffill()
        
        # Calculate weighted sum
        weights_series = pd.Series(target_weights)
        portfolio_equity_norm = (aligned_df * weights_series).sum(axis=1)
        
        # Scale to a nominal base (e.g. 10,000) for standard reporting look
        starting_value = 10_000.0
        portfolio_equity = portfolio_equity_norm * starting_value
        ending_value = float(portfolio_equity.iloc[-1])

    # Metrics
    total_pnl = float(ending_value - starting_value)
    total_return = float(ending_value / starting_value - 1.0) if starting_value > 0 else 0.0
    
    peak = portfolio_equity.cummax()
    dd = (portfolio_equity / peak) - 1.0
    max_dd = float(dd.min())
    
    # Contribution analysis (weighted)
    if mode == "raw_capital":
        for c in candidates_data:
            c["contribution_pct"] = float(c["total_pnl"] / total_pnl) if abs(total_pnl) > 1e-6 else 0.0
    else:
        # PnL contribution from weighted component i: w_i * (norm_eq_i_end - 1.0) * Portfolio_Start
        # sum of contributions will equal total portfolio PnL
        for c in candidates_data:
            sid = c["session_id"]
            w = float(target_weights.get(sid, 0.0))
            comp_normalized_pnl = float(c["total_return"]) # (norm_eq - 1.0)
            comp_pnl_in_portfolio = w * comp_normalized_pnl * starting_value
            c["contribution_pct"] = float(comp_pnl_in_portfolio / total_pnl) if abs(total_pnl) > 1e-6 else 0.0

    # CLEANUP: Pop equity_norm from candidates before payload construction
    for c in candidates_data:
        c.pop("equity_norm", None)

    # Ensure target_weights values are floats for JSON
    json_weights = {k: float(v) for k, v in target_weights.items()}

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_candidates": len(candidates_data),
        "candidates": candidates_data,
        "portfolio_summary": {
            "starting_value": float(starting_value),
            "ending_value": float(ending_value),
            "total_pnl": float(total_pnl),
            "total_return": float(total_return),
            "max_drawdown": float(max_dd),
            "n_bars": int(len(portfolio_equity))
        },
        "allocation": {
            "mode": mode,
            "weights_supplied": weights or {},
            "weights_used": json_weights,
            "normalized_weights": mode in ["equal_weight", "custom_weight"]
        },
        **stats,
        "scanning_stats": stats
    }
    
    return _sanitize(payload)

def render_portfolio_md(payload: Dict[str, Any]) -> str:
    """
    Render portfolio aggregation payload to Markdown.
    """
    summary = payload.get("portfolio_summary", {})
    candidates = payload.get("candidates", [])
    stats = payload.get("scanning_stats", {})
    alloc = payload.get("allocation", {})
    
    lines = [
        "# Portfolio Aggregation Report",
        "",
        f"- **Generated At:** {payload.get('generated_at', '—')}",
        "",
        "## Scanning & Deduplication",
        "",
        f"- **Sessions Scanned:** {stats.get('sessions_scanned', 0)}",
        f"- **Sessions Included:** {stats.get('sessions_included', 0)}",
        f"- **Sessions Excluded (Incomplete):** {stats.get('sessions_excluded_incomplete', 0)}",
        f"- **Sessions Collapsed (Duplicates):** {stats.get('sessions_collapsed_duplicates', 0)}",
        "",
        "## Allocation",
        "",
        f"- **Mode:** `{alloc.get('mode', 'raw_capital')}`",
        f"- **Included Sessions:** {payload.get('n_candidates', 0)}",
        f"- **Weights Normalized:** {'yes' if alloc.get('normalized_weights') else 'no'}",
        f"- **Total Assigned Weight:** {_fmt(sum(alloc.get('weights_used', {}).values()), '.4f')}",
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
        "| Session ID | Ticker | Strategy | Weight | Start Cash | End Equity | PnL | Return | Contribution |",
        "|------------|--------|----------|--------|------------|------------|-----|--------|--------------|",
    ]
    
    for c in candidates:
        weight_str = _fmt(c.get("assigned_weight"), ".2%") if "assigned_weight" in c else "—"
        lines.append(
            f"| `{c.get('session_id')}` | {c.get('ticker')} | {c.get('strategy')} | {weight_str} | "
            f"{_fmt(c.get('starting_cash'), ',.0f')} | {_fmt(c.get('ending_equity'), ',.2f')} | "
            f"{_fmt(c.get('total_pnl'), ',.2f')} | {_fmt(c.get('total_return'), '.2%')} | "
            f"{_fmt(c.get('contribution_pct'), '.1%')} |"
        )
        
    return "\n".join(lines)

def write_portfolio_report(
    session_dirs: List[str | Path], 
    out_dir: str | Path,
    mode: str = "raw_capital",
    weights: Optional[Dict[str, float]] = None
) -> Tuple[str, str]:
    """
    Write portfolio report artifacts to *out_dir*.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    payload = aggregate_portfolio(session_dirs, mode=mode, weights=weights)
    
    json_path = out_path / "portfolio_report.json"
    md_path = out_path / "portfolio_report.md"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_portfolio_md(payload))
        
    return str(json_path), str(md_path)
