"""
portfolio_mode_compare.py – Stage M.4: compare portfolio aggregation modes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from quantlab.reporting.forward_report import _sanitize, _fmt
from quantlab.reporting.portfolio_report import (
    get_eligible_sessions,
    compute_portfolio_from_sessions
)

def compare_portfolio_modes(
    session_dirs: List[str | Path],
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
    Compare multiple allocation modes over the same set of eligible sessions.
    """
    # 1. Get eligible sessions (the stable universe)
    eligible_sessions, stats = get_eligible_sessions(
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

    if not eligible_sessions:
        raise ValueError("No eligible sessions found for comparison.")

    # 2. Run aggregation for each mode
    modes = ["raw_capital", "equal_weight"]
    if weights:
        modes.append("custom_weight")

    comparison_results = {}
    for mode in modes:
        res = compute_portfolio_from_sessions(
            eligible_sessions,
            mode=mode,
            weights=weights
        )
        comparison_results[mode] = res["portfolio_summary"]
        # Add a few more details to the summary for comparison
        comparison_results[mode]["mode"] = mode

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_sessions": len(eligible_sessions),
        "selection_stats": stats,
        "comparison": comparison_results,
        "selection_criteria": {
            "rank_metric": rank_metric,
            "top_n": top_n,
            "min_return": min_return,
            "max_drawdown": max_drawdown,
            "include_tickers": include_tickers,
            "exclude_tickers": exclude_tickers,
            "include_strategies": include_strategies,
            "exclude_strategies": exclude_strategies,
            "latest_per_source_run": latest_per_source_run
        }
    }

    return _sanitize(payload)

def render_comparison_md(payload: Dict[str, Any]) -> str:
    """
    Render portfolio mode comparison payload to Markdown.
    """
    comp = payload.get("comparison", {})
    sel = payload.get("selection_criteria", {})
    
    lines = [
        "# Portfolio Mode Comparison Report",
        "",
        f"- **Generated At:** {payload.get('generated_at', '—')}",
        f"- **Eligible Sessions:** {payload.get('n_sessions', 0)}",
        "",
        "## Selection Context",
        "",
        f"- **Top N:** {sel.get('top_n') or 'All'}",
        f"- **Rank Metric:** `{sel.get('rank_metric', 'total_return')}`",
        f"- **Filters Applied:** " + (
            f"min_ret={sel.get('min_return') or 'None'}, "
            f"max_dd={sel.get('max_drawdown') or 'None'}, "
            f"latest_only={sel.get('latest_per_source_run')}"
        ),
        "",
        "## Side-by-Side Comparison",
        "",
        "| Metric | " + " | ".join(f"`{m}`" for m in comp.keys()) + " |",
        "|--------|" + "|".join(["----------"] * len(comp)) + "|",
    ]

    metrics = [
        ("Starting Value", "starting_value", ",.2f"),
        ("Ending Value", "ending_value", ",.2f"),
        ("Total PnL", "total_pnl", ",.2f"),
        ("Total Return", "total_return", ".2%"),
        ("Max Drawdown", "max_drawdown", ".2%"),
        ("Aggregate Bars", "n_bars", "d"),
    ]

    for label, key, fmt in metrics:
        row = [label]
        for mode in comp.keys():
            val = comp[mode].get(key, 0.0)
            row.append(_fmt(val, fmt))
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)

def write_mode_comparison_report(
    session_dirs: List[str | Path],
    out_dir: str | Path,
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
    Perform comparison and write artifacts.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    payload = compare_portfolio_modes(
        session_dirs,
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

    json_path = out_path / "portfolio_compare.json"
    md_path = out_path / "portfolio_compare.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_comparison_md(payload))

    return str(json_path), str(md_path)
