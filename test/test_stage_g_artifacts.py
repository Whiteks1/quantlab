import os
import json
import yaml
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from quantlab.experiments.runner import make_run_dir, run_sweep, fetch_ohlc_cached

def newest_run_dir(base: Path) -> Path:
    dirs = [p for p in base.iterdir() if p.is_dir()]
    assert dirs, f"No run directories created under {base}"
    return max(dirs, key=lambda p: p.stat().st_mtime)

def test_make_run_dir(tmp_path):
    base = tmp_path / "runs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text("ticker: ETH-USD")
    
    run_dir = make_run_dir(base=str(base), mode="test", config_path=str(config_path))
    
    assert run_dir.exists()
    assert str(base) in str(run_dir)
    assert "_test_" in run_dir.name

def test_grid_artifacts(tmp_path):
    # Setup minimal config
    config = {
        "ticker": "ETH-USD",
        "start": "2023-01-01",
        "end": "2023-01-05",
        "interval": "1d",
        "param_grid": {
            "rsi_buy_max": [60],
            "rsi_sell_min": [70]
        }
    }
    config_path = tmp_path / "grid_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
        
    out_dir = tmp_path / "run_grid"
    
    # Mock dependencies to avoid network/heavy logic
    with patch("quantlab.experiments.runner.fetch_ohlc_cached") as mock_fetch, \
         patch("quantlab.experiments.runner.add_indicators") as mock_ind, \
         patch("quantlab.experiments.runner.run_backtest") as mock_bt, \
         patch("quantlab.experiments.runner.run_paper_broker") as mock_paper:
        
        # Mock data
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [95, 96, 97],
            "close": [102, 103, 104],
            "volume": [1000, 1100, 1200]
        }, index=pd.date_range("2023-01-01", periods=3))
        mock_fetch.return_value = df
        mock_ind.return_value = df.assign(ma20=100, rsi=50)
        
        mock_bt.return_value = pd.DataFrame({
            "equity": [1000, 1010, 1020],
            "position": [0, 1, 1],
            "trade": [0, 1, 0],
            "strategy_ret_net": [0.0, 0.01, 0.01]
        }, index=df.index)
        mock_paper.return_value = pd.DataFrame() # No trades
        
        run_sweep(str(config_path), out_dir=str(out_dir))
        
    # Check artifacts in nested run dir
    run_dir = newest_run_dir(out_dir)
    assert (run_dir / "experiments.csv").exists()
    assert (run_dir / "leaderboard.csv").exists()
    assert (run_dir / "meta.json").exists()
    assert (run_dir / "config_resolved.yaml").exists()
    
    with open(run_dir / "meta.json", "r") as f:
        meta = json.load(f)
        assert meta["mode"] == "grid"
        assert "run_id" in meta

def test_ohlc_caching(tmp_path):
    cache_dir = tmp_path / "cache"
    ticker = "BTC-USD"
    start = "2023-01-01"
    end = "2023-01-10"
    
    idx = pd.date_range("2023-01-01", periods=3)
    idx.freq = None  # Parquet loading loses 'freq', making assert_frame_equal fail
    df_mock = pd.DataFrame({"close": [1, 2, 3]}, index=idx)
    
    with patch("quantlab.experiments.runner.fetch_ohlc") as mock_fetch:
        mock_fetch.return_value = df_mock
        
        # 1st call: should hit fetch_ohlc
        res1 = fetch_ohlc_cached(ticker, start, end, cache_dir=str(cache_dir))
        assert mock_fetch.call_count == 1
        assert (cache_dir / f"BTC_USD_{start}_{end}_1d.parquet").exists()
        
        # 2nd call: should hit cache
        res2 = fetch_ohlc_cached(ticker, start, end, cache_dir=str(cache_dir))
        assert mock_fetch.call_count == 1
        pd.testing.assert_frame_equal(res1, res2)


def test_walkforward_artifacts(tmp_path):
    # Setup walkforward config
    config = {
        "ticker": "ETH-USD",
        "start": "2023-01-01",
        "end": "2023-01-31",
        "interval": "1d",
        "splits": [
            {
                "name": "split1",
                "train": {"start": "2023-01-01", "end": "2023-01-10"},
                "test": {"start": "2023-01-11", "end": "2023-01-15"}
            }
        ],
        "param_grid": {"rsi_buy_max": [60]},
        "selection": {"top_k": 1}
    }
    config_path = tmp_path / "wf_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
        
    out_dir = tmp_path / "run_wf"
    
    # Mock everything in the pipeline
    with patch("quantlab.experiments.runner.fetch_ohlc_cached") as mock_fetch, \
         patch("quantlab.experiments.runner.add_indicators") as mock_ind, \
         patch("quantlab.experiments.runner.run_backtest") as mock_bt, \
         patch("quantlab.experiments.runner.run_paper_broker") as mock_paper:
        
        df = pd.DataFrame({"close": [1, 2, 3]}, index=pd.date_range("2023-01-01", periods=3))
        mock_fetch.return_value = df
        mock_ind.return_value = df.assign(ma20=1, rsi=50)
        mock_bt.return_value = pd.DataFrame({
            "equity": [1000, 1010],
            "position": [0, 1],
            "trade": [0, 1],
            "strategy_ret_net": [0, 0.01]
        }, index=df.index[:2])
        mock_paper.return_value = pd.DataFrame()
        
        run_sweep(str(config_path), out_dir=str(out_dir))
        
    # Check artifacts in nested run dir
    run_dir = newest_run_dir(out_dir)
    assert (run_dir / "walkforward.csv").exists()
    assert (run_dir / "walkforward_summary.csv").exists()
    assert (run_dir / "oos_leaderboard.csv").exists()
    assert (run_dir / "meta.json").exists()
    assert (run_dir / "config_resolved.yaml").exists()
    
    with open(run_dir / "meta.json", "r") as f:
        meta = json.load(f)
        assert meta["mode"] == "walkforward"
        # Check specific walkforward meta fields
        assert "n_train_runs" in meta
        assert "n_selected" in meta
        assert "n_test_runs" in meta
