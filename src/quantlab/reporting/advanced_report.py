"""
advanced_report.py – Stage K: orchestrates advanced analytics for a run.

Combines advanced metrics + charts into two artifacts:
 - advanced_report.json  (strict, allow_nan=False)
 - advanced_report.md

Functions
---------
build_advanced_report(run_dir)     -> dict
render_advanced_report_md(payload) -> str
write_advanced_report(run_dir)     -> tuple[str, str]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from quantlab.reporting.advanced_metrics import build_advanced_metrics, _sanitize
from quantlab.reporting.charts import generate_charts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(val: Any, fmt: str) -> str:
    """
    Format *val* using *fmt* spec, returning ``'N/A'`` for ``None`` and
    falling back gracefully on type errors.
    """
    if val is None:
        return "N/A"
    try:
        return format(val, fmt)
    except (TypeError, ValueError):
        return str(val)


def _fmt_pct(val: Any) -> str:
    """Format a ratio as a percentage string, or 'N/A'."""
    return _fmt(val, ".1%")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_advanced_report(run_dir: str | Path) -> Dict[str, Any]:
    """
    Build the full advanced report payload for a run directory.

    Calls ``build_advanced_metrics`` and ``generate_charts``, combines their
    outputs, and returns a sanitised dict.

    Parameters
    ----------
    run_dir:
        Completed run directory.

    Returns
    -------
    dict
        Strictly JSON-serialisable payload.
    """
    run_path = Path(run_dir)

    # 1) Advanced metrics
    metrics = build_advanced_metrics(run_path)

    # 2) Charts (written into run_dir)
    chart_paths = generate_charts(run_path, out_dir=run_path)

    # 3) Artifact scan
    artifacts: List[Dict[str, Any]] = []
    for f in sorted(run_path.iterdir()):
        if f.is_file():
            artifacts.append({"file": f.name, "size_bytes": f.stat().st_size})

    payload = {
        **metrics,
        "charts": [Path(p).name for p in chart_paths],
        "artifacts": artifacts,
    }

    return _sanitize(payload)


def render_advanced_report_md(payload: Dict[str, Any]) -> str:
    """
    Render the advanced report payload as a Markdown document.

    Unreliable metrics (``None``) are shown as ``N/A`` rather than
    being omitted or displayed as raw non-finite floats.  The time-window
    section renders an informational note for insufficient data rather than
    producing a misleading or empty section.

    Parameters
    ----------
    payload:
        Dict returned by :func:`build_advanced_report`.

    Returns
    -------
    str
        Full Markdown text.
    """
    run_id = payload.get("run_id", "unknown")
    mode = payload.get("mode", "—")
    created = payload.get("created_at", "—")

    lines = [
        f"# Advanced Run Report: {run_id}",
        "",
        "## Summary",
        "",
        f"- **Mode:** {mode}",
        f"- **Created At:** {created}",
        "",
    ]

    # Core metrics
    em = payload.get("equity_metrics", {})
    if em:
        lines += [
            "## Core Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]
        metric_labels = [
            ("Total Return", "total_return", ".2%"),
            ("CAGR", "cagr", ".2%"),
            ("Sharpe Ratio", "sharpe", ".3f"),
            ("Sortino Ratio", "sortino", ".3f"),
            ("Annualised Volatility", "annualized_volatility", ".2%"),
            ("Days", "n_days", "d"),
        ]
        for label, key, fmt in metric_labels:
            val = em.get(key)
            formatted = _fmt(val, fmt)
            # Annotate ratios that are N/A so reader knows why
            if val is None and key in ("sortino", "sharpe"):
                formatted = "N/A *(insufficient data)*"
            lines.append(f"| {label} | {formatted} |")
        lines.append("")

    # Drawdown
    dm = payload.get("drawdown_metrics", {})
    if dm:
        lines += [
            "## Drawdown Analysis",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]
        dd_labels = [
            ("Max Drawdown", "max_drawdown", ".2%"),
            ("Avg Drawdown", "avg_drawdown", ".2%"),
            ("Calmar Ratio", "calmar", ".3f"),
            ("Longest DD (days)", "longest_dd_days", "d"),
            ("# Drawdown Periods", "n_drawdown_periods", "d"),
        ]
        for label, key, fmt in dd_labels:
            val = dm.get(key)
            formatted = _fmt(val, fmt)
            if val is None and key == "calmar":
                formatted = "N/A *(drawdown too small)*"
            lines.append(f"| {label} | {formatted} |")
        lines.append("")

    # Trade distribution
    td = payload.get("trade_distribution", {})
    if td.get("n_trades", 0) > 0:
        lines += [
            "## Trade Distribution",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]
        trade_labels = [
            ("Trades", "n_trades", "d"),
            ("Win Rate", "win_rate", ".1%"),
            ("Profit Factor", "profit_factor", ".2f"),
            ("Expectancy (net PnL)", "expectancy", ".4f"),
            ("Avg Return", "avg_return", ".2%"),
            ("Median Return", "median_return", ".2%"),
            ("Best Trade PnL", "best_trade_pnl", ".4f"),
            ("Worst Trade PnL", "worst_trade_pnl", ".4f"),
            ("Top-3 PnL Share", "top3_pnl_share", ".1%"),
            ("Max Consec. Losses", "max_consecutive_losses", "d"),
        ]
        for label, key, fmt in trade_labels:
            val = td.get(key)
            lines.append(f"| {label} | {_fmt(val, fmt)} |")
        lines.append("")

    # Time window
    tw = payload.get("time_window_metrics", {})
    if tw:
        lines += [
            "## Time Window Analysis",
            "",
        ]
        if tw.get("insufficient_data"):
            note = tw.get("note", "Insufficient monthly data for statistics.")
            lines += [
                f"> ⚠️ **Note:** {note}",
                "",
            ]
        else:
            best = _fmt_pct(tw.get("best_month"))
            worst = _fmt_pct(tw.get("worst_month"))
            pos_pct = _fmt_pct(tw.get("positive_months_pct"))
            lines += [
                f"- **Best month:** {best}",
                f"- **Worst month:** {worst}",
                f"- **Positive months:** {pos_pct}",
                "",
            ]
            monthly = tw.get("monthly_returns", [])
            if monthly:
                df_m = pd.DataFrame(monthly)
                lines.append(df_m.to_markdown(index=False))
                lines.append("")

    # Charts
    charts = payload.get("charts", [])
    lines += ["## Charts", ""]
    if charts:
        for c in charts:
            lines.append(f"- `{c}`")
    else:
        lines.append("_No charts generated (insufficient data)._")
    lines.append("")

    # Artifacts
    artifacts = payload.get("artifacts", [])
    lines += ["## Artifacts", ""]
    if artifacts:
        df_a = pd.DataFrame(artifacts)
        lines.append(df_a.to_markdown(index=False))
    else:
        lines.append("_No artifacts found._")

    return "\n".join(lines)


def write_advanced_report(run_dir: str | Path) -> Tuple[str, str]:
    """
    Build the advanced report and write artifacts to *run_dir*.

    Generates:
    - ``advanced_report.json``  (strict JSON)
    - ``advanced_report.md``
    - Chart PNG files (via :func:`~charts.generate_charts`)

    Parameters
    ----------
    run_dir:
        Completed run directory.

    Returns
    -------
    tuple[str, str]
        Paths to (json, md).
    """
    run_path = Path(run_dir)
    payload = build_advanced_report(run_path)

    json_path = run_path / "advanced_report.json"
    md_path = run_path / "advanced_report.md"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, allow_nan=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_advanced_report_md(payload))

    return str(json_path), str(md_path)
