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

def get_eligible_sessions(
    session_dirs: List[str | Path],
    top_n: Optional[int] = None,
    rank_metric: str = "total_return",
    min_return: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    include_tickers: Optional[List[str]] = None,
    exclude_tickers: Optional[List[str]] = None,
    include_strategies: Optional[List[str]] = None,
    exclude_strategies: Optional[List[str]] = None,
    latest_per_source_run: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Scan, hygiene, dedup, and filter sessions.
    Returns (sessions_list, scanning_stats).
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
            
            # Session-level metrics for selection
            eq = df_eq["equity"]
            peak = eq.cummax()
            dd = (eq / peak) - 1.0
            sess_max_dd = float(dd.min())

            raw_sessions.append({
                "session_id": state.get("session_id"),
                "ticker": ticker,
                "strategy": strategy,
                "source_run_id": source_run_id,
                "starting_cash": initial_cash,
                "ending_equity": float(eq.iloc[-1] * initial_cash),
                "total_pnl": float((eq.iloc[-1] - 1.0) * initial_cash),
                "total_return": float(eq.iloc[-1] - 1.0),
                "max_drawdown": sess_max_dd,
                "eval_start": state.get("eval_start", "N/A"),
                "eval_end": state.get("eval_end", "N/A"),
                "updated_at": state.get("updated_at", ""),
                "equity_norm": eq  # Normalized 1.0-based series
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
                
    candidates_after_dedup = list(dedup_map.values())
    dropped_as_dupes = len(raw_sessions) - len(candidates_after_dedup)

    # --- SELECTION FILTERS ---
    final_selected = candidates_after_dedup
    
    # 1. Ticker/Strategy Filters
    if include_tickers:
        final_selected = [c for c in final_selected if c["ticker"] in include_tickers]
    if exclude_tickers:
        final_selected = [c for c in final_selected if c["ticker"] not in exclude_tickers]
    if include_strategies:
        final_selected = [c for c in final_selected if c["strategy"] in include_strategies]
    if exclude_strategies:
        final_selected = [c for c in final_selected if c["strategy"] not in exclude_strategies]
        
    # 2. Performance Filters
    if min_return is not None:
        final_selected = [c for c in final_selected if c["total_return"] >= min_return]
    if max_drawdown is not None:
        # Threshold is decimal negative, e.g. -0.20
        final_selected = [c for c in final_selected if c["max_drawdown"] >= max_drawdown]
        
    # 3. Latest per source run
    if latest_per_source_run:
        grouped = {}
        for c in final_selected:
            srid = c["source_run_id"]
            if srid not in grouped or c["updated_at"] > grouped[srid]["updated_at"]:
                grouped[srid] = c
        final_selected = list(grouped.values())
        
    # 4. Ranking & Top-N
    if top_n is not None and top_n > 0:
        # Sort by rank_metric descending
        # If sort_key is contribution_pct, use total_pnl as proxy for ordering
        sk = rank_metric
        if sk == "contribution_pct":
            sk = "total_pnl"
        
        final_selected.sort(key=lambda x: x.get(sk, 0.0), reverse=True)
        final_selected = final_selected[:top_n]
    
    stats = {
        "sessions_scanned": scanned_count,
        "sessions_included": len(final_selected),
        "sessions_excluded_incomplete": excluded_incomplete,
        "sessions_collapsed_duplicates": dropped_as_dupes,
        "sessions_after_hygiene": len(raw_sessions),
        "sessions_after_dedup": len(candidates_after_dedup),
        "sessions_after_selection": len(final_selected)
    }
    
    return final_selected, stats

def compute_portfolio_from_sessions(
    candidates_data: List[Dict[str, Any]],
    mode: str = "raw_capital",
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Perform weighted aggregation and metric calculation from a list of eligible sessions.
    The candidates_data should contain 'equity_norm' series for each session.
    """
    if not candidates_data:
        raise ValueError("No portfolio sessions provided for aggregation.")

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
    # We work on a copy to avoid side effects if reused
    import copy
    work_candidates = copy.deepcopy(candidates_data)
    for c in work_candidates:
        c["assigned_weight"] = target_weights.get(c["session_id"], 0.0)

    # Weighted Equity Construction
    # Align all normalized (1.0 based) curves
    equity_norm_list = [c.get("equity_norm") for c in work_candidates]
    for i, s in enumerate(equity_norm_list):
        s.name = work_candidates[i]["session_id"]
        
    aligned_df = pd.concat(equity_norm_list, axis=1)
    
    # For raw_capital, we continue with the absolute sum approach to stay consistent
    if mode == "raw_capital":
        # absolute sum logic (Stage M fix)
        abs_list = []
        for c in work_candidates:
            abs_eq = c["equity_norm"] * c["starting_cash"]
            abs_eq.name = c["session_id"]
            abs_list.append(abs_eq)
        
        portfolio_df = pd.concat(abs_list, axis=1)
        # Correct staggered starts: fill leading NaNs with starting cash
        for col in portfolio_df.columns:
            matching_c = next(c for c in work_candidates if c["session_id"] == col)
            sc = matching_c["starting_cash"]
            fv = portfolio_df[col].first_valid_index()
            if fv is not None:
                portfolio_df.loc[:fv, col] = portfolio_df.loc[:fv, col].fillna(sc)
        
        portfolio_df = portfolio_df.ffill()
        portfolio_equity = portfolio_df.sum(axis=1)
        starting_value = float(sum(c["starting_cash"] for c in work_candidates))
        ending_value = float(portfolio_equity.iloc[-1])
    else:
        # Weighted normalized logic
        # Neutral fill for staggered starts
        for col in aligned_df.columns:
            fv = aligned_df[col].first_valid_index()
            if fv is not None:
                aligned_df.loc[:fv, col] = aligned_df.loc[:fv, col].fillna(1.0)
        
        aligned_df = aligned_df.ffill()
        
        # Calculate weighted sum
        weights_series = pd.Series(target_weights)
        portfolio_equity_norm = (aligned_df * weights_series).sum(axis=1)
        
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
        for c in work_candidates:
            c["contribution_pct"] = float(c["total_pnl"] / total_pnl) if abs(total_pnl) > 1e-6 else 0.0
    else:
        for c in work_candidates:
            sid = c["session_id"]
            w = float(target_weights.get(sid, 0.0))
            comp_normalized_pnl = float(c["total_return"])
            comp_pnl_in_portfolio = w * comp_normalized_pnl * starting_value
            c["contribution_pct"] = float(comp_pnl_in_portfolio / total_pnl) if abs(total_pnl) > 1e-6 else 0.0

    # CLEANUP: Pop equity_norm
    for c in work_candidates:
        c.pop("equity_norm", None)

    # Ensure target_weights values are floats for JSON
    json_weights = {k: float(v) for k, v in target_weights.items()}

    return {
        "candidates": work_candidates,
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
        }
    }

def aggregate_portfolio(
    session_dirs: List[str | Path], 
    mode: str = "raw_capital", 
    weights: Optional[Dict[str, float]] = None,
    top_n: Optional[int] = None,
    rank_metric: str = "total_return",
    min_return: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    include_tickers: Optional[List[str]] = None,
    exclude_tickers: Optional[List[str]] = None,
    include_strategies: Optional[List[str]] = None,
    exclude_strategies: Optional[List[str]] = None,
    latest_per_source_run: bool = False
) -> Dict[str, Any]:
    """
    Aggregate multiple forward evaluation sessions into a portfolio payload.
    Wrapper around get_eligible_sessions and compute_portfolio_from_sessions.
    """
    candidates_data, stats = get_eligible_sessions(
        session_dirs,
        top_n=top_n,
        rank_metric=rank_metric,
        min_return=min_return,
        max_drawdown=max_drawdown,
        include_tickers=include_tickers,
        exclude_tickers=exclude_tickers,
        include_strategies=include_strategies,
        exclude_strategies=exclude_strategies,
        latest_per_source_run=latest_per_source_run
    )

    if not candidates_data:
        raise ValueError(
            "No portfolio sessions remain after applying selection rules. "
            f"(scanned={stats['sessions_scanned']}, after_hygiene={stats['sessions_after_hygiene']}, "
            f"after_dedup={stats['sessions_after_dedup']}, after_selection=0)"
        )

    res = compute_portfolio_from_sessions(candidates_data, mode=mode, weights=weights)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_candidates": len(res["candidates"]),
        "candidates": res["candidates"],
        "portfolio_summary": res["portfolio_summary"],
        "allocation": res["allocation"],
        "selection": {
            "rank_metric": rank_metric,
            "top_n": top_n,
            "min_return": min_return,
            "max_drawdown": max_drawdown,
            "include_tickers": include_tickers,
            "exclude_tickers": exclude_tickers,
            "include_strategies": include_strategies,
            "exclude_strategies": exclude_strategies,
            "latest_per_source_run": latest_per_source_run
        },
        "scanning_stats": stats,
        **stats
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
    sel = payload.get("selection", {})
    
    lines = [
        "# Portfolio Aggregation Report",
        "",
        f"- **Generated At:** {payload.get('generated_at', '—')}",
        "",
        "## Scanning & Deduplication",
        "",
        f"- **Sessions Scanned:** {stats.get('sessions_scanned', 0)}",
        f"- **Sessions Included (Final):** {stats.get('sessions_included', 0)}",
        f"- **Sessions Excluded (Incomplete):** {stats.get('sessions_excluded_incomplete', 0)}",
        f"- **Sessions Collapsed (Duplicates):** {stats.get('sessions_collapsed_duplicates', 0)}",
        f"- **Sessions After Hygiene:** {stats.get('sessions_after_hygiene', 'N/A')}",
        f"- **Sessions After Dedup:** {stats.get('sessions_after_dedup', 'N/A')}",
        f"- **Sessions After Selection:** {stats.get('sessions_after_selection', 'N/A')}",
        "",
        "## Selection Rules",
        "",
        f"- **Rank Metric:** `{sel.get('rank_metric', 'total_return')}`",
        f"- **Top N:** {sel.get('top_n') or 'All'}",
        f"- **Min Return:** {sel.get('min_return') if sel.get('min_return') is not None else 'None'}",
        f"- **Max Drawdown:** {sel.get('max_drawdown') if sel.get('max_drawdown') is not None else 'None'}",
        f"- **Include Tickers:** {', '.join(sel.get('include_tickers')) if sel.get('include_tickers') else 'All'}",
        f"- **Exclude Tickers:** {', '.join(sel.get('exclude_tickers')) if sel.get('exclude_tickers') else 'None'}",
        f"- **Include Strategies:** {', '.join(sel.get('include_strategies')) if sel.get('include_strategies') else 'All'}",
        f"- **Exclude Strategies:** {', '.join(sel.get('exclude_strategies')) if sel.get('exclude_strategies') else 'None'}",
        f"- **Latest Per Source Run:** {'Yes' if sel.get('latest_per_source_run') else 'No'}",
        "",
        "## Allocation",
        "",
        f"- **Mode:** `{alloc.get('mode', 'raw_capital')}`",
        f"- **Included Sessions:** {len(candidates)}",
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
    weights: Optional[Dict[str, float]] = None,
    top_n: Optional[int] = None,
    rank_metric: str = "total_return",
    min_return: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    include_tickers: Optional[List[str]] = None,
    exclude_tickers: Optional[List[str]] = None,
    include_strategies: Optional[List[str]] = None,
    exclude_strategies: Optional[List[str]] = None,
    latest_per_source_run: bool = False
) -> Tuple[str, str]:
    """
    Write portfolio report artifacts to *out_dir*.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    payload = aggregate_portfolio(
        session_dirs, 
        mode=mode, 
        weights=weights,
        top_n=top_n,
        rank_metric=rank_metric,
        min_return=min_return,
        max_drawdown=max_drawdown,
        include_tickers=include_tickers,
        exclude_tickers=exclude_tickers,
        include_strategies=include_strategies,
        exclude_strategies=exclude_strategies,
        latest_per_source_run=latest_per_source_run
    )
    
    json_path = out_path / "portfolio_report.json"
    md_path = out_path / "portfolio_report.md"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_portfolio_md(payload))
        
    return str(json_path), str(md_path)
