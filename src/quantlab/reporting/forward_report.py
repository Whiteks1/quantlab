"""
forward_report.py – Stage L: forward evaluation reporting for QuantLab.

Reads forward evaluation artifacts from an output directory and produces:
- ``forward_report.json``  (strict, allow_nan=False)
- ``forward_report.md``

Functions
---------
build_forward_report(out_dir)      -> dict
render_forward_report_md(payload)  -> str
write_forward_report(out_dir)      -> tuple[str, str]
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from quantlab.reporting.charts import plot_equity_curve, plot_drawdown


# ---------------------------------------------------------------------------
# JSON sanitisation
# ---------------------------------------------------------------------------

def _sanitize(obj: Any) -> Any:
    """Recursively make a nested structure strictly JSON-safe."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def _fmt(val: Any, fmt: str) -> str:
    """Format *val* using *fmt* spec, returning 'N/A' for None."""
    if val is None:
        return "N/A"
    try:
        return format(val, fmt)
    except (TypeError, ValueError):
        return str(val)


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def _compute_summary_metrics(
    equity: pd.Series,
    trades_df: pd.DataFrame,
    initial_cash: float,
) -> Dict[str, Any]:
    """Derive summary metrics from equity curve and trade log."""
    metrics: Dict[str, Any] = {}

    # Equity metrics
    if equity is not None and len(equity) >= 2:
        eq = equity.dropna()
        total_return = float(eq.iloc[-1] / eq.iloc[0]) - 1.0 if eq.iloc[0] > 0 else None
        metrics["total_return"] = total_return if total_return is None or math.isfinite(total_return) else None

        # Max drawdown
        peak = eq.cummax()
        dd = (eq / peak) - 1.0
        metrics["max_drawdown"] = float(dd.min()) if not dd.empty else None

        # Ann. volatility
        daily_ret = eq.pct_change().dropna()
        import numpy as np
        metrics["annualized_volatility"] = (
            float(daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 1 else None
        )
        metrics["n_bars"] = len(eq)

    # Trade metrics
    if trades_df is not None and not trades_df.empty and "fee" in trades_df.columns:
        pnl_series = _extract_round_trip_pnl(trades_df, initial_cash)
        n_trades = len(pnl_series)
        metrics["n_trades"] = n_trades
        if n_trades > 0:
            metrics["win_rate"] = float((pnl_series > 0).mean())
            metrics["expectancy"] = float(pnl_series.mean())
            metrics["best_trade_pnl"] = float(pnl_series.max())
            metrics["worst_trade_pnl"] = float(pnl_series.min())
            metrics["total_fees"] = float(trades_df["fee"].sum())
        else:
            metrics.update({"win_rate": None, "expectancy": None,
                            "best_trade_pnl": None, "worst_trade_pnl": None,
                            "total_fees": 0.0})
    else:
        metrics.update({"n_trades": 0, "win_rate": None, "expectancy": None,
                        "best_trade_pnl": None, "worst_trade_pnl": None,
                        "total_fees": 0.0})

    return _sanitize(metrics)


def _extract_round_trip_pnl(trades_df: pd.DataFrame, initial_cash: float) -> pd.Series:
    """
    Compute per round-trip PnL from a forward trades log.

    Pairs BUY→SELL sequentially and returns net PnL per closed trade.
    """
    pnl_list = []
    open_eq: Optional[float] = None
    for _, row in trades_df.iterrows():
        side = str(row.get("side", ""))
        eq = row.get("equity_after")
        if eq is None:
            continue
        eq = float(eq)
        if side == "BUY":
            open_eq = eq
        elif side == "SELL" and open_eq is not None:
            pnl_list.append(eq - open_eq)
            open_eq = None
    return pd.Series(pnl_list, dtype=float)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_forward_report(out_dir: str | Path) -> Dict[str, Any]:
    """
    Build the forward evaluation report payload from persisted artifacts.

    Loads ``portfolio_state.json``, ``forward_trades.csv``, and
    ``forward_equity_curve.csv`` from *out_dir* and computes summary metrics.

    Parameters
    ----------
    out_dir:
        Directory written by :func:`~quantlab.execution.forward_eval.write_forward_eval_artifacts`.

    Returns
    -------
    dict
        Strictly JSON-serialisable payload.
    """
    out_path = Path(out_dir)

    # Portfolio state
    state: Dict[str, Any] = {}
    state_path = out_path / "portfolio_state.json"
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as fh:
                state = json.load(fh)
        except Exception:
            pass

    # Trades
    trades_df: Optional[pd.DataFrame] = None
    trades_path = out_path / "forward_trades.csv"
    if trades_path.exists():
        try:
            trades_df = pd.read_csv(trades_path)
        except Exception:
            pass

    # Equity curve
    equity: Optional[pd.Series] = None
    eq_path = out_path / "forward_equity_curve.csv"
    if eq_path.exists():
        try:
            df_eq = pd.read_csv(eq_path)
            if "equity" in df_eq.columns:
                equity = df_eq["equity"].dropna()
        except Exception:
            pass

    initial_cash = float(state.get("cash", 0.0) or state.get("current_equity", 10_000.0))
    # Prefer initial_cash from candidate params if explicitly stored
    candidate = state.get("candidate", {})

    summary = _compute_summary_metrics(
        equity=equity,
        trades_df=trades_df,
        initial_cash=initial_cash or 10_000.0,
    )

    # Artifact list
    artifacts: List[Dict[str, Any]] = []
    for f in sorted(out_path.iterdir()):
        if f.is_file():
            artifacts.append({"file": f.name, "size_bytes": f.stat().st_size})

    payload = {
        "session_id": state.get("session_id", ""),
        "mode": state.get("mode", "forward_paper"),
        "eval_start": state.get("eval_start", ""),
        "eval_end": state.get("eval_end", ""),
        "created_at": state.get("created_at", ""),
        "updated_at": state.get("updated_at", ""),
        "candidate": candidate,
        "portfolio_state": state,
        "summary": summary,
        "artifacts": artifacts,
        "charts": [],
        # Stage L.1
        "performance": {
            "starting_cash": state.get("starting_cash", initial_cash),
            "ending_equity": state.get("current_equity", 0.0),
            "realized_pnl": state.get("realized_pnl", 0.0),
            "unrealized_pnl": state.get("unrealized_pnl", 0.0),
            "total_pnl": state.get("current_equity", 0.0) - state.get("starting_cash", initial_cash),
        },
        "warmup": {
            "bars_fetched": state.get("bars_fetched", 0),
            "warmup_bars": state.get("warmup_bars", 0),
            "bars_evaluated": state.get("bars_evaluated", summary.get("n_bars", 0)),
        },
        "continuity": {
            "is_resumed": (state.get("resume_count", 0) > 0),
            "original_start": state.get("original_eval_start", ""),
            "latest_update": state.get("eval_end", ""),
            "resume_count": state.get("resume_count", 0),
            "total_bars": state.get("total_bars_evaluated", 0),
            "last_ts": state.get("last_timestamp", ""),
        }
    }

    # Check for generated charts
    for f in out_path.glob("forward_chart_*.png"):
        payload["charts"].append(f.name)

    return _sanitize(payload)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_forward_report_md(payload: Dict[str, Any]) -> str:
    """
    Render the forward evaluation report payload as a Markdown document.

    Parameters
    ----------
    payload:
        Dict returned by :func:`build_forward_report`.

    Returns
    -------
    str
        Full Markdown text.
    """
    sid = payload.get("session_id", "—")
    eval_start = payload.get("eval_start") or "—"
    eval_end = payload.get("eval_end") or "—"
    created = payload.get("created_at") or "—"

    lines = [
        f"# Forward Evaluation Report",
        "",
        f"- **Session ID:** `{sid}`",
        f"- **Mode:** {payload.get('mode', 'forward_paper')}",
        f"- **Created At:** {created}",
        "",
        "### Session Bounds",
        f"- **Bars Fetched:** {payload.get('warmup', {}).get('bars_fetched', '—')}",
        f"- **Warmup Bars Skipped:** {payload.get('warmup', {}).get('warmup_bars', '—')}",
        f"- **Bars Evaluated (Last Segment):** {payload.get('warmup', {}).get('bars_evaluated', '—')}",
        "",
    ]

    # --- Session Continuity ---
    cont = payload.get("continuity", {})
    if cont.get("is_resumed") or cont.get("resume_count", 0) > 0:
        lines += [
            "## Session Continuity",
            "",
            f"- **Session Type:** Resumed (Count: {cont.get('resume_count')})",
            f"- **Original Start:** {cont.get('original_start', '—')}",
            f"- **Latest Evaluation End:** {cont.get('latest_update', '—')}",
            f"- **Total Bars Processed:** {cont.get('total_bars', '—')}",
            f"- **Last Record Timestamp:** `{cont.get('last_ts', '—')}`",
            "",
        ]

    # --- Candidate ---
    candidate = payload.get("candidate", {})
    if candidate:
        lines += [
            "## Candidate",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Strategy | `{candidate.get('strategy_name', 'N/A')}` |",
            f"| Source Run | `{candidate.get('source_run_id', 'N/A')}` |",
            f"| Selection Metric | {candidate.get('selection_metric', 'N/A')} |",
            f"| Selection Value | {_fmt(candidate.get('selection_value'), '.4f')} |",
            f"| Ticker | {candidate.get('ticker') or candidate.get('params', {}).get('ticker', 'N/A')} |",
            f"| Fee Rate | {_fmt(candidate.get('fee_rate'), '.3%')} |",
            f"| Slippage | {_fmt(candidate.get('slippage_bps'), '.1f')} bps |",
            "",
        ]
        params = candidate.get("params", {})
        if params:
            lines += ["### Strategy Parameters", "", "| Param | Value |", "|-------|-------|"]
            for k, v in params.items():
                lines.append(f"| `{k}` | {v} |")
            lines.append("")

    # --- Portfolio Summary ---
    ps = payload.get("portfolio_state", {})
    summary = payload.get("summary", {})
    lines += [
        "## Portfolio Summary",
        "",
        f"- **Forward Period:** {eval_start} → {eval_end}",
        f"- **Starting Cash:** {_fmt(payload.get('performance', {}).get('starting_cash'), ',.2f')}",
        f"- **Ending Equity:** {_fmt(payload.get('performance', {}).get('ending_equity'), ',.2f')}",
        f"- **Realized PnL:** {_fmt(payload.get('performance', {}).get('realized_pnl'), ',.2f')}",
        f"- **Unrealized PnL:** {_fmt(payload.get('performance', {}).get('unrealized_pnl'), ',.2f')}",
        f"- **Total Return:** {_fmt(summary.get('total_return'), '.2%')}",
        f"- **Max Drawdown:** {_fmt(summary.get('max_drawdown'), '.2%')}",
        f"- **Annualised Volatility:** {_fmt(summary.get('annualized_volatility'), '.2%')}",
        f"- **Total Fees Paid:** {_fmt(summary.get('total_fees'), ',.4f')}",
        f"- **Open Position:** {'YES' if ps.get('has_open_position') else 'NO'}",
        "",
    ]

    # --- Open Position ---
    if ps.get("has_open_position"):
        lines += [
            "## Open Position",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Quantity | {ps.get('open_position_qty', 0.0):.6f} |",
            f"| Entry Price | {_fmt(ps.get('open_position_entry_price'), ',.4f')} |",
            f"| Mark Price | {_fmt(ps.get('open_position_mark_price'), ',.4f')} |",
            f"| Market Value | {_fmt(ps.get('open_position_market_value'), ',.2f')} |",
            f"| Unrealized PnL | {_fmt(ps.get('unrealized_pnl'), ',.2f')} |",
            "",
        ]

    # --- Closed Trade Summary ---
    # Trade summary remains based on closed round-trips
    n_trades = summary.get("n_trades", 0)
    lines += [
        "## Closed Trade Summary",
        "",
        "> [!NOTE]",
        "> The following metrics are calculated only from closed round-trip trades.",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Round-trips | {n_trades if n_trades is not None else 'N/A'} |",
        f"| Win Rate | {_fmt(summary.get('win_rate'), '.1%')} |",
        f"| Expectancy (PnL) | {_fmt(summary.get('expectancy'), '.4f')} |",
        f"| Best Trade PnL | {_fmt(summary.get('best_trade_pnl'), '.4f')} |",
        f"| Worst Trade PnL | {_fmt(summary.get('worst_trade_pnl'), '.4f')} |",
        "",
    ]

    # --- Charts ---
    charts = payload.get("charts", [])
    lines += ["## Charts", ""]
    if charts:
        for c in sorted(charts):
            lines.append(f"- `{c}`")
    else:
        lines.append("_No charts generated._")
    lines.append("")

    # --- Artifacts ---
    artifacts = payload.get("artifacts", [])
    lines += ["## Artifacts", ""]
    if artifacts:
        df_a = pd.DataFrame(artifacts)
        lines.append(df_a.to_markdown(index=False))
    else:
        lines.append("_No artifacts found._")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def generate_forward_charts(out_dir: str | Path) -> List[str]:
    """
    Generate standard charts for a forward evaluation session.

    Parameters
    ----------
    out_dir:
        Directory containing forward evaluation artifacts.

    Returns
    -------
    list[str]
        Paths to generated PNG files.
    """
    out_path = Path(out_dir)
    eq_path = out_path / "forward_equity_curve.csv"
    if not eq_path.exists():
        return []

    try:
        df_eq = pd.read_csv(eq_path)
        if "equity" not in df_eq.columns or "timestamp" not in df_eq.columns:
            return []
        df_eq["timestamp"] = pd.to_datetime(df_eq["timestamp"])
        equity = df_eq.set_index("timestamp")["equity"]

        generated = []
        p1 = plot_equity_curve(equity, str(out_path / "forward_chart_equity.png"))
        if p1: generated.append(p1)

        p2 = plot_drawdown(equity, str(out_path / "forward_chart_drawdown.png"))
        if p2: generated.append(p2)

        return generated
    except Exception as exc:
        import warnings
        warnings.warn(f"[forward_report] Failed to generate charts: {exc}")
        return []


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_forward_report(out_dir: str | Path) -> Tuple[str, str]:
    """
    Build and write the forward evaluation report to *out_dir*.

    Generates:
    - ``forward_report.json`` (strict JSON)
    - ``forward_report.md``

    Parameters
    ----------
    out_dir:
        Directory containing forward evaluation artifacts.

    Returns
    -------
    tuple[str, str]
        Paths to (json_path, md_path).
    """
    out_path = Path(out_dir)
    
    # Generate charts first so they are discovered by build_forward_report
    generate_forward_charts(out_path)
    
    payload = build_forward_report(out_path)

    json_path = out_path / "forward_report.json"
    md_path = out_path / "forward_report.md"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, allow_nan=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_forward_report_md(payload))

    return str(json_path), str(md_path)
