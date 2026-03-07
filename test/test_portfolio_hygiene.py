import json
import pytest
import pandas as pd
from pathlib import Path
from quantlab.reporting.portfolio_report import _resolve_ticker, _get_dedup_key, aggregate_portfolio

def test_resolve_ticker_fallback():
    # Case 1: Ticker at top level
    assert _resolve_ticker({"ticker": "BTC"}) == "BTC"
    
    # Case 2: Ticker in candidate
    assert _resolve_ticker({"candidate": {"ticker": "ETH"}}) == "ETH"
    
    # Case 3: Ticker in candidate params
    assert _resolve_ticker({"candidate": {"params": {"ticker": "SOL"}}}) == "SOL"
    
    # Case 4: Missing ticker
    assert _resolve_ticker({}) == "N/A"
    assert _resolve_ticker({"ticker": ""}) == "N/A"

def test_dedup_key_stability():
    sess1 = {
        "source_run_id": "run_a",
        "ticker": "BTC",
        "strategy": "strat_1",
        "eval_start": "2023-01-01",
        "eval_end": "2023-01-02",
        "starting_cash": 10000.0,
        "ending_equity": 10500.0
    }
    key1 = _get_dedup_key(sess1)
    
    # Same data, slightly different types
    sess2 = sess1.copy()
    sess2["starting_cash"] = 10000 # int
    key2 = _get_dedup_key(sess2)
    
    assert key1 == key2

def test_aggregate_portfolio_with_dedup(tmp_path):
    # Create two duplicate sessions (same key) and one unique
    
    def create_mock_session(name, ticker, updated_at, pnl=500):
        d = tmp_path / name
        d.mkdir()
        state = {
            "session_id": name,
            "ticker": ticker,
            "candidate": {"strategy_name": "S1", "source_run_id": "R1"},
            "eval_start": "2023-01-01",
            "eval_end": "2023-01-10",
            "starting_cash": 10000.0,
            "updated_at": updated_at
        }
        with open(d / "portfolio_state.json", "w") as f:
            json.dump(state, f)
            
        df = pd.DataFrame([
            {"timestamp": "2023-01-01", "equity": 1.0},
            {"timestamp": "2023-01-10", "equity": 1.0 + (pnl/10000.0)}
        ])
        df.to_csv(d / "forward_equity_curve.csv", index=False)
        return d

    # DUPES: sess_a and sess_b have same dedup key (R1, BTC, S1, 2023-01-01, 2023-01-10, 10000, 10500)
    # sess_b is newer
    dir_a = create_mock_session("sess_a", "BTC", "2023-05-01T10:00:00")
    dir_b = create_mock_session("sess_b", "BTC", "2023-05-01T11:00:00")
    
    # UNIQUE
    dir_c = create_mock_session("sess_c", "ETH", "2023-05-01T10:00:00", pnl=200)
    
    payload = aggregate_portfolio([dir_a, dir_b, dir_c])
    
    # stats check
    stats = payload["scanning_stats"]
    assert stats["sessions_scanned"] == 3
    assert stats["sessions_included"] == 2 # sess_b (newer BTC) and sess_c (ETH)
    assert stats["sessions_collapsed_duplicates"] == 1
    
    # Top-level check
    assert payload["sessions_collapsed_duplicates"] == 1
    assert payload["sessions_included"] == 2
    session_ids = [c["session_id"] for c in payload["candidates"]]
    assert "sess_b" in session_ids
    assert "sess_c" in session_ids
    assert "sess_a" not in session_ids

def test_aggregate_portfolio_filtering(tmp_path):
    # Create one valid, one missing state, one empty equity
    
    d_valid = tmp_path / "valid"
    d_valid.mkdir()
    with open(d_valid / "portfolio_state.json", "w") as f:
        json.dump({"session_id": "v", "starting_cash": 1000}, f)
    pd.DataFrame([{"timestamp": "2023-01-01", "equity": 1.0}]).to_csv(d_valid / "forward_equity_curve.csv", index=False)
    
    d_no_state = tmp_path / "no_state"
    d_no_state.mkdir()
    # Missing state file
    
    d_empty_eq = tmp_path / "empty_eq"
    d_empty_eq.mkdir()
    with open(d_empty_eq / "portfolio_state.json", "w") as f:
        json.dump({"session_id": "e"}, f)
    pd.DataFrame(columns=["timestamp", "equity"]).to_csv(d_empty_eq / "forward_equity_curve.csv", index=False)
    
    payload = aggregate_portfolio([d_valid, d_no_state, d_empty_eq])
    
    stats = payload["scanning_stats"]
    assert stats["sessions_scanned"] == 3
    assert stats["sessions_included"] == 1
    assert stats["sessions_excluded_incomplete"] == 2
