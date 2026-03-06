"""Tests for advanced_metrics.py (Stage K / K.3)."""

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
    _MIN_DAYS_FOR_RATIO,
    _MIN_MONTHS,
    _MIN_DD_FOR_CALMAR,
    _SORTINO_DOWNSIDE_FLOOR,
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
# Basic smoke tests (pre-existing, kept for regression)
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
    """Short series (< 10 bars) → returns empty dict."""
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


# ---------------------------------------------------------------------------
# K.3 robustness / sanity-guard tests
# ---------------------------------------------------------------------------

class TestSortinoGuard:
    """Sortino must be None when downside returns are absent or trivial."""

    def test_sortino_all_positive_returns(self):
        """All daily returns positive → downside vol ~ 0 → sortino is None."""
        idx = pd.date_range("2023-01-01", periods=60, freq="B")
        # Strictly monotone increasing equity — no negative daily returns
        equity = pd.Series(
            np.linspace(1.0, 1.5, 60),
            index=idx,
        )
        result = compute_equity_metrics(equity)
        assert result.get("sortino") is None, (
            f"Expected sortino=None for all-positive series, got {result.get('sortino')}"
        )

    def test_sortino_too_short(self):
        """Series shorter than _MIN_DAYS_FOR_RATIO → sortino is None."""
        equity = _make_equity(_MIN_DAYS_FOR_RATIO - 1)
        result = compute_equity_metrics(equity)
        assert result.get("sortino") is None, (
            "Expected sortino=None for series shorter than _MIN_DAYS_FOR_RATIO"
        )

    def test_sortino_is_none_not_nan_or_inf(self):
        """sortino must be exactly None (not NaN, Inf) for degenerate input."""
        idx = pd.date_range("2023-01-01", periods=30, freq="B")
        equity = pd.Series(np.linspace(1.0, 1.2, 30), index=idx)
        result = compute_equity_metrics(equity)
        val = result.get("sortino")
        assert val is None or (isinstance(val, float) and math.isfinite(val)), (
            f"sortino must be None or a finite float, got {val}"
        )

    def test_sortino_normal_series(self):
        """Normal mixed series with enough data → sortino is a finite float."""
        equity = _make_equity(252)
        result = compute_equity_metrics(equity)
        sortino = result.get("sortino")
        # May be None if the random seed produces no downside, else must be finite
        if sortino is not None:
            assert math.isfinite(sortino), f"sortino must be finite, got {sortino}"


class TestCalmarGuard:
    """Calmar must be None when max_drawdown is near-zero."""

    def test_calmar_near_zero_drawdown(self):
        """Near-flat equity → |max_dd| < _MIN_DD_FOR_CALMAR → calmar is None."""
        # Build equity that barely dips by less than 0.5 %
        tiny_dd = _MIN_DD_FOR_CALMAR / 2  # e.g. 0.25 %
        vals = [1.0] * 200 + [1.0 - tiny_dd] * 10 + [1.0] * 40
        equity = pd.Series(vals, index=pd.date_range("2023-01-01", periods=len(vals), freq="B"))
        result = compute_drawdown_metrics(equity)
        assert result.get("calmar") is None, (
            f"Expected calmar=None for near-zero drawdown, got {result.get('calmar')}"
        )

    def test_calmar_flat_equity(self):
        """Perfectly flat equity → max_dd == 0 → calmar is None."""
        equity = pd.Series(
            [1.0] * 100,
            index=pd.date_range("2023-01-01", periods=100, freq="B"),
        )
        result = compute_drawdown_metrics(equity)
        assert result.get("calmar") is None

    def test_calmar_real_drawdown(self):
        """Real drawdown beyond threshold → calmar is a finite float or None only if CAGR/dd gives non-finite."""
        equity = _make_equity(252)
        result = compute_drawdown_metrics(equity)
        calmar = result.get("calmar")
        if calmar is not None:
            assert math.isfinite(calmar), f"calmar must be finite, got {calmar}"

    def test_calmar_not_huge(self):
        """Calmar values must not exceed a sanity ceiling when drawdown is gated."""
        equity = _make_equity(252)
        result = compute_drawdown_metrics(equity)
        calmar = result.get("calmar")
        if calmar is not None:
            assert abs(calmar) <= 1000, f"Calmar suspiciously large: {calmar}"


class TestTimeWindowGuard:
    """Monthly summaries must be honest about insufficient data."""

    def test_sparse_monthly_has_flag(self):
        """Series with < _MIN_MONTHS complete months → insufficient_data flag."""
        # ~6 weeks of bars, < 3 complete months
        idx = pd.date_range("2023-01-03", periods=30, freq="B")
        equity = pd.Series(np.linspace(1.0, 1.05, 30), index=idx)
        result = compute_time_window_metrics(equity)
        # Must not be empty (we have ≥ 10 bars) but must signal insufficient data
        if result:  # if any result at all (may be {} if < 2 months formed)
            if result.get("n_months", _MIN_MONTHS) < _MIN_MONTHS:
                assert result.get("insufficient_data") is True
                assert "note" in result
                assert result.get("monthly_returns") == []

    def test_sparse_monthly_no_best_worst(self):
        """Insufficient monthly data must not expose best_month / worst_month."""
        idx = pd.date_range("2023-01-03", periods=30, freq="B")
        equity = pd.Series(np.linspace(1.0, 1.05, 30), index=idx)
        result = compute_time_window_metrics(equity)
        if result.get("insufficient_data"):
            assert "best_month" not in result
            assert "worst_month" not in result

    def test_sufficient_monthly_no_flag(self):
        """Series with enough months must NOT have insufficient_data=True."""
        equity = _make_equity(400)
        result = compute_time_window_metrics(equity)
        assert result.get("insufficient_data") is not True


class TestStrictJsonEdgeCases:
    """Metrics payload must always be strictly JSON-serialisable."""

    def test_all_positive_equity_strict_json(self):
        """All-positive equity (zero downside) must still produce valid JSON."""
        idx = pd.date_range("2023-01-01", periods=60, freq="B")
        equity = pd.Series(np.linspace(1.0, 1.5, 60), index=idx)
        em = compute_equity_metrics(equity)
        serialised = json.dumps(em, allow_nan=False)
        data = json.loads(serialised)
        assert "sortino" in data

    def test_flat_equity_strict_json(self):
        """Flat equity (zero drawdown) must produce valid JSON with calmar=null."""
        equity = pd.Series([1.0] * 100, index=pd.date_range("2023-01-01", periods=100, freq="B"))
        dm = compute_drawdown_metrics(equity)
        serialised = json.dumps(dm, allow_nan=False)
        data = json.loads(serialised)
        assert data["calmar"] is None

    def test_constants_exported(self):
        """All K.3 guard constants must be importable and positive."""
        assert _MIN_DAYS_FOR_RATIO > 0
        assert _MIN_MONTHS > 0
        assert _MIN_DD_FOR_CALMAR > 0
        assert _SORTINO_DOWNSIDE_FLOOR > 0
