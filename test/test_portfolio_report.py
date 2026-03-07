import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
from quantlab.reporting.portfolio_report import aggregate_portfolio, render_portfolio_md

@pytest.fixture
def mock_session_dirs(tmp_path):
    # Session 1: ETH
    s1 = tmp_path / "session_eth"
    s1.mkdir()
    
    state1 = {
        "session_id": "eth_session",
        "starting_cash": 10000.0,
        "candidate": {"ticker": "ETH-USD", "strategy_name": "rsi_ma"},
    }
    with open(s1 / "portfolio_state.json", "w") as f:
        json.dump(state1, f)
        
    df1 = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
        "equity": [1.0, 1.01, 1.02, 1.01, 1.05]
    })
    df1.to_csv(s1 / "forward_equity_curve.csv", index=False)
    
    # Session 2: BTC
    s2 = tmp_path / "session_btc"
    s2.mkdir()
    
    state2 = {
        "session_id": "btc_session",
        "starting_cash": 10000.0,
        "candidate": {"ticker": "BTC-USD", "strategy_name": "rsi_ma"},
    }
    with open(s2 / "portfolio_state.json", "w") as f:
        json.dump(state2, f)
        
    df2 = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
        "equity": [1.0, 0.99, 0.98, 1.00, 1.02]
    })
    df2.to_csv(s2 / "forward_equity_curve.csv", index=False)
    
    return [s1, s2]

def test_aggregate_portfolio_multiple(mock_session_dirs):
    payload = aggregate_portfolio(mock_session_dirs)
    
    assert payload["n_candidates"] == 2
    summary = payload["portfolio_summary"]
    
    # Starting value: 10000 + 10000 = 20000
    assert summary["starting_value"] == 20000.0
    
    # Ending value: (1.05 * 10000) + (1.02 * 10000) = 10500 + 10200 = 20700
    assert summary["ending_value"] == 20700.0
    assert summary["total_pnl"] == 700.0
    assert pytest.approx(summary["total_return"]) == 0.035
    
    # Check contribution
    eth_cand = next(c for c in payload["candidates"] if c["ticker"] == "ETH-USD")
    assert eth_cand["total_pnl"] == 500.0
    assert pytest.approx(eth_cand["contribution_pct"]) == 500.0 / 700.0

def test_aggregate_portfolio_single(mock_session_dirs):
    payload = aggregate_portfolio([mock_session_dirs[0]])
    
    assert payload["n_candidates"] == 1
    summary = payload["portfolio_summary"]
    assert summary["starting_value"] == 10000.0
    assert pytest.approx(summary["total_return"]) == 0.05

def test_aggregate_portfolio_staggered(tmp_path):
    # Cand A: starts at t0, stable at 1.0
    s1 = tmp_path / "session_a"
    s1.mkdir()
    state1 = {"session_id": "a", "starting_cash": 10000.0, "candidate": {"ticker": "A"}}
    with open(s1 / "portfolio_state.json", "w") as f: json.dump(state1, f)
    df1 = pd.DataFrame({"timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]), "equity": [1.0, 1.0]})
    df1.to_csv(s1 / "forward_equity_curve.csv", index=False)

    # Cand B: starts at t1 (staggered), starts at 1.0
    s2 = tmp_path / "session_b"
    s2.mkdir()
    state2 = {"session_id": "b", "starting_cash": 10000.0, "candidate": {"ticker": "B"}}
    with open(s2 / "portfolio_state.json", "w") as f: json.dump(state2, f)
    # Only one bar at t=2
    df2 = pd.DataFrame({"timestamp": pd.to_datetime(["2024-01-02"]), "equity": [1.0]})
    df2.to_csv(s2 / "forward_equity_curve.csv", index=False)

    payload = aggregate_portfolio([s1, s2])
    summary = payload["portfolio_summary"]
    
    # Correct behavior:
    # t0: A=10000, B=(loading NaNs filled with 10000) -> Portfolio=20000
    # t1: A=10000, B=10000 -> Portfolio=20000
    # Starting value = 20000
    # Ending value = 20000
    # Total PnL = 0
    # Max DD = 0
    
    assert summary["starting_value"] == 20000.0
    assert summary["ending_value"] == 20000.0
    assert summary["total_pnl"] == 0.0
    assert summary["max_drawdown"] == 0.0 # No fake drawdown!

def test_render_portfolio_md(mock_session_dirs):
    payload = aggregate_portfolio(mock_session_dirs)
    md = render_portfolio_md(payload)
    
    assert "# Portfolio Aggregation Report" in md
    assert "ETH-USD" in md
    assert "BTC-USD" in md
    assert "3.50%" in md # Total return
