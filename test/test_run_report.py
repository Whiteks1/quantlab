import json
import os
import pandas as pd
import pytest
from pathlib import Path
from quantlab.reporting.run_report import build_report, write_report

def test_run_report_grid(tmp_path):
    # Setup fake grid run dir
    run_dir = tmp_path / "20230305_220000_grid_abc123"
    run_dir.mkdir()
    
    meta = {
        "run_id": "20230305_220000_grid_abc123",
        "mode": "grid",
        "created_at": "2023-03-05T22:00:00",
        "git_commit": "abcdef123456",
        "python_version": "3.13.0",
        "config_path": "configs/test.yaml",
        "config_hash": "hash123"
    }
    with open(run_dir / "meta.json", "w") as f:
        json.dump(meta, f)
        
    experiments_data = [
        {"rsi_buy_max": 50, "rsi_sell_min": 70, "sharpe_simple": 1.5, "total_return": 0.2},
        {"rsi_buy_max": 60, "rsi_sell_min": 80, "sharpe_simple": 1.2, "total_return": 0.15},
    ]
    pd.DataFrame(experiments_data).to_csv(run_dir / "experiments.csv", index=False)
    
    # Execute
    md_path, json_path = write_report(str(run_dir))
    
    # Assert
    assert os.path.exists(md_path)
    assert os.path.exists(json_path)
    
    with open(json_path, "r") as f:
        report = json.load(f)
        
    assert report["header"]["run_id"] == "20230305_220000_grid_abc123"
    assert len(report["results"]) == 2
    assert report["results"][0]["rsi_buy_max"] == 50
    assert "artifacts" in report
    assert len(report["artifacts"]) > 0

def test_run_report_walkforward(tmp_path):
    # Setup fake walkforward run dir
    run_dir = tmp_path / "20230305_221000_walkforward_xyz789"
    run_dir.mkdir()
    
    meta = {
        "run_id": "20230305_221000_walkforward_xyz789",
        "mode": "walkforward",
        "created_at": "2023-03-05T22:10:00",
        "git_commit": "abcdef123456",
        "python_version": "3.13.0",
        "config_path": "configs/test_wf.yaml",
        "config_hash": "hash789"
    }
    with open(run_dir / "meta.json", "w") as f:
        json.dump(meta, f)
        
    oos_data = [
        {"split_name": "split1", "rsi_buy_max": 50, "sharpe_simple": 1.1},
    ]
    pd.DataFrame(oos_data).to_csv(run_dir / "oos_leaderboard.csv", index=False)
    
    summary_data = [
        {"split_name": "split1", "avg_test_sharpe_topk": 1.0},
    ]
    pd.DataFrame(summary_data).to_csv(run_dir / "walkforward_summary.csv", index=False)
    
    # Execute
    md_path, json_path = write_report(str(run_dir))
    
    # Assert
    assert os.path.exists(md_path)
    assert os.path.exists(json_path)
    
    with open(json_path, "r") as f:
        report = json.load(f)
        
    assert report["header"]["mode"] == "walkforward"
    assert len(report["oos_leaderboard"]) == 1
    assert report["summary"][0]["split_name"] == "split1"
    assert "artifacts" in report
    
    # We didn't create config_resolved.yaml here, let's create it and verify
    with open(run_dir / "config_resolved.yaml", "w") as f:
        f.write("key: value\n")
    _, json_path2 = write_report(str(run_dir))
    with open(json_path2, "r") as f:
        report2 = json.load(f)
    assert report2["config_resolved"]["key"] == "value"

def test_run_report_strict_json(tmp_path):
    run_dir = tmp_path / "strict_json"
    run_dir.mkdir()
    
    meta = {"mode": "grid", "run_id": "test"}
    with open(run_dir / "meta.json", "w") as f:
        json.dump(meta, f)
        
    # Data with NaN
    data = [{"metric": float('nan'), "value": float('inf')}]
    pd.DataFrame(data).to_csv(run_dir / "experiments.csv", index=False)
    
    # Execute
    _, json_path = write_report(str(run_dir))
    
    # Assert load works (json.load would fail if allow_nan=False and NaN exists)
    with open(json_path, "r") as f:
        # This will fail if NaN escaped sanitizer
        report = json.load(f)
        
    assert report["results"][0]["metric"] is None
    assert report["results"][0]["value"] is None
