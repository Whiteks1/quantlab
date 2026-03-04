import pytest
import pandas as pd
import numpy as np
from quantlab.reporting.trade_analytics import compute_round_trips, aggregate_trade_metrics

def test_compute_round_trips_handles_sell_qty_zero():
    """
    Test that a SELL row with qty=0 correctly closes the full position.
    """
    data = [
        {"timestamp": "2024-01-01 10:00", "side": "BUY", "exec_price": 100.0, "qty": 10.0, "fee": 1.0, "close": 100.0, "equity_after": 1000.0},
        {"timestamp": "2024-01-01 11:00", "side": "SELL", "exec_price": 110.0, "qty": 0.0, "fee": 1.0, "close": 110.0, "equity_after": 1100.0},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    rt = compute_round_trips(df)
    
    assert len(rt) == 1
    assert rt.iloc[0]["qty"] == 10.0
    assert rt.iloc[0]["net_pnl"] == (10.0 * (110.0 - 100.0)) - 1.0 - 1.0  # 100 - 2 = 98
    assert rt.iloc[0]["net_pnl"] == 98.0

def test_aggregate_metrics_sanity():
    """
    Test aggregate metrics calculation (profit factor, win rate).
    """
    data = [
        {"timestamp": "2024-01-01", "side": "LONG", "qty": 1.0, "entry_price": 100.0, "exit_price": 110.0, 
         "entry_fee": 1.0, "exit_fee": 1.0, "gross_pnl": 10.0, "net_pnl": 8.0, "return_pct": 0.08, "holding_days": 1, "entry_time": "2024-01-01", "exit_time": "2024-01-02"},
        {"timestamp": "2024-01-03", "side": "LONG", "qty": 1.0, "entry_price": 100.0, "exit_price": 90.0, 
         "entry_fee": 1.0, "exit_fee": 1.0, "gross_pnl": -10.0, "net_pnl": -12.0, "return_pct": -0.12, "holding_days": 1, "entry_time": "2024-01-03", "exit_time": "2024-01-04"},
    ]
    rt = pd.DataFrame(data)
    rt["entry_time"] = pd.to_datetime(rt["entry_time"])
    rt["exit_time"] = pd.to_datetime(rt["exit_time"])
    
    metrics = aggregate_trade_metrics(rt)
    
    assert metrics["trades"] == 2
    assert metrics["win_rate_trades"] == 0.5
    assert metrics["gross_profit"] == 8.0
    assert metrics["gross_loss"] == -12.0
    assert metrics["profit_factor"] == 8.0 / 12.0
    assert metrics["total_net_pnl"] == -4.0

def test_compute_round_trips_empty():
    rt = compute_round_trips(pd.DataFrame())
    assert rt.empty
