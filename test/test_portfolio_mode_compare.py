import pytest
import pandas as pd
import json
from pathlib import Path
from quantlab.reporting.portfolio_mode_compare import compare_portfolio_modes, render_comparison_md

@pytest.fixture
def mock_session_dirs(tmp_path):
    # Session 1: ETH (+10%)
    s1 = tmp_path / "session_eth"
    s1.mkdir()
    state1 = {
        "session_id": "eth_session",
        "starting_cash": 10000.0,
        "ticker": "ETH-USD",
        "candidate": {"strategy_name": "rsi_ma", "source_run_id": "run_1"},
        "eval_start": "2024-01-01",
        "eval_end": "2024-01-02",
        "updated_at": "2024-01-02T00:00:00Z"
    }
    with open(s1 / "portfolio_state.json", "w") as f:
        json.dump(state1, f)
    df1 = pd.DataFrame({"timestamp": ["2024-01-01", "2024-01-02"], "equity": [1.0, 1.1]})
    df1.to_csv(s1 / "forward_equity_curve.csv", index=False)
    
    # Session 2: BTC (-10%)
    s2 = tmp_path / "session_btc"
    s2.mkdir()
    state2 = {
        "session_id": "btc_session",
        "starting_cash": 10000.0,
        "ticker": "BTC-USD",
        "candidate": {"strategy_name": "rsi_ma", "source_run_id": "run_1"},
        "eval_start": "2024-01-01",
        "eval_end": "2024-01-02",
        "updated_at": "2024-01-02T00:00:00Z"
    }
    with open(s2 / "portfolio_state.json", "w") as f:
        json.dump(state2, f)
    df2 = pd.DataFrame({"timestamp": ["2024-01-01", "2024-01-02"], "equity": [1.0, 0.9]})
    df2.to_csv(s2 / "forward_equity_curve.csv", index=False)
    
    return [s1, s2]

def test_compare_portfolio_modes_basic(mock_session_dirs):
    # Without custom weights: raw_capital and equal_weight
    payload = compare_portfolio_modes(mock_session_dirs)
    
    assert "raw_capital" in payload["comparison"]
    assert "equal_weight" in payload["comparison"]
    assert "custom_weight" not in payload["comparison"]
    
    # raw_capital return: (11k + 9k) / 20k - 1 = 0%
    assert payload["comparison"]["raw_capital"]["total_return"] == pytest.approx(0.0)
    
    # equal_weight return: (0.5 * 0.1) + (0.5 * -0.1) = 0%
    assert payload["comparison"]["equal_weight"]["total_return"] == pytest.approx(0.0)

def test_compare_portfolio_modes_with_custom(mock_session_dirs):
    weights = {"eth_session": 1.0, "btc_session": 0.0}
    payload = compare_portfolio_modes(mock_session_dirs, weights=weights)
    
    assert "custom_weight" in payload["comparison"]
    # custom_weight return (100% ETH): +10%
    assert payload["comparison"]["custom_weight"]["total_return"] == pytest.approx(0.10)

def test_render_comparison_md(mock_session_dirs):
    payload = compare_portfolio_modes(mock_session_dirs)
    md = render_comparison_md(payload)
    
    assert "# Portfolio Mode Comparison Report" in md
    assert "| Total Return |" in md
    assert "0.00%" in md

def test_compare_modes_reuse_universe(mock_session_dirs):
    # Ensure all modes use exactly the same N sessions
    payload = compare_portfolio_modes(mock_session_dirs, top_n=1, rank_metric="total_return")
    
    # Top 1 by total_return is ETH (+10%)
    assert payload["n_sessions"] == 1
    
    # Both modes should show same return since they only have one session
    assert payload["comparison"]["raw_capital"]["total_return"] == pytest.approx(0.10)
    assert payload["comparison"]["equal_weight"]["total_return"] == pytest.approx(0.10)
