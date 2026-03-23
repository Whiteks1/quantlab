"""
advanced_metrics.py – Stage K: advanced run analytics for QuantLab.

Computes richer performance metrics from run artifacts (trades.csv,
equity series, etc.) and returns a unified payload suitable for JSON
serialisation and Markdown rendering.

Numerical guard policy (Stage K.3)
------------------------------------
- ``_MIN_DAYS_FOR_RATIO``   : minimum equity points needed to compute Sharpe /
  Sortino.  Below this threshold those metrics return ``None``.
- ``_SORTINO_DOWNSIDE_FLOOR``: minimum annualised downside-volatility required
  to trust Sortino.  When all returns are positive (or downside std is
  near-zero), Sortino is ``None`` rather than an absurdly large number.
- ``_MIN_DD_FOR_CALMAR``    : Calmar is ``None`` when |max_drawdown| < 0.5 %
  because a near-zero denominator makes the ratio uninformative.
- ``_MIN_MONTHS``           : monthly summary metrics require at least this
  many complete monthly periods; otherwise an ``insufficient_data`` flag is
  returned.

Functions
---------
compute_equity_metrics(equity)       -> dict
compute_drawdown_metrics(equity)     -> dict
compute_trade_distribution_metrics(rt) -> dict
compute_time_window_metrics(equity)  -> dict
build_advanced_metrics(run_dir)      -> dict
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from quantlab.runs.artifacts import CANONICAL_REPORT_FILENAME, LEGACY_REPORT_FILENAMES, load_json_with_fallback


# ---------------------------------------------------------------------------
# Numerical-guard constants  (Stage K.3)
# ---------------------------------------------------------------------------

#: Minimum equity data-points required before computing Sharpe / Sortino.
_MIN_DAYS_FOR_RATIO: int = 20

#: Minimum annualised downside volatility required to treat Sortino as valid.
#: Below this the denominator is essentially zero and the ratio is misleading.
_SORTINO_DOWNSIDE_FLOOR: float = 1e-4   # 0.01 % annualised

#: Minimum |max_drawdown| to report Calmar ratio (0.5 %).
_MIN_DD_FOR_CALMAR: float = 0.005

#: Minimum number of complete monthly periods for monthly stats to be useful.
_MIN_MONTHS: int = 3


# ---------------------------------------------------------------------------
# JSON sanitisation (shared pattern)
# ---------------------------------------------------------------------------

def _san(v: Any) -> Any:
    """Convert non-finite float to None for strict JSON."""
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _sanitize(obj: Any) -> Any:
    """Recursively sanitise a nested structure."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# ---------------------------------------------------------------------------
# Individual metric groups
# ---------------------------------------------------------------------------

def compute_equity_metrics(equity: pd.Series) -> Dict[str, Any]:
    """
    Compute return and risk metrics from an equity curve.

    Numerical guard policy (Stage K.3)
    ------------------------------------
    - Sortino is ``None`` when fewer than ``_MIN_DAYS_FOR_RATIO`` data-points
      are available, or when the annualised downside volatility is below
      ``_SORTINO_DOWNSIDE_FLOOR`` (all or nearly all returns are positive).
    - Sharpe falls back to ``None`` for very short series as well.

    Parameters
    ----------
    equity:
        Normalised equity series (starting at 1.0) indexed by date or int.
        Values represent the portfolio value as a fraction of initial capital.

    Returns
    -------
    dict
        Keys: total_return, cagr, annualized_volatility, sharpe, sortino,
        equity_start, equity_end, n_days.
        ``sharpe`` and ``sortino`` may be ``None`` for short/flat series.
    """
    result: Dict[str, Any] = {}
    if equity is None or len(equity) < 2:
        return result

    eq = equity.dropna()
    if len(eq) < 2:
        return result

    n_days = len(eq)
    years = max(n_days / 252.0, 1 / 252.0)

    start_val = float(eq.iloc[0])
    end_val = float(eq.iloc[-1])

    total_return = (end_val / start_val) - 1.0
    cagr = (end_val / start_val) ** (1.0 / years) - 1.0 if years > 0 else 0.0

    daily_ret = eq.pct_change().dropna()
    ann_vol = float(daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 1 else 0.0

    # --- Sharpe (needs >= _MIN_DAYS_FOR_RATIO) ---
    if len(daily_ret) >= _MIN_DAYS_FOR_RATIO and daily_ret.std() > 0:
        sharpe: Optional[float] = _san(
            float(np.sqrt(252) * daily_ret.mean() / daily_ret.std())
        )
    else:
        sharpe = None

    # --- Sortino (needs >= _MIN_DAYS_FOR_RATIO AND meaningful downside vol) ---
    sortino: Optional[float] = None
    if len(daily_ret) >= _MIN_DAYS_FOR_RATIO:
        downside = daily_ret[daily_ret < 0]
        if len(downside) > 1:
            downside_vol = float(downside.std() * np.sqrt(252))
            if downside_vol >= _SORTINO_DOWNSIDE_FLOOR:
                sortino = _san(
                    float(np.sqrt(252) * daily_ret.mean() / downside_vol)
                )
            # else: downside vol is negligible → leave sortino as None
        # else: fewer than 2 negative returns → not enough data for sortino

    result.update({
        "equity_start": _san(start_val),
        "equity_end": _san(end_val),
        "n_days": n_days,
        "total_return": _san(total_return),
        "cagr": _san(cagr),
        "annualized_volatility": _san(ann_vol),
        "sharpe": sharpe,
        "sortino": sortino,
    })
    return result


def compute_drawdown_metrics(equity: pd.Series) -> Dict[str, Any]:
    """
    Compute drawdown-related metrics from an equity curve.

    Numerical guard policy
    ----------------------
    - Calmar ratio is suppressed when |max_drawdown| < ``_MIN_DD_FOR_CALMAR``
      (0.5 %) because tiny drawdowns make Calmar uninformative.

    Parameters
    ----------
    equity:
        Normalised equity series.

    Returns
    -------
    dict  Keys: max_drawdown, avg_drawdown, calmar, longest_dd_days,
          current_drawdown, n_drawdown_periods.  Calmar may be ``None``.
    """
    if equity is None or len(equity) < 2:
        return {}

    eq = equity.dropna()
    peak = eq.cummax()
    dd = (eq / peak) - 1.0

    max_dd = float(dd.min())
    avg_dd = float(dd[dd < 0].mean()) if (dd < 0).any() else 0.0
    current_dd = float(dd.iloc[-1])

    # Drawdown duration: count of consecutive negative drawdown periods
    in_dd = (dd < -1e-9).astype(int)
    run_lengths: list[int] = []
    cur = 0
    for v in in_dd:
        if v:
            cur += 1
        else:
            if cur > 0:
                run_lengths.append(cur)
            cur = 0
    if cur > 0:
        run_lengths.append(cur)

    longest_dd = max(run_lengths) if run_lengths else 0
    n_dd_periods = len(run_lengths)

    # Calmar: suppress when drawdown is trivially small
    n_days = len(eq)
    years = n_days / 252.0
    end_val = float(eq.iloc[-1])
    start_val = float(eq.iloc[0])
    if years > 0 and abs(max_dd) >= _MIN_DD_FOR_CALMAR:
        cagr = (end_val / start_val) ** (1.0 / years) - 1.0
        calmar: Optional[float] = _san(cagr / abs(max_dd))
    else:
        calmar = None   # drawdown too small — Calmar not informative

    return {
        "max_drawdown": _san(max_dd),
        "avg_drawdown": _san(avg_dd),
        "current_drawdown": _san(current_dd),
        "longest_dd_days": longest_dd,
        "n_drawdown_periods": n_dd_periods,
        "calmar": calmar,
    }


def compute_trade_distribution_metrics(rt: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute detailed trade-level distribution metrics.

    Parameters
    ----------
    rt:
        Round-trip trades DataFrame as produced by
        ``trade_analytics.compute_round_trips``.

    Returns
    -------
    dict
        Keys: n_trades, avg_return, median_return, best_trade, worst_trade,
        pnl_std, top3_pnl_share, expectancy, win_rate, …
    """
    if rt is None or rt.empty:
        return {"n_trades": 0}

    pnl = rt["net_pnl"].dropna()
    ret = rt["return_pct"].dropna() if "return_pct" in rt.columns else pd.Series(dtype=float)
    n = len(pnl)

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    profit_factor = (wins.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() < 0 else None

    # PnL concentration: top-3 positive trades / total gross profit
    top3_pnl_share: Optional[float] = None
    if len(wins) >= 3:
        top3 = wins.nlargest(3).sum()
        top3_pnl_share = float(top3 / wins.sum()) if wins.sum() > 0 else None

    return {
        "n_trades": n,
        "avg_return": _san(float(ret.mean())) if len(ret) else None,
        "median_return": _san(float(ret.median())) if len(ret) else None,
        "best_trade_pnl": _san(float(pnl.max())),
        "worst_trade_pnl": _san(float(pnl.min())),
        "pnl_std": _san(float(pnl.std())) if n > 1 else None,
        "expectancy": _san(float(pnl.mean())),
        "win_rate": _san(float((pnl > 0).mean())),
        "profit_factor": _san(float(profit_factor)) if profit_factor is not None else None,
        "avg_holding_days": _san(float(rt["holding_days"].mean())) if "holding_days" in rt.columns else None,
        "top3_pnl_share": _san(top3_pnl_share),
        "max_consecutive_losses": _consecutive_count(pnl < 0),
        "max_consecutive_wins": _consecutive_count(pnl > 0),
    }


def _consecutive_count(mask: pd.Series) -> int:
    """Return the maximum run of consecutive True values in *mask*."""
    best = 0
    cur = 0
    for v in mask:
        if v:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def compute_time_window_metrics(equity: pd.Series) -> Dict[str, Any]:
    """
    Compute monthly / quarterly performance summaries from an equity curve.

    Guard policy (Stage K.3)
    -------------------------
    - Returns ``{}`` when fewer than 10 data-points are available (cannot
      even form a single month's worth of bars).
    - When fewer than ``_MIN_MONTHS`` full monthly periods exist, returns a
      partial dict with ``insufficient_data=True`` and a ``note`` field
      explaining the limitation — rather than silently returning ``{}``.
    - Flat monthly periods (return == 0) are included.

    Parameters
    ----------
    equity:
        Normalised equity series with a datetime index (or coercible to one).

    Returns
    -------
    dict
        Keys: n_months, monthly_returns (list), best_month, worst_month,
        positive_months_pct.
        May also contain: insufficient_data (bool), note (str),
        min_months_required (int).
    """
    if equity is None or len(equity) < 10:
        return {}

    eq = equity.copy()
    if not isinstance(eq.index, pd.DatetimeIndex):
        try:
            eq.index = pd.to_datetime(eq.index)
        except Exception:
            return {}

    try:
        monthly = eq.resample("ME").last()
        monthly_ret = monthly.pct_change().dropna()
    except Exception:
        return {}

    n_months = len(monthly_ret)
    if n_months < _MIN_MONTHS:
        # Too few periods — report the situation honestly
        return {
            "n_months": n_months,
            "min_months_required": _MIN_MONTHS,
            "monthly_returns": [],
            "insufficient_data": True,
            "note": (
                f"Only {n_months} complete monthly period(s) available; "
                f"at least {_MIN_MONTHS} are needed for reliable monthly statistics."
            ),
        }

    records = [
        {"month": str(ts.to_period("M")), "return": _san(float(r))}
        for ts, r in monthly_ret.items()
    ]

    best_month = _san(float(monthly_ret.max()))
    worst_month = _san(float(monthly_ret.min()))
    positive_pct = _san(float((monthly_ret > 0).mean()))

    return {
        "n_months": n_months,
        "monthly_returns": records,
        "best_month": best_month,
        "worst_month": worst_month,
        "positive_months_pct": positive_pct,
    }


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def _load_equity_from_artifacts(run_path: Path) -> Optional[pd.Series]:
    """
    Try to reconstruct a normalised equity series from available artifacts.

    Resolution order (newer / richer artifacts preferred):
    1. ``oos_equity_timeseries.csv``  — per-bar stitched OOS (Stage K.2)
    2. ``oos_equity_curve.csv``       — per-split cumulative (Stage K.1)
    3. ``equity_curve.csv``           — generic persisted equity
    4. ``trades.csv`` → ``equity_after``  — existing paper-broker log
    """
    # 1) Per-bar OOS timeseries (Stage K.2 — highest fidelity)
    oos_ts_path = run_path / "oos_equity_timeseries.csv"
    if oos_ts_path.exists():
        try:
            df = pd.read_csv(oos_ts_path)
            if "equity" in df.columns and len(df) >= 2:
                eq = df["equity"].dropna()
                if "timestamp" in df.columns:
                    eq.index = pd.to_datetime(df["timestamp"], errors="coerce")
                return eq
        except Exception:
            pass

    # 2) Per-split cumulative equity (Stage K.1)
    oos_eq_path = run_path / "oos_equity_curve.csv"
    if oos_eq_path.exists():
        try:
            df = pd.read_csv(oos_eq_path)
            if "cumulative_equity" in df.columns and len(df) >= 2:
                eq = df["cumulative_equity"].dropna()
                eq = pd.concat([pd.Series([1.0]), eq.reset_index(drop=True)], ignore_index=True)
                return eq
        except Exception:
            pass

    # 3) Generic equity_curve.csv
    eq_path = run_path / "equity_curve.csv"
    if eq_path.exists():
        try:
            df = pd.read_csv(eq_path)
            col = next((c for c in ("equity", "cumulative_equity", "equity_after") if c in df.columns), None)
            if col and len(df) >= 2:
                eq = df[col].dropna()
                eq = eq / eq.iloc[0]
                if "timestamp" in df.columns or "date" in df.columns:
                    ts_col = "timestamp" if "timestamp" in df.columns else "date"
                    eq.index = pd.to_datetime(df[ts_col], errors="coerce")
                return eq
        except Exception:
            pass

    # 4) trades.csv -> equity_after (legacy)
    trades_path = run_path / "trades.csv"
    if trades_path.exists():
        try:
            df = pd.read_csv(trades_path)
            if "equity_after" in df.columns and len(df) > 1:
                eq = df["equity_after"].dropna()
                eq = eq / eq.iloc[0]
                if "timestamp" in df.columns:
                    eq.index = pd.to_datetime(df["timestamp"], errors="coerce")
                return eq
        except Exception:
            pass

    return None


def _load_round_trips(run_path: Path) -> Optional[pd.DataFrame]:
    """Load round-trip trades if trades.csv is present in the run dir."""
    trades_path = run_path / "trades.csv"
    if not trades_path.exists():
        return None
    try:
        from quantlab.reporting.trade_analytics import load_trades_csv, compute_round_trips
        raw = load_trades_csv(str(trades_path))
        return compute_round_trips(raw)
    except Exception as exc:
        warnings.warn(f"[advanced_metrics] Could not load round trips from {trades_path}: {exc}")
        return None


def _load_run_report(run_path: Path) -> Dict[str, Any]:
    """Load report.json if available, else fall back to legacy report artifacts."""
    try:
        payload, _ = load_json_with_fallback(
            run_path,
            CANONICAL_REPORT_FILENAME,
            *LEGACY_REPORT_FILENAMES,
        )
        return payload
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Master builder
# ---------------------------------------------------------------------------

def build_advanced_metrics(run_dir: str | Path) -> Dict[str, Any]:
    """
    Build a comprehensive advanced metrics payload for a run directory.

    Loads whatever artifacts are available (trades.csv, report.json,
    metadata.json) and computes metrics gracefully, skipping unavailable
    analytics rather than crashing.

    Parameters
    ----------
    run_dir:
        Path to a completed run directory.

    Returns
    -------
    dict
        Sanitised dict ready for ``json.dump(..., allow_nan=False)``.
        Unreliable / unsupported metrics are represented as ``None``
        rather than extreme or non-finite values.
    """
    run_path = Path(run_dir)
    report = _load_run_report(run_path)
    header = report.get("header", {})

    payload: Dict[str, Any] = {
        "run_id": header.get("run_id") or run_path.name,
        "mode": header.get("mode"),
        "created_at": header.get("created_at"),
    }

    # --- Equity metrics from trades.csv (if present) ---
    equity = _load_equity_from_artifacts(run_path)
    if equity is not None and len(equity) >= 2:
        payload["equity_metrics"] = compute_equity_metrics(equity)
        payload["drawdown_metrics"] = compute_drawdown_metrics(equity)
        payload["time_window_metrics"] = compute_time_window_metrics(equity)
    else:
        payload["equity_metrics"] = {}
        payload["drawdown_metrics"] = {}
        payload["time_window_metrics"] = {}

    # --- Trade distribution metrics ---
    rt = _load_round_trips(run_path)
    if rt is not None and not rt.empty:
        payload["trade_distribution"] = compute_trade_distribution_metrics(rt)
    else:
        payload["trade_distribution"] = {"n_trades": 0}

    # --- Summary from report.json (top result row) ---
    run_results = report.get("results", report.get("oos_leaderboard", []))
    payload["top_result_summary"] = run_results[0] if run_results else {}

    return _sanitize(payload)
