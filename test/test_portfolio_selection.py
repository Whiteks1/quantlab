import json
import pytest
import pandas as pd
from pathlib import Path
from quantlab.reporting.portfolio_report import aggregate_portfolio, render_portfolio_md

def create_mock_session(tmp_path, name, returns, ticker="BTC", strategy="strat", source_run="run1", updated_at="2023-01-01T00:00:00Z"):
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    state = {
        "session_id": name,
        "ticker": ticker,
        "strategy_name": strategy,
        "source_run_id": source_run,
        "starting_cash": 10000.0,
        "eval_start": returns[0][0],
        "eval_end": returns[-1][0],
        "updated_at": updated_at
    }
    with open(d / "portfolio_state.json", "w") as f:
        json.dump(state, f)
        
    df = pd.DataFrame(returns, columns=["timestamp", "equity"])
    df.to_csv(d / "forward_equity_curve.csv", index=False)
    return d

def test_selection_ticker_strategy(tmp_path):
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0)], ticker="BTC", strategy="S1")
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0)], ticker="ETH", strategy="S1")
    s3 = create_mock_session(tmp_path, "s3", [("2023-01-01", 1.0)], ticker="BTC", strategy="S2")
    
    # Include BTC only
    payload = aggregate_portfolio([s1, s2, s3], include_tickers=["BTC"])
    assert payload["n_candidates"] == 2
    assert all(c["ticker"] == "BTC" for c in payload["candidates"])
    
    # Exclude S2
    payload = aggregate_portfolio([s1, s2, s3], exclude_strategies=["S2"])
    assert payload["n_candidates"] == 2
    assert all(c["strategy"] != "S2" for c in payload["candidates"])

def test_selection_performance(tmp_path):
    # s1: +20% return, -5% max dd
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 0.95), ("2023-01-03", 1.2)])
    # s2: +5% return, -15% max dd
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0), ("2023-01-02", 0.85), ("2023-01-03", 1.05)])
    
    # Min return 10%
    payload = aggregate_portfolio([s1, s2], min_return=0.10)
    assert payload["n_candidates"] == 1
    assert payload["candidates"][0]["session_id"] == "s1"
    
    # Max drawdown -10% (threshold -0.10)
    payload = aggregate_portfolio([s1, s2], max_drawdown=-0.10)
    assert payload["n_candidates"] == 1
    assert payload["candidates"][0]["session_id"] == "s1"

def test_selection_latest_per_source_run(tmp_path):
    # Same source_run, different update times
    s1 = create_mock_session(tmp_path, "s1_old", [("2023-01-01", 1.0)], source_run="R1", updated_at="2023-01-01T10:00:00Z")
    s2 = create_mock_session(tmp_path, "s1_new", [("2023-01-01", 1.1)], source_run="R1", updated_at="2023-01-01T12:00:00Z")
    s3 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0)], source_run="R2")
    
    payload = aggregate_portfolio([s1, s2, s3], latest_per_source_run=True)
    assert payload["n_candidates"] == 2
    ids = [c["session_id"] for c in payload["candidates"]]
    assert "s1_new" in ids
    assert "s1_old" not in ids
    assert "s2" in ids

def test_selection_top_n(tmp_path):
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.5)], ticker="T1") # +50%
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 1.0), ("2023-01-02", 1.2)], ticker="T2") # +20%
    s3 = create_mock_session(tmp_path, "s3", [("2023-01-01", 1.0), ("2023-01-02", 1.1)], ticker="T3") # +10%
    
    # Top 2 by total_return
    payload = aggregate_portfolio([s1, s2, s3], top_n=2, rank_metric="total_return")
    assert payload["n_candidates"] == 2
    ids = [c["session_id"] for c in payload["candidates"]]
    assert "s1" in ids
    assert "s2" in ids
    assert "s3" not in ids

def test_selection_rendering(tmp_path):
    """Rendering test: use a session that PASSES the filters so we can inspect the MD output."""
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0), ("2023-01-02", 1.1)], ticker="BTC")
    payload = aggregate_portfolio([s1], top_n=5, include_tickers=["BTC"])
    md = render_portfolio_md(payload)

    assert "## Selection Rules" in md
    assert "- **Top N:** 5" in md
    assert "- **Include Tickers:** BTC" in md
    assert "- **Sessions After Selection:** 1" in md


def test_empty_selection_raises(tmp_path):
    """When all sessions are eliminated by selection rules, a ValueError must be raised."""
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0)], ticker="BTC")
    s2 = create_mock_session(tmp_path, "s2", [("2023-01-01", 0.9)], ticker="ETH")

    # Filter to a ticker that doesn't exist — all sessions rejected
    with pytest.raises(ValueError, match="No portfolio sessions remain after applying selection rules"):
        aggregate_portfolio([s1, s2], include_tickers=["DOGE"])

    # Similarly via min_return threshold higher than any session
    with pytest.raises(ValueError, match="No portfolio sessions remain after applying selection rules"):
        aggregate_portfolio([s1, s2], min_return=99.0)

def test_pipeline_order_stability(tmp_path):
    """Verify scanning_stats counters are correct through hygiene → dedup → selection,
    and that filtering everything out raises ValueError."""
    # 1. Hygiene: s_bad has no required files (skipped)
    s_bad = tmp_path / "bad"
    s_bad.mkdir()

    # 2. Dedup: s1 and s1_dup share the same dedup key; only the newer survives
    s1 = create_mock_session(tmp_path, "s1", [("2023-01-01", 1.0)], ticker="BTC", strategy="S1", updated_at="2023-01-01T10:00:00")
    s1_dup = create_mock_session(tmp_path, "s1_dup", [("2023-01-01", 1.0)], ticker="BTC", strategy="S1", updated_at="2023-01-01T11:00:00")

    # 3. Selection: filter for ETH — nothing matches → must raise
    with pytest.raises(ValueError, match="No portfolio sessions remain after applying selection rules"):
        aggregate_portfolio([s_bad, s1, s1_dup], include_tickers=["ETH"])

    # 4. Confirm intermediate counters by using a filter that keeps the surviving session
    payload = aggregate_portfolio([s_bad, s1, s1_dup], include_tickers=["BTC"])
    stats = payload["scanning_stats"]
    assert stats["sessions_scanned"] == 3
    assert stats["sessions_excluded_incomplete"] == 1
    assert stats["sessions_after_hygiene"] == 2
    assert stats["sessions_collapsed_duplicates"] == 1
    assert stats["sessions_after_dedup"] == 1
    assert stats["sessions_after_selection"] == 1
    assert stats["sessions_included"] == 1
