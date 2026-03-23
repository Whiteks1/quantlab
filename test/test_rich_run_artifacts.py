"""Tests for Stage K.1 rich run artifact persistence and consumption."""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from quantlab.reporting.advanced_metrics import (
    _load_equity_from_artifacts,
    build_advanced_metrics,
)
from quantlab.experiments.runner import (
    _persist_grid_rich_artifacts,
    _persist_walkforward_rich_artifacts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_walkforward_df(n_splits: int = 3, top_k: int = 1) -> pd.DataFrame:
    """Create a minimal walkforward result DataFrame."""
    rows = []
    for s in range(n_splits):
        for phase in ("train", "test"):
            for k in range(top_k):
                rows.append({
                    "split_name": f"split_{s:02d}",
                    "phase": phase,
                    "selected": phase == "test",
                    "rank_in_train": k + 1,
                    "total_return": 0.1 * (s + 1),
                    "sharpe_simple": 1.0 + s * 0.1,
                    "max_drawdown": -0.05,
                    "trades": 10,
                    "rsi_buy_max": 60,
                    "rsi_sell_min": 75,
                })
    return pd.DataFrame(rows)


def _make_grid_leaderboard(n: int = 5) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "sharpe_simple": 2.0 - i * 0.1,
            "total_return": 0.3 - i * 0.02,
            "rsi_buy_max": 60 + i,
            "max_drawdown": -0.1,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Grid artifact tests
# ---------------------------------------------------------------------------

def test_persist_grid_rich_artifacts_creates_best_config(tmp_path):
    lb = _make_grid_leaderboard()
    _persist_grid_rich_artifacts(tmp_path, lb)

    best_path = tmp_path / "best_config.json"
    assert best_path.exists(), "best_config.json must be created"

    with open(best_path) as f:
        data = json.load(f)
    # Top row is highest sharpe
    assert data["sharpe_simple"] == pytest.approx(2.0, rel=1e-6)


def test_persist_grid_rich_artifacts_strict_json(tmp_path):
    """best_config.json must survive allow_nan=False load."""
    lb = _make_grid_leaderboard()
    lb.loc[0, "sharpe_simple"] = float("nan")  # inject NaN
    _persist_grid_rich_artifacts(tmp_path, lb)

    with open(tmp_path / "best_config.json") as f:
        data = json.load(f)
    assert data["sharpe_simple"] is None  # sanitised to null


def test_persist_grid_rich_artifacts_empty_df(tmp_path):
    """Empty leaderboard must not crash and must not write the file."""
    _persist_grid_rich_artifacts(tmp_path, pd.DataFrame())
    assert not (tmp_path / "best_config.json").exists()


# ---------------------------------------------------------------------------
# Walkforward artifact tests
# ---------------------------------------------------------------------------

def test_persist_walkforward_rich_artifacts_creates_files(tmp_path):
    wf_df = _make_walkforward_df(n_splits=4, top_k=1)
    summary_records = [
        {"split_name": f"split_{i:02d}", "n_selected": 1, "n_train_runs": 9, "n_test_runs": 9,
         "best_train_sharpe": 1.2, "best_test_sharpe": 0.9}
        for i in range(4)
    ]
    _persist_walkforward_rich_artifacts(tmp_path, wf_df, summary_records)

    assert (tmp_path / "selected_configs.csv").exists()
    assert (tmp_path / "oos_equity_curve.csv").exists()
    assert (tmp_path / "split_metrics.csv").exists()


def test_oos_equity_curve_is_monotonic_given_positive_returns(tmp_path):
    """With all positive OOS returns the equity curve must be strictly increasing."""
    wf_df = _make_walkforward_df(n_splits=5, top_k=1)
    _persist_walkforward_rich_artifacts(tmp_path, wf_df, [])

    df = pd.read_csv(tmp_path / "oos_equity_curve.csv")
    eq = df["cumulative_equity"].values
    assert len(eq) == 5
    # All cumulative values above 1.0 (positive returns)
    assert all(eq > 1.0)
    # Monotonically increasing
    assert all(eq[i] < eq[i + 1] for i in range(len(eq) - 1))


def test_oos_equity_curve_starts_at_one_after_prepend(tmp_path):
    """_load_equity_from_artifacts must prepend 1.0 to the oos equity curve."""
    wf_df = _make_walkforward_df(n_splits=3)
    _persist_walkforward_rich_artifacts(tmp_path, wf_df, [])

    eq = _load_equity_from_artifacts(tmp_path)
    assert eq is not None
    assert float(eq.iloc[0]) == pytest.approx(1.0)
    assert len(eq) == 4   # 3 splits + the prepended 1.0


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------

def test_load_equity_from_artifacts_fallback_to_trades_csv(tmp_path):
    """Runs without oos_equity_curve or equity_curve must fall back to trades.csv."""
    from quantlab.reporting.trade_analytics import REQUIRED_COLS

    trades_data = {
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "side": ["BUY", "SELL", "BUY"],
        "close": [100.0, 102.0, 101.0],
        "exec_price": [100.0, 102.0, 101.0],
        "qty": [1.0, 0.0, 1.0],
        "fee": [0.1, 0.1, 0.1],
        "equity_after": [1000.0, 1002.0, 1001.5],
    }
    pd.DataFrame(trades_data).to_csv(tmp_path / "trades.csv", index=False)

    eq = _load_equity_from_artifacts(tmp_path)
    assert eq is not None
    assert float(eq.iloc[0]) == pytest.approx(1.0)


def test_load_equity_prefers_oos_over_trades(tmp_path):
    """oos_equity_curve.csv must take priority over trades.csv."""
    # Write a trades.csv with 3 rows
    pd.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "side": ["BUY", "SELL", "BUY"],
        "close": [100.0, 102.0, 101.0],
        "exec_price": [100.0, 102.0, 101.0],
        "qty": [1.0, 0.0, 1.0],
        "fee": [0.1, 0.1, 0.1],
        "equity_after": [1000.0, 1002.0, 1001.5],
    }).to_csv(tmp_path / "trades.csv", index=False)

    # Write an oos_equity_curve with 5 splits
    wf_df = _make_walkforward_df(n_splits=5)
    _persist_walkforward_rich_artifacts(tmp_path, wf_df, [])

    eq = _load_equity_from_artifacts(tmp_path)
    # Should have 6 rows (5 splits + prepended 1.0), not 3 rows from trades.csv
    assert len(eq) == 6


def test_build_advanced_metrics_uses_oos_equity(tmp_path):
    """build_advanced_metrics must compute equity metrics when oos_equity_curve is present."""
    run_dir = tmp_path / "wf_run"
    run_dir.mkdir()

    # Write report.json
    report = {
        "header": {"run_id": "wf_run", "mode": "walkforward",
                   "created_at": "2023-01-01", "git_commit": "abc"},
        "results": [],
        "config_resolved": {},
    }
    with open(run_dir / "report.json", "w") as f:
        json.dump(report, f)

    # Persist OOS equity
    wf_df = _make_walkforward_df(n_splits=6, top_k=1)
    _persist_walkforward_rich_artifacts(run_dir, wf_df, [])

    payload = build_advanced_metrics(run_dir)

    # equity_metrics must now be populated
    em = payload.get("equity_metrics", {})
    assert em.get("n_days") is not None, "equity_metrics must have n_days"
    assert em.get("total_return") is not None, "equity_metrics must have total_return"

    # Strictly JSON-serialisable
    json.dumps(payload, allow_nan=False)
