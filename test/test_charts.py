"""Tests for charts.py (Stage K)."""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from quantlab.reporting.charts import (
    plot_equity_curve,
    plot_drawdown,
    plot_trade_distribution,
    plot_rolling_performance,
    plot_monthly_returns,
    generate_charts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_equity(n: int = 200, seed: int = 7) -> pd.Series:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.001, 0.015, n)
    eq = pd.Series(
        np.cumprod(1 + ret),
        index=pd.date_range("2023-01-01", periods=n, freq="B"),
    )
    return eq / eq.iloc[0]


def _make_rt(n: int = 15, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    pnl = rng.normal(10, 40, n)
    return pd.DataFrame({
        "net_pnl": pnl,
        "return_pct": pnl / 1000,
        "holding_days": rng.integers(1, 15, n),
        "is_loss": pnl < 0,
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_plot_equity_curve_creates_file(tmp_path):
    equity = _make_equity(100)
    out = str(tmp_path / "equity.png")
    result = plot_equity_curve(equity, out)
    assert result is not None
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_plot_equity_curve_returns_none_on_insufficient_data(tmp_path):
    out = str(tmp_path / "eq.png")
    assert plot_equity_curve(None, out) is None
    assert plot_equity_curve(pd.Series([1.0]), out) is None


def test_plot_drawdown_creates_file(tmp_path):
    equity = _make_equity(100)
    out = str(tmp_path / "dd.png")
    result = plot_drawdown(equity, out)
    assert result is not None
    assert Path(result).exists()


def test_plot_trade_distribution_creates_file(tmp_path):
    rt = _make_rt(20)
    out = str(tmp_path / "dist.png")
    result = plot_trade_distribution(rt, out)
    assert result is not None
    assert Path(result).exists()


def test_plot_trade_distribution_none_on_empty(tmp_path):
    out = str(tmp_path / "dist2.png")
    assert plot_trade_distribution(pd.DataFrame(), out) is None


def test_plot_rolling_performance_creates_file(tmp_path):
    equity = _make_equity(200)
    out = str(tmp_path / "roll.png")
    result = plot_rolling_performance(equity, out, window=30)
    assert result is not None
    assert Path(result).exists()


def test_plot_rolling_performance_skip_short(tmp_path):
    equity = _make_equity(20)  # shorter than default window + 10
    out = str(tmp_path / "roll2.png")
    result = plot_rolling_performance(equity, out, window=60)
    assert result is None  # not enough data


def test_plot_monthly_returns_creates_file(tmp_path):
    equity = _make_equity(250)
    out = str(tmp_path / "monthly.png")
    result = plot_monthly_returns(equity, out)
    assert result is not None
    assert Path(result).exists()


def test_generate_charts_no_trades_no_crash(tmp_path):
    """generate_charts must return empty list (not crash) when no trades.csv."""
    run_dir = tmp_path / "run_no_trades"
    run_dir.mkdir()
    # Write minimal meta to make it look like a run dir
    (run_dir / "meta.json").write_text(json.dumps({"run_id": "x", "mode": "grid"}))

    charts = generate_charts(run_dir, out_dir=tmp_path / "charts")
    assert isinstance(charts, list)
    # No files created since no source data
    assert len(charts) == 0
