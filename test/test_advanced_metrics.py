"""Tests for advanced_metrics.py (Stage K)."""

import json
import math
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from quantlab.reporting.advanced_metrics import (
    compute_equity_metrics,
    compute_drawdown_metrics,
    compute_trade_distribution_metrics,
    compute_time_window_metrics,
    build_advanced_metrics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_equity(n: int = 100, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    daily_ret = rng.normal(0.0005, 0.015, n)
    equity = pd.Series(
        np.cumprod(1 + daily_ret),
        index=pd.date_range("2023-01-01", periods=n, freq="B"),
    )
    return equity / equity.iloc[0]  # normalise to 1.0


def _make_round_trips(n: int = 20, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    net_pnl = rng.normal(5, 30, n)
    return_pct = net_pnl / 1000
    return pd.DataFrame({
        "net_pnl": net_pnl,
        "return_pct": return_pct,
        "holding_days": rng.integers(1, 20, n),
        "is_loss": net_pnl < 0,
    })


def _make_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "test_run"
    run_dir.mkdir()
    report = {
        "header": {
            "run_id": "test_run",
            "mode": "grid",
            "created_at": "2023-01-01T00:00:00",
            "git_commit": "abc",
        },
        "results": [{"sharpe_simple": 1.2, "total_return": 0.15}],
        "config_resolved": {},
    }
    with open(run_dir / "run_report.json", "w") as f:
        json.dump(report, f)
    return run_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_compute_equity_metrics_basic():
    equity = _make_equity(252)
    result = compute_equity_metrics(equity)

    assert "total_return" in result
    assert "cagr" in result
    assert "sharpe" in result
    assert "sortino" in result
    assert "annualized_volatility" in result
    assert result["n_days"] == 252


def test_compute_equity_metrics_empty():
    """Empty or single-point equity must not raise."""
    assert compute_equity_metrics(None) == {}
    assert compute_equity_metrics(pd.Series(dtype=float)) == {}
    assert compute_equity_metrics(pd.Series([1.0])) == {}


def test_compute_drawdown_metrics_basic():
    equity = _make_equity(252)
    result = compute_drawdown_metrics(equity)

    assert "max_drawdown" in result
    assert result["max_drawdown"] <= 0, "max_drawdown must be non-positive"
    assert "longest_dd_days" in result
    assert result["longest_dd_days"] >= 0
    assert "calmar" in result


def test_compute_drawdown_metrics_flat_equity():
    """Flat equity (all 1.0) → zero drawdown, no crash."""
    equity = pd.Series([1.0] * 50, index=pd.date_range("2023-01-01", periods=50, freq="B"))
    result = compute_drawdown_metrics(equity)
    assert result["max_drawdown"] == pytest.approx(0.0, abs=1e-9)


def test_compute_trade_distribution_metrics():
    rt = _make_round_trips(20)
    result = compute_trade_distribution_metrics(rt)

    assert result["n_trades"] == 20
    assert "win_rate" in result
    assert 0.0 <= result["win_rate"] <= 1.0
    assert "expectancy" in result
    assert "best_trade_pnl" in result
    assert "worst_trade_pnl" in result


def test_compute_trade_distribution_empty():
    result = compute_trade_distribution_metrics(pd.DataFrame())
    assert result["n_trades"] == 0


def test_compute_time_window_metrics():
    equity = _make_equity(400)  # >1 year of data
    result = compute_time_window_metrics(equity)

    assert "monthly_returns" in result
    assert len(result["monthly_returns"]) > 0
    assert "best_month" in result
    assert "worst_month" in result
    assert "positive_months_pct" in result
    assert 0.0 <= result["positive_months_pct"] <= 1.0


def test_compute_time_window_metrics_insufficient():
    """Short series → returns empty dict."""
    equity = _make_equity(5)
    assert compute_time_window_metrics(equity) == {}


def test_build_advanced_metrics_no_trades(tmp_path):
    """build_advanced_metrics on a run without trades.csv must not crash."""
    run_dir = _make_run_dir(tmp_path)
    payload = build_advanced_metrics(run_dir)

    assert "run_id" in payload
    assert payload["trade_distribution"]["n_trades"] == 0
    # JSON must be strictly serialisable
    json.dumps(payload, allow_nan=False)


def test_build_advanced_metrics_strict_json(tmp_path):
    """Payload must survive allow_nan=False serialisation even with NaN inputs."""
    run_dir = _make_run_dir(tmp_path)
    payload = build_advanced_metrics(run_dir)
    serialised = json.dumps(payload, allow_nan=False)
    data = json.loads(serialised)
    assert "run_id" in data
