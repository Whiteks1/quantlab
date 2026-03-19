"""
charts.py – Stage K: chart generation for QuantLab run analysis.

All chart functions accept a matplotlib-compatible data source, save the
output to a file, and return the output path (str).  They degrade
gracefully when data is insufficient — returning None instead of crashing.

Functions
---------
plot_equity_curve(equity, out_path)          -> str | None
plot_drawdown(equity, out_path)              -> str | None
plot_trade_distribution(rt, out_path)        -> str | None
plot_rolling_performance(equity, out_path)   -> str | None
plot_monthly_returns(equity, out_path)       -> str | None
generate_charts(run_dir, out_dir)            -> list[str]
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

# matplotlib in non-interactive mode (no display required)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def plot_basic_equity(
    bt: pd.DataFrame,
    out_path: str,
    ticker: str,
    strategy_name: str
) -> None:
    """
    Simple equity curve plot used for legacy reports.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(bt.index, bt["equity"], label="Equity (net)")
    plt.title(f"Equity Curve — {ticker} — {strategy_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_price_signals(
    df: pd.DataFrame,
    signals: pd.Series,
    out_path: str,
    ticker: str,
    strategy_name: str
) -> None:
    """
    Price + BUY/SELL signals plot.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["close"], label="Close")
    if "ma20" in df.columns:
        plt.plot(df.index, df["ma20"], label="MA20", linestyle="--")

    buy_idx = df.index[signals == 1]
    sell_idx = df.index[signals == -1]
    plt.scatter(buy_idx, df.loc[buy_idx, "close"], marker="^", s=100, label="BUY")
    plt.scatter(sell_idx, df.loc[sell_idx, "close"], marker="v", s=100, label="SELL")

    plt.title(f"Price + Signals — {ticker} — {strategy_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

_STYLE = {
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0",
    "axes.titlecolor": "#ffffff",
    "xtick.color": "#e0e0e0",
    "ytick.color": "#e0e0e0",
    "grid.color": "#2d4059",
    "grid.alpha": 0.5,
    "text.color": "#e0e0e0",
}

_EQUITY_COLOR = "#4fc3f7"
_DD_COLOR = "#ef5350"
_WIN_COLOR = "#66bb6a"
_LOSS_COLOR = "#ef5350"
_ROLL_COLOR = "#ffa726"


def _apply_style(ax: plt.Axes) -> None:
    ax.grid(True, linewidth=0.5, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _savefig(fig: plt.Figure, out_path: str) -> str:
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Individual chart functions
# ---------------------------------------------------------------------------

def plot_equity_curve(equity: pd.Series, out_path: str) -> Optional[str]:
    """
    Plot a normalised equity curve.

    Parameters
    ----------
    equity:
        Normalised equity series (starts at 1.0).
    out_path:
        Absolute path where the PNG is saved.

    Returns
    -------
    str | None
        Path to the saved image, or None if the chart could not be produced.
    """
    try:
        if equity is None or len(equity) < 2:
            return None

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(equity.index, equity.values, color=_EQUITY_COLOR, linewidth=1.8, label="Equity")
            ax.fill_between(equity.index, 1.0, equity.values,
                            where=equity.values >= 1.0, alpha=0.15, color=_WIN_COLOR)
            ax.fill_between(equity.index, 1.0, equity.values,
                            where=equity.values < 1.0, alpha=0.20, color=_DD_COLOR)
            ax.axhline(1.0, color="#ffffff", linewidth=0.8, linestyle="--", alpha=0.6)
            ax.set_title("Equity Curve", fontsize=14, fontweight="bold")
            ax.set_xlabel("Date / Period")
            ax.set_ylabel("Normalised Equity")
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
            ax.legend(loc="upper left")
            _apply_style(ax)
            return _savefig(fig, out_path)
    except Exception as exc:
        warnings.warn(f"[charts] plot_equity_curve failed: {exc}")
        plt.close("all")
        return None


def plot_drawdown(equity: pd.Series, out_path: str) -> Optional[str]:
    """
    Plot the drawdown series over time.

    Returns
    -------
    str | None
    """
    try:
        if equity is None or len(equity) < 2:
            return None

        peak = equity.cummax()
        dd = (equity / peak) - 1.0

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.fill_between(dd.index, 0, dd.values, color=_DD_COLOR, alpha=0.7, label="Drawdown")
            ax.plot(dd.index, dd.values, color=_DD_COLOR, linewidth=1.2)
            ax.axhline(0, color="#ffffff", linewidth=0.6, linestyle="--", alpha=0.5)
            ax.set_title("Drawdown", fontsize=14, fontweight="bold")
            ax.set_xlabel("Date / Period")
            ax.set_ylabel("Drawdown")
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=1))
            ax.legend(loc="lower left")
            _apply_style(ax)
            return _savefig(fig, out_path)
    except Exception as exc:
        warnings.warn(f"[charts] plot_drawdown failed: {exc}")
        plt.close("all")
        return None


def plot_trade_distribution(rt: pd.DataFrame, out_path: str) -> Optional[str]:
    """
    Plot a histogram of trade PnL distribution.

    Returns
    -------
    str | None
    """
    try:
        if rt is None or rt.empty or "net_pnl" not in rt.columns:
            return None
        pnl = rt["net_pnl"].dropna()
        if len(pnl) < 2:
            return None

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(10, 5))
            bins = min(30, max(10, len(pnl) // 2))
            wins = pnl[pnl >= 0]
            losses = pnl[pnl < 0]
            ax.hist(losses.values, bins=bins // 2, color=_LOSS_COLOR, alpha=0.75, label="Losses", density=False)
            ax.hist(wins.values, bins=bins // 2, color=_WIN_COLOR, alpha=0.75, label="Wins", density=False)
            ax.axvline(0, color="#ffffff", linewidth=0.8, linestyle="--", alpha=0.7)
            ax.axvline(float(pnl.mean()), color=_ROLL_COLOR, linewidth=1.5,
                       linestyle=":", label=f"Mean: {pnl.mean():.2f}")
            ax.set_title("Trade PnL Distribution", fontsize=14, fontweight="bold")
            ax.set_xlabel("Net PnL")
            ax.set_ylabel("Count")
            ax.legend()
            _apply_style(ax)
            return _savefig(fig, out_path)
    except Exception as exc:
        warnings.warn(f"[charts] plot_trade_distribution failed: {exc}")
        plt.close("all")
        return None


def plot_rolling_performance(equity: pd.Series, out_path: str, window: int = 60) -> Optional[str]:
    """
    Plot a rolling Sharpe ratio.

    Returns
    -------
    str | None
    """
    try:
        if equity is None or len(equity) < window + 10:
            return None

        daily_ret = equity.pct_change().dropna()
        rolling_sharpe = (
            daily_ret.rolling(window).mean()
            / (daily_ret.rolling(window).std() + 1e-12)
            * np.sqrt(252)
        ).dropna()

        if len(rolling_sharpe) < 2:
            return None

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(rolling_sharpe.index, rolling_sharpe.values,
                    color=_ROLL_COLOR, linewidth=1.5, label=f"{window}d Rolling Sharpe")
            ax.axhline(0, color="#ffffff", linewidth=0.6, linestyle="--", alpha=0.5)
            ax.axhline(1, color=_WIN_COLOR, linewidth=0.8, linestyle=":", alpha=0.6)
            ax.set_title(f"Rolling Sharpe ({window}-day)", fontsize=14, fontweight="bold")
            ax.set_xlabel("Date / Period")
            ax.set_ylabel("Sharpe (ann.)")
            ax.legend(loc="upper left")
            _apply_style(ax)
            return _savefig(fig, out_path)
    except Exception as exc:
        warnings.warn(f"[charts] plot_rolling_performance failed: {exc}")
        plt.close("all")
        return None


def plot_monthly_returns(equity: pd.Series, out_path: str) -> Optional[str]:
    """
    Plot a monthly returns bar chart.

    Returns
    -------
    str | None
    """
    try:
        if equity is None or len(equity) < 20:
            return None

        eq = equity.copy()
        if not isinstance(eq.index, pd.DatetimeIndex):
            try:
                eq.index = pd.to_datetime(eq.index)
            except Exception:
                return None

        monthly = eq.resample("ME").last().pct_change().dropna()
        if len(monthly) < 2:
            return None

        labels = [str(ts.to_period("M")) for ts in monthly.index]
        values = monthly.values
        colors = [_WIN_COLOR if v >= 0 else _LOSS_COLOR for v in values]

        with plt.rc_context(_STYLE):
            fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.5), 5))
            ax.bar(range(len(labels)), values, color=colors, alpha=0.85, width=0.7)
            ax.axhline(0, color="#ffffff", linewidth=0.6, linestyle="--", alpha=0.5)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=1))
            ax.set_title("Monthly Returns", fontsize=14, fontweight="bold")
            ax.set_ylabel("Return")
            _apply_style(ax)
            return _savefig(fig, out_path)
    except Exception as exc:
        warnings.warn(f"[charts] plot_monthly_returns failed: {exc}")
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def generate_charts(run_dir: str | Path, out_dir: Optional[str | Path] = None) -> List[str]:
    """
    Generate all available charts for a run directory.

    Loads equity and round-trip trade data from the run's ``trades.csv``
    (if present), then attempts each chart function, collecting paths of
    successfully created images.

    Parameters
    ----------
    run_dir:
        Path to a completed run directory.
    out_dir:
        Directory where chart PNGs are saved.  Defaults to ``run_dir``.

    Returns
    -------
    list[str]
        Paths of generated chart files (may be empty if no data available).
    """
    run_path = Path(run_dir)
    out = Path(out_dir) if out_dir else run_path
    out.mkdir(parents=True, exist_ok=True)

    equity: Optional[pd.Series] = None
    rt: Optional[pd.DataFrame] = None

    # Load equity using the full priority chain (oos_equity_timeseries → curve → trades)
    try:
        from quantlab.reporting.advanced_metrics import _load_equity_from_artifacts
        equity = _load_equity_from_artifacts(run_path)
    except Exception as exc:
        warnings.warn(f"[charts] Could not load equity: {exc}")

    # Load round-trip trades only from trades.csv (paper-broker output)
    trades_path = run_path / "trades.csv"
    if trades_path.exists():
        try:
            from quantlab.reporting.trade_analytics import load_trades_csv, compute_round_trips
            raw = load_trades_csv(str(trades_path))
            rt = compute_round_trips(raw)
        except Exception as exc:
            warnings.warn(f"[charts] Could not load trades.csv: {exc}")


    generated: List[str] = []

    def _try(fn, *args) -> None:
        result = fn(*args)
        if result is not None:
            generated.append(result)

    _try(plot_equity_curve, equity, str(out / "chart_equity.png"))
    _try(plot_drawdown, equity, str(out / "chart_drawdown.png"))
    _try(plot_trade_distribution, rt, str(out / "chart_trade_dist.png"))
    _try(plot_rolling_performance, equity, str(out / "chart_rolling_sharpe.png"))
    _try(plot_monthly_returns, equity, str(out / "chart_monthly_returns.png"))

    return generated
