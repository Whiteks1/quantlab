
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import json
from copy import deepcopy

from quantlab.execution.forward_eval import (
    CandidateConfig, 
    PortfolioState, 
    run_forward_evaluation, 
    write_forward_eval_artifacts,
    load_forward_session
)

@pytest.fixture
def sample_df():
    """Create 400 bars of synthetic OHLC data."""
    dates = pd.date_range("2024-01-01", periods=400, freq="D")
    df = pd.DataFrame({
        "open": np.linspace(100, 110, 400),
        "high": np.linspace(101, 111, 400),
        "low": np.linspace(99, 109, 400),
        "close": np.linspace(100, 110, 400),
    }, index=dates)
    return df

@pytest.fixture
def candidate():
    return CandidateConfig(
        strategy_name="rsi_ma_cross_v2",
        params={"rsi_period": 14},
        ticker="TEST",
        interval="1d",
        source_run_id="run_123"
    )

def test_forward_resume_workflow(sample_df, candidate, tmp_path):
    # 1. First evaluation (bars 0-200)
    df_part1 = sample_df.iloc[:200]
    out_dir = tmp_path / "fwd_session"
    
    result1 = run_forward_evaluation(
        candidate=candidate,
        df=df_part1,
        initial_cash=10000.0,
        eval_start="2024-01-01",
        eval_end="2024-07-18"
    )
    
    write_forward_eval_artifacts(result1, out_dir)
    
    ps1 = result1["portfolio_state"]
    assert ps1.resume_count == 0
    assert ps1.bars_fetched == 200
    assert ps1.last_timestamp is not None
    
    # 2. Resume evaluation (bars 200-400)
    df_part2 = sample_df.iloc[0:400] 
    
    session_data = load_forward_session(out_dir)
    initial_historical = {
        "historic_trades": session_data["historic_trades"],
        "historic_equity": session_data["historic_equity"]
    }
    
    result2 = run_forward_evaluation(
        candidate=candidate,
        df=df_part2,
        initial_state=session_data["portfolio_state"]
    )
    
    write_forward_eval_artifacts(result2, out_dir, initial_historical=initial_historical)
    
    # Reload and verify
    session_data_final = load_forward_session(out_dir)
    ps_final = session_data_final["portfolio_state"]
    
    assert ps_final.resume_count == 1
    assert ps_final.bars_fetched == 200 + 400 # Segment 1 + Segment 2
    
    # Verify artifacts are merged
    trades_final = session_data_final["historic_trades"]
    equity_final = session_data_final["historic_equity"]
    
    # If no trades happened in second segment, trades count remains same
    # But timestamps in equity curve should cover both segments without duplicates
    assert len(pd.to_datetime(equity_final["timestamp"]).unique()) == 301
    
    # Check original start preservation
    assert ps_final.original_eval_start == "2024-01-01"

def test_portfolio_state_preservation_on_resume(sample_df, candidate):
    # Mock a state with an open position
    state = PortfolioState(
        session_id="test",
        cash=0.0,
        qty=100.0,
        current_equity=11000.0,
        starting_cash=10000.0,
        last_timestamp="2024-01-10",
        realized_pnl=500.0,
        original_eval_start="2024-01-01"
    )
    
    # Evaluation on a range that overlaps then continues
    df = sample_df.iloc[:150] # bars 0-150
    # last_timestamp is 2024-01-10 (which is bar 10 in sample_df)
    
    result = run_forward_evaluation(
        candidate=candidate,
        df=df,
        initial_state=state
    )
    
    ps = result["portfolio_state"]
    assert ps.resume_count == 1
    assert ps.qty == 100.0 # Should still be 100 if no SELL signal
    assert ps.realized_pnl == 500.0 # Should be preserved
    # current_equity should be updated to bar 20 close
    expected_eq = 100.0 * float(df.iloc[-1]["close"])
    assert ps.current_equity == pytest.approx(expected_eq)

def test_load_forward_session_invalid_dir(tmp_path):
    # Empty dir
    with pytest.raises(ValueError, match="Invalid session directory"):
        load_forward_session(tmp_path)

def test_run_forward_evaluation_short_data_error():
    candidate = CandidateConfig(strategy_name="rsi_ma_cross_v2", params={})
    df = pd.DataFrame({"close": [100.0]*10, "open": [100.0]*10, "high": [101.0]*10, "low": [99.0]*10}, 
                      index=pd.date_range("2024-01-01", periods=10))
    with pytest.raises(ValueError, match="produced an empty DataFrame"):
        run_forward_evaluation(candidate, df)

def test_lookback_skip_logic(sample_df, candidate):
    # Pass 400 bars, but eval_start is at bar 200
    eval_start = str(sample_df.index[200].date())
    result = run_forward_evaluation(
        candidate=candidate,
        df=sample_df,
        eval_start=eval_start,
        initial_cash=10000.0
    )
    
    # equity_curve should only contain bars from eval_start onwards
    eq = result["equity_curve"]
    assert eq.index[0].strftime("%Y-%m-%d") == eval_start
    # bars_evaluated should match eq length
    assert result["bars_evaluated"] == len(eq)
    # 400 bars total, indices 0-399. eval_start is at index 200.
    # So we should have indices [200, 201, ..., 399] which is 200 bars.
    assert len(eq) == 200

def test_resume_short_segment_after_short_fresh(sample_df, candidate, tmp_path):
    """
    Test a scenario where both the fresh run and the resume run are short.
    This verifies that lookback prefetch (implemented in main.py logic) 
    would allow this to work.
    
    Note: In this unit test, we pass the full sample_df manually to 
    run_forward_evaluation, simulating what main.py does with its fetch logic.
    """
    out_dir = tmp_path / "short_session"
    out_dir.mkdir()
    
    # 1. Fresh short session (indices 200-210)
    # Start at index 200
    eval_start_1 = str(sample_df.index[200].date())
    eval_end_1 = str(sample_df.index[210].date())
    
    # Pass full sample_df (simulates lookback prefetch)
    result1 = run_forward_evaluation(
        candidate=candidate,
        df=sample_df,
        eval_start=eval_start_1,
        eval_end=eval_end_1,
        initial_cash=1000.0
    )
    
    write_forward_eval_artifacts(result1, out_dir)
    assert len(result1["equity_curve"]) == 11 # 200 to 210 inclusive
    
    # 2. Resume short session (indices 211-215)
    session_data = load_forward_session(out_dir)
    initial_historical = {
        "historic_trades": session_data["historic_trades"],
        "historic_equity": session_data["historic_equity"]
    }
    
    eval_end_2 = str(sample_df.index[215].date())
    
    # Resume using same sample_df (simulates resume lookback)
    result2 = run_forward_evaluation(
        candidate=candidate,
        df=sample_df,
        eval_end=eval_end_2,
        initial_state=session_data["portfolio_state"]
    )
    
    write_forward_eval_artifacts(result2, out_dir, initial_historical=initial_historical)
    
    # Verify final session
    final_data = load_forward_session(out_dir)
    eq_final = final_data["historic_equity"]
    
    # Segment 1: index 200..210 (11 rows)
    # Segment 2: index 211..215 (5 rows)
    # Total: 16 rows
    assert len(eq_final) == 16
    assert len(eq_final["timestamp"].unique()) == 16
    
    # Verify chronological order
    eq_final["timestamp"] = pd.to_datetime(eq_final["timestamp"])
    assert eq_final["timestamp"].is_monotonic_increasing
