import pytest
import pandas as pd
from quantlab.experiments.runner import expand_grid

def test_expand_grid_creates_correct_count():
    """
    Test that expand_grid creates the expected number of combinations.
    """
    config = {
        "ticker": "ETH-USD",
        "param_grid": {
            "rsi_buy_max": [55, 60],
            "rsi_sell_min": [70, 75, 80],
            "cooldown_days": [0, 5]
        }
    }
    # 2 * 3 * 2 = 12
    runs = expand_grid(config)
    assert len(runs) == 12
    
    # Check one run
    run = runs[0]
    assert "param_grid" not in run
    assert run["ticker"] == "ETH-USD"
    assert "rsi_buy_max" in run
    assert "rsi_sell_min" in run
    assert "cooldown_days" in run

def test_expand_grid_no_grid():
    config = {"ticker": "ETH-USD", "rsi_buy_max": 60}
    runs = expand_grid(config)
    assert len(runs) == 1
    assert runs[0]["rsi_buy_max"] == 60

def test_expand_grid_preserves_other_keys():
    config = {
        "ticker": "ETH-USD",
        "fee": 0.002,
        "param_grid": {
            "rsi_buy_max": [55, 60]
        }
    }
    runs = expand_grid(config)
    assert len(runs) == 2
    for r in runs:
        assert r["ticker"] == "ETH-USD"
        assert r["fee"] == 0.002
