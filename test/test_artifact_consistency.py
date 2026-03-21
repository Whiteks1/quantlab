import json
import os
import pandas as pd
import pytest
from pathlib import Path

from quantlab.reporting.run_report import write_report as write_run_report
from quantlab.reporting.forward_report import write_forward_report
from quantlab.reporting.report import write_report as write_legacy_report

def verify_summary(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "summary" in data, f"Missing 'summary' in {report_path}"
    summary = data["summary"]
    
    # Check for approved repo-native keys (Issue #22)
    expected_keys = ["total_return", "sharpe_simple", "max_drawdown", "trades", "win_rate"]
    for key in expected_keys:
        assert key in summary, f"Missing '{key}' in summary of {report_path}"

def test_run_report_dual_writing(tmp_path):
    run_dir = tmp_path / "run_test"
    run_dir.mkdir()
    
    # Minimal meta for build_report
    meta = {
        "run_id": "run_test_id",
        "mode": "grid",
        "created_at": "2026-03-21T15:00:00",
        "git_commit": "abc",
        "python_version": "3.10",
        "config_path": "config.yaml",
        "config_hash": "hash"
    }
    with open(run_dir / "meta.json", "w") as f:
        json.dump(meta, f)
    
    # Execute
    write_run_report(str(run_dir))
    
    # Assert dual writing
    assert os.path.exists(run_dir / "report.json"), "Canonical report.json missing"
    assert os.path.exists(run_dir / "run_report.json"), "Legacy run_report.json missing"
    
    # Verify summary schema
    verify_summary(run_dir / "report.json")
    verify_summary(run_dir / "run_report.json")

def test_forward_report_dual_writing(tmp_path):
    fwd_dir = tmp_path / "fwd_test"
    fwd_dir.mkdir()
    
    # Minimal portfolio_state for build_forward_report
    state = {
        "session_id": "fwd_test_id",
        "mode": "forward_paper",
        "current_equity": 10500.0,
        "starting_cash": 10000.0,
        "created_at": "2026-03-21T15:00:00"
    }
    with open(fwd_dir / "portfolio_state.json", "w") as f:
        json.dump(state, f)
        
    # Execute
    write_forward_report(str(fwd_dir))
    
    # Assert dual writing
    assert os.path.exists(fwd_dir / "report.json"), "Canonical report.json missing"
    assert os.path.exists(fwd_dir / "forward_report.json"), "Legacy forward_report.json missing"
    
    # Verify summary schema
    verify_summary(fwd_dir / "report.json")
    verify_summary(fwd_dir / "forward_report.json")

def test_legacy_report_summary_integration(tmp_path):
    out_dir = tmp_path / "legacy_test"
    out_dir.mkdir()
    
    trades_path = out_dir / "trades.csv"
    # Create empty trades file with required columns
    cols = ["timestamp", "ticker", "side", "qty", "price", "equity_after", "fee", "close", "exec_price"]
    pd.DataFrame(columns=cols).to_csv(trades_path, index=False)
    
    json_path = out_dir / "report.json"
    
    # Execute
    write_legacy_report(str(trades_path), out_json_path=str(json_path))
    
    # Assert
    assert os.path.exists(json_path)
    
    # Verify summary schema exists even if empty
    verify_summary(json_path)
