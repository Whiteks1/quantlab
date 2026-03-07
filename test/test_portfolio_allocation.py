import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from quantlab.reporting.portfolio_report import aggregate_portfolio

def create_mock_session(tmp_path, name, returns, ticker="BTC"):
    """
    returns: list of (timestamp, equity_norm)
    """
    d = tmp_path / name
    d.mkdir()
    state = {
        "session_id": name,
        "ticker": ticker,
        "starting_cash": 10000.0,
        "eval_start": returns[0][0],
        "eval_end": returns[-1][0],
        "updated_at": "2023-01-01T00:00:00Z"
    }
    with open(d / "portfolio_state.json", "w") as f:
        json.dump(state, f)
        
    df = pd.DataFrame(returns, columns=["timestamp", "equity"])
    df.to_csv(d / "forward_equity_curve.csv", index=False)
    return d

def test_equal_weight_aggregation(tmp_path):
    # sess1: starts at 1.0, ends at 1.1 (+10%)
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.1)])
    # sess2: starts at 1.0, ends at 0.9 (-10%)
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0), ("2023-01-02", 0.9)])
    
    payload = aggregate_portfolio([s1, s2], mode="equal_weight")
    
    # In equal weight: split 50/50. 
    # Portfolio return should be (0.5 * 0.1) + (0.5 * -0.1) = 0.0
    summary = payload["portfolio_summary"]
    assert summary["total_return"] == pytest.approx(0.0)
    assert payload["allocation"]["mode"] == "equal_weight"
    assert payload["candidates"][0]["assigned_weight"] == 0.5

def test_custom_weight_normalization(tmp_path):
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.2)]) # +20%
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0), ("2023-01-02", 1.0)]) # +0%
    
    # Weights 3:1 -> 0.75 and 0.25
    weights = {"s1": 3.0, "s2": 1.0}
    payload = aggregate_portfolio([s1, s2], mode="custom_weight", weights=weights)
    
    # Return: (0.75 * 0.2) + (0.25 * 0.0) = 0.15 (15%)
    summary = payload["portfolio_summary"]
    assert summary["total_return"] == pytest.approx(0.15)
    assert payload["allocation"]["weights_used"]["s1"] == 0.75

def test_staggered_start_weighted(tmp_path):
    # s1: active t1, t2
    # s2: active t2 only
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.1)])
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-02", 1.0)])
    
    # Equal weight 50/50
    payload = aggregate_portfolio([s1, s2], mode="equal_weight")
    
    # t1: s1=1.0, s2=neutral(1.0). Weighted = (0.5*1.0) + (0.5*1.0) = 1.0
    # t2: s1=1.1, s2=1.0. Weighted = (0.5*1.1) + (0.5*1.0) = 1.05
    summary = payload["portfolio_summary"]
    assert summary["total_return"] == pytest.approx(0.05)

def test_reject_invalid_custom_weights(tmp_path):
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0)])
    
    # Empty weights
    with pytest.raises(ValueError, match="mode requires a weights mapping"):
        aggregate_portfolio([s1], mode="custom_weight", weights=None)
        
    # Weights for nonexistent session
    with pytest.raises(ValueError, match="refer only to excluded or nonexistent sessions"):
        aggregate_portfolio([s1], mode="custom_weight", weights={"ghost": 1.0})
        
    # Total zero weight
    with pytest.raises(ValueError, match="must be positive"):
        aggregate_portfolio([s1], mode="custom_weight", weights={"s1": 0.0})

def test_reject_negative_custom_weights(tmp_path):
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0)], ticker="T1")
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0)], ticker="T2")
    
    # One negative weight
    with pytest.raises(ValueError, match="cannot be negative"):
        aggregate_portfolio([s1, s2], mode="custom_weight", weights={"s1": 1.0, "s2": -0.5})
        
    # All negative weights
    with pytest.raises(ValueError, match="cannot be negative"):
        aggregate_portfolio([s1, s2], mode="custom_weight", weights={"s1": -1.0, "s2": -1.0})

def test_raw_capital_compat(tmp_path):
    # s1: 10k -> 11k
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.1)])
    # s2: 10k -> 9k
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0), ("2023-01-02", 0.9)])
    
    payload = aggregate_portfolio([s1, s2], mode="raw_capital")
    
    # (11k + 9k) / 20k - 1 = 0
    assert payload["portfolio_summary"]["total_return"] == pytest.approx(0.0)
    assert payload["portfolio_summary"]["starting_value"] == 20000.0
