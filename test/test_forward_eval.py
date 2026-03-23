"""Tests for execution/forward_eval.py (Stage L)."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantlab.execution.forward_eval import (
    CandidateConfig,
    PortfolioState,
    build_strategy,
    load_candidate_from_run,
    load_portfolio_state,
    run_forward_evaluation,
    update_portfolio_state,
    write_forward_eval_artifacts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Synthetic OHLCV DataFrame with a DatetimeIndex."""
    rng = np.random.default_rng(seed)
    close = np.cumprod(1 + rng.normal(0.0005, 0.015, n)) * 100
    df = pd.DataFrame({
        "open": close * (1 - rng.uniform(0.001, 0.005, n)),
        "high": close * (1 + rng.uniform(0.001, 0.01, n)),
        "low": close * (1 - rng.uniform(0.001, 0.01, n)),
        "close": close,
        "volume": rng.integers(1_000, 100_000, n).astype(float),
    }, index=pd.date_range("2023-01-01", periods=n, freq="B"))
    return df


def _make_candidate(params: dict | None = None) -> CandidateConfig:
    return CandidateConfig(
        strategy_name="rsi_ma_cross_v2",
        params=params or {"rsi_buy_max": 60.0, "rsi_sell_min": 75.0, "cooldown_days": 0},
        fee_rate=0.002,
        slippage_bps=8.0,
        source_run_id="test_run_001",
        source_run_dir="/tmp/test_run_001",
        selection_metric="sharpe_simple",
        selection_value=1.23,
        selected_at="2026-01-01T00:00:00+00:00",
        ticker="ETH-USD",
        interval="1d",
    )


def _make_grid_run_dir(tmp_path: Path) -> Path:
    """Populate a minimal grid run directory with a leaderboard.csv."""
    run_dir = tmp_path / "grid_run"
    run_dir.mkdir()

    meta = {
        "run_id": "grid_run",
        "mode": "grid",
        "ticker": "ETH-USD",
        "interval": "1d",
        "fee_rate": 0.002,
        "slippage_bps": 8.0,
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f)

    lb = pd.DataFrame([
        {"strategy_name": "rsi_ma_cross_v2", "rsi_buy_max": 55.0, "rsi_sell_min": 70.0,
         "cooldown_days": 0, "sharpe_simple": 1.5, "total_return": 0.20},
        {"strategy_name": "rsi_ma_cross_v2", "rsi_buy_max": 60.0, "rsi_sell_min": 75.0,
         "cooldown_days": 1, "sharpe_simple": 0.8, "total_return": 0.10},
    ])
    lb.to_csv(run_dir / "leaderboard.csv", index=False)
    return run_dir


def _make_walkforward_run_dir(tmp_path: Path) -> Path:
    """Populate a minimal walkforward run directory with oos_leaderboard.csv."""
    run_dir = tmp_path / "wf_run"
    run_dir.mkdir()

    meta = {"run_id": "wf_run", "mode": "walkforward", "ticker": "BTC-USD"}
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f)

    oos = pd.DataFrame([
        {"strategy_name": "rsi_ma_cross_v2", "rsi_buy_max": 65.0, "rsi_sell_min": 80.0,
         "cooldown_days": 0, "sharpe_simple": 2.1, "total_return": 0.35},
    ])
    oos.to_csv(run_dir / "oos_leaderboard.csv", index=False)
    return run_dir


# ---------------------------------------------------------------------------
# Candidate loading
# ---------------------------------------------------------------------------

class TestLoadCandidate:

    def test_load_candidate_grid_run(self, tmp_path):
        run_dir = _make_grid_run_dir(tmp_path)
        candidate = load_candidate_from_run(run_dir, metric="sharpe_simple")
        assert isinstance(candidate, CandidateConfig)
        assert candidate.strategy_name == "rsi_ma_cross_v2"
        assert candidate.selection_metric == "sharpe_simple"
        # Best row should have the highest sharpe
        assert candidate.selection_value == pytest.approx(1.5)
        assert candidate.params.get("rsi_buy_max") == pytest.approx(55.0)
        assert candidate.source_run_id == "grid_run"
        assert candidate.ticker == "ETH-USD"

    def test_load_candidate_walkforward_run(self, tmp_path):
        run_dir = _make_walkforward_run_dir(tmp_path)
        candidate = load_candidate_from_run(run_dir, metric="sharpe_simple")
        assert candidate.strategy_name == "rsi_ma_cross_v2"
        assert candidate.selection_value == pytest.approx(2.1)
        assert candidate.params.get("rsi_sell_min") == pytest.approx(80.0)

    def test_load_candidate_missing_leaderboard_raises(self, tmp_path):
        """No leaderboard at all → clear ValueError."""
        run_dir = tmp_path / "empty_run"
        run_dir.mkdir()
        meta = {"run_id": "empty_run", "mode": "grid"}
        with open(run_dir / "metadata.json", "w") as f:
            json.dump(meta, f)
        with pytest.raises(ValueError, match="Could not derive a candidate"):
            load_candidate_from_run(run_dir)

    def test_load_candidate_nonexistent_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_candidate_from_run(tmp_path / "does_not_exist")

    def test_load_candidate_from_run_report_json(self, tmp_path):
        """Falls back to run_report.json when no leaderboard CSV."""
        run_dir = tmp_path / "rr_run"
        run_dir.mkdir()
        rr = {
            "header": {"run_id": "rr_run", "mode": "grid"},
            "results": [
                {"strategy_name": "rsi_ma_cross_v2", "rsi_buy_max": 58.0,
                 "rsi_sell_min": 72.0, "cooldown_days": 0, "sharpe_simple": 1.1},
            ],
        }
        with open(run_dir / "run_report.json", "w") as f:
            json.dump(rr, f)
        candidate = load_candidate_from_run(run_dir)
        assert candidate.strategy_name == "rsi_ma_cross_v2"


# ---------------------------------------------------------------------------
# Strategy construction
# ---------------------------------------------------------------------------

class TestBuildStrategy:

    def test_build_rsi_ma_atr(self):
        candidate = _make_candidate()
        strat = build_strategy(candidate)
        assert hasattr(strat, "generate_signals")
        assert strat.rsi_buy_max == pytest.approx(60.0)
        assert strat.rsi_sell_min == pytest.approx(75.0)

    def test_build_unknown_strategy_raises(self):
        candidate = _make_candidate()
        candidate.strategy_name = "unknown_strategy_xyz"
        with pytest.raises(KeyError, match="Unknown strategy"):
            build_strategy(candidate)

    def test_extra_params_ignored(self):
        """Params not in strategy __init__ signature must not cause errors."""
        candidate = _make_candidate(params={
            "rsi_buy_max": 60.0, "rsi_sell_min": 75.0,
            "cooldown_days": 0, "some_unknown_param": 999,
        })
        strat = build_strategy(candidate)
        assert strat.rsi_buy_max == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Forward evaluation engine
# ---------------------------------------------------------------------------

class TestRunForwardEvaluation:

    def test_basic_run_returns_all_keys(self):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df, initial_cash=10_000.0)
        assert "candidate" in result
        assert "trades" in result
        assert "equity_curve" in result
        assert "portfolio_state" in result
        assert "bars_evaluated" in result
        assert result["bars_evaluated"] > 0

    def test_equity_curve_starts_at_one(self):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        eq = result["equity_curve"]
        assert len(eq) > 0
        assert eq.iloc[0] == pytest.approx(1.0, abs=1e-6)

    def test_equity_curve_length_matches_bars(self):
        df = _make_ohlcv(200)
        from quantlab.features.indicators import add_indicators
        df_ind = add_indicators(df)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        assert len(result["equity_curve"]) == result["bars_evaluated"]

    def test_no_trades_for_flat_data(self):
        """Flat close series → strategy generates no signals → empty trades."""
        n = 150
        df = pd.DataFrame({
            "open": [100.0] * n, "high": [101.0] * n,
            "low": [99.0] * n, "close": [100.0] * n, "volume": [1000.0] * n,
        }, index=pd.date_range("2023-01-01", periods=n, freq="B"))
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df, initial_cash=5_000.0)
        ps = result["portfolio_state"]
        assert ps.n_trades == 0
        assert result["trades"].empty

    def test_portfolio_state_n_trades_matches_trades_df(self):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        ps = result["portfolio_state"]
        assert ps.n_trades == len(result["trades"])

    def test_raises_on_empty_df(self):
        candidate = _make_candidate()
        with pytest.raises(ValueError, match="non-empty"):
            run_forward_evaluation(candidate, pd.DataFrame())

    def test_deterministic_with_same_seed(self):
        """Same inputs → same trades DataFrame."""
        df = _make_ohlcv(200, seed=7)
        candidate = _make_candidate()
        r1 = run_forward_evaluation(candidate, df, initial_cash=10_000.0, session_id="s1")
        r2 = run_forward_evaluation(candidate, df, initial_cash=10_000.0, session_id="s2")
        pd.testing.assert_frame_equal(r1["trades"], r2["trades"])

    def test_warmup_bar_accounting(self):
        """Verify bars_fetched and warmup_bars are correctly populated."""
        n = 150
        df = _make_ohlcv(n)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        ps = result["portfolio_state"]
        
        # indicator.py drops 99 bars (MA100), but adds_indicators drops any row with NaN
        assert ps.bars_fetched == n
        assert ps.warmup_bars > 0
        assert ps.bars_fetched == ps.warmup_bars + len(result["equity_curve"])


# ---------------------------------------------------------------------------
# Portfolio state
# ---------------------------------------------------------------------------

class TestPortfolioState:

    def test_update_portfolio_state_no_trades(self):
        eq = pd.Series([1.0, 1.01, 1.02], index=pd.date_range("2023-01-01", periods=3))
        ps = PortfolioState(session_id="x", cash=10_000.0, current_equity=10_000.0)
        updated = update_portfolio_state(ps, pd.DataFrame(columns=["timestamp", "side", "fee",
                                                                     "equity_after", "qty",
                                                                     "slippage"]),
                                         equity_series=eq, initial_cash=10_000.0)
        assert updated.n_trades == 0
        assert updated.realized_pnl == 0.0
        assert updated.unrealized_pnl == 0.0
        assert not updated.has_open_position

    def test_update_portfolio_state_with_open_position(self):
        """Verify PnL split and open position details."""
        # Mocking a session that ends with an open position
        eq_series = pd.Series([1000.0, 1050.0], index=[pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")])
        trades_df = pd.DataFrame([
            {"timestamp": "2023-01-01", "side": "BUY", "qty": 10.0, "exec_price": 100.0, "fee": 2.0, "equity_after": 998.0, "slippage": 0.0}
        ])
        ps = PortfolioState(session_id="op", starting_cash=1000.0)
        
        # total_equity = 1.05 * 1000 = 1050 (since normalized series is used in actual flow, 
        # but here we pass absolute eq_series for simplicity in test if update_portfolio_state expects normalized)
        # Actually update_portfolio_state expects normalized equity_series:
        # state.current_equity = float(equity_series.iloc[-1]) * initial_cash
        
        norm_eq = eq_series / 1000.0 
        updated = update_portfolio_state(ps, trades_df, norm_eq, initial_cash=1000.0)
        
        assert updated.has_open_position is True
        assert updated.open_position_qty == 10.0
        assert updated.open_position_entry_price == 100.0
        assert updated.current_equity == 1050.0
        assert updated.realized_pnl == 0.0
        # unrealized_pnl = current_equity - equity_after_last_trade = 1050 - 998 = 52
        assert updated.unrealized_pnl == pytest.approx(52.0)
        assert updated.open_position_mark_price == pytest.approx(105.0)

    def test_update_portfolio_state_with_closed_trades(self):
        """Verify realized PnL correctly computed."""
        norm_eq = pd.Series([1.0, 1.1], index=[pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")])
        trades_df = pd.DataFrame([
            {"timestamp": "2023-01-01", "side": "BUY", "qty": 10.0, "exec_price": 100.0, "fee": 2.0, "equity_after": 998.0, "slippage": 0.0},
            {"timestamp": "2023-01-02", "side": "SELL", "qty": 0.0, "exec_price": 110.0, "fee": 2.2, "equity_after": 1097.8, "slippage": 0.0}
        ])
        ps = PortfolioState(session_id="cl", starting_cash=1000.0)
        updated = update_portfolio_state(ps, trades_df, norm_eq, initial_cash=1000.0)
        
        assert updated.has_open_position is False
        assert updated.realized_pnl == pytest.approx(1097.8 - 998.0)
        assert updated.unrealized_pnl == 0.0
        assert updated.current_equity == 1100.0 # From norm_eq * 1000

    def test_portfolio_state_round_trip_json(self, tmp_path):
        ps = PortfolioState(
            session_id="abc",
            cash=5_000.0,
            qty=0.5,
            current_equity=6_000.0,
            total_fees=10.5,
            n_trades=4,
        )
        path = tmp_path / "portfolio_state.json"
        with open(path, "w") as f:
            json.dump(ps.to_dict(), f, allow_nan=False)
        restored = load_portfolio_state(path)
        assert restored.session_id == "abc"
        assert restored.cash == pytest.approx(5_000.0)
        assert restored.n_trades == 4

    def test_portfolio_state_strict_json(self, tmp_path):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        ps = result["portfolio_state"]
        serialised = json.dumps(ps.to_dict(), allow_nan=False)
        data = json.loads(serialised)
        assert "session_id" in data

    def test_load_portfolio_state_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_portfolio_state(tmp_path / "does_not_exist.json")


# ---------------------------------------------------------------------------
# Artifact persistence
# ---------------------------------------------------------------------------

class TestWriteForwardArtifacts:

    def test_all_files_created(self, tmp_path):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        written = write_forward_eval_artifacts(result, tmp_path / "fwd_out")
        out = tmp_path / "fwd_out"
        assert (out / "portfolio_state.json").exists()
        assert (out / "forward_trades.csv").exists()
        assert (out / "forward_equity_curve.csv").exists()
        assert (out / "forward_returns_series.csv").exists()
        assert len(written) == 4

    def test_portfolio_state_json_parseable(self, tmp_path):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        write_forward_eval_artifacts(result, tmp_path)
        content = (tmp_path / "portfolio_state.json").read_text(encoding="utf-8")
        data = json.loads(content)
        assert "session_id" in data
        assert "mode" in data

    def test_equity_curve_csv_schema(self, tmp_path):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        write_forward_eval_artifacts(result, tmp_path)
        df_eq = pd.read_csv(tmp_path / "forward_equity_curve.csv")
        assert "timestamp" in df_eq.columns
        assert "equity" in df_eq.columns

    def test_trades_csv_schema_when_no_trades(self, tmp_path):
        """Empty trades must still write a well-formed CSV with headers."""
        n = 150
        df_flat = pd.DataFrame({
            "open": [100.0] * n, "high": [101.0] * n,
            "low": [99.0] * n, "close": [100.0] * n, "volume": [1000.0] * n,
        }, index=pd.date_range("2023-01-01", periods=n, freq="B"))
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df_flat)
        write_forward_eval_artifacts(result, tmp_path)
        df_t = pd.read_csv(tmp_path / "forward_trades.csv")
        assert "timestamp" in df_t.columns
        assert "side" in df_t.columns
        assert len(df_t) == 0

    def test_resume_portfolio_state(self, tmp_path):
        """Portfolio state persisted and re-loaded must be identical."""
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        write_forward_eval_artifacts(result, tmp_path)
        restored = load_portfolio_state(tmp_path / "portfolio_state.json")
        original = result["portfolio_state"]
        assert restored.session_id == original.session_id
        assert restored.n_trades == original.n_trades
        assert restored.total_fees == pytest.approx(original.total_fees)

    def test_no_nan_in_equity_csv(self, tmp_path):
        df = _make_ohlcv(200)
        candidate = _make_candidate()
        result = run_forward_evaluation(candidate, df)
        write_forward_eval_artifacts(result, tmp_path)
        df_eq = pd.read_csv(tmp_path / "forward_equity_curve.csv")
        assert not df_eq["equity"].isna().any(), "equity curve must not contain NaN"
