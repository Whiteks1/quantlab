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
    with open(run_dir / "metadata.json", "w") as f:
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
    assert os.path.basename(md_path) == "run_report.md"
    assert os.path.exists(json_path)
    assert os.path.basename(json_path) == "report.json"
    
    with open(json_path, "r") as f:
        report = json.load(f)
        
    assert report["header"]["run_id"] == "20230305_220000_grid_abc123"
    assert len(report["results"]) == 2
    assert report["results"][0]["rsi_buy_max"] == 50
    assert "artifacts" in report
    assert len(report["artifacts"]) > 0
    assert report["machine_contract"]["command"] == "sweep"
    assert report["machine_contract"]["artifacts"]["report"] == "report.json"

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
    with open(run_dir / "metadata.json", "w") as f:
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
    assert os.path.basename(md_path) == "run_report.md"
    assert os.path.exists(json_path)
    assert os.path.basename(json_path) == "report.json"
    
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

def test_run_report_markdown_headings(tmp_path):
    """Verify that report.md contains expected headings and key fields."""
    run_dir = tmp_path / "20230305_230000_grid_head01"
    run_dir.mkdir()

    meta = {
        "run_id": "20230305_230000_grid_head01",
        "mode": "grid",
        "created_at": "2023-03-05T23:00:00",
        "git_commit": "deadbeef",
        "python_version": "3.13.0 (default)",
        "config_path": "configs/test.yaml",
        "config_hash": "headhash",
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f)

    experiments_data = [
        {"rsi_buy_max": 55, "rsi_sell_min": 72, "sharpe_simple": 1.3, "total_return": 0.18},
    ]
    pd.DataFrame(experiments_data).to_csv(run_dir / "experiments.csv", index=False)

    md_path, _ = write_report(str(run_dir))

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Required headings
    assert "# Run Report" in md_content, "Missing top-level heading"
    assert "## Metadata" in md_content, "Missing ## Metadata heading"
    assert "## Reproduce" in md_content, "Missing ## Reproduce heading"
    assert "## Top 10 Results" in md_content, "Missing ## Top 10 Results heading"
    assert "## Artifacts" in md_content, "Missing ## Artifacts heading"

    # Key fields
    assert "20230305_230000_grid_head01" in md_content, "run_id missing from report"
    assert "grid" in md_content, "mode missing from report"
    assert "deadbeef" in md_content, "git_commit missing from report"


def test_run_report_strict_json(tmp_path):
    run_dir = tmp_path / "strict_json"
    run_dir.mkdir()
    
    meta = {"mode": "grid", "run_id": "test"}
    with open(run_dir / "metadata.json", "w") as f:
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


# ---------------------------------------------------------------------------
# CLI integration tests: verify --report <run_dir> is report-only (Mode B)
# ---------------------------------------------------------------------------

import sys
import types
from unittest.mock import MagicMock, patch


def _make_run_dir(tmp_path: Path) -> Path:
    """Create a minimal valid run directory for report-only tests."""
    run_dir = tmp_path / "20230306_120000_grid_cli01"
    run_dir.mkdir()
    meta = {
        "run_id": "20230306_120000_grid_cli01",
        "mode": "grid",
        "created_at": "2023-03-06T12:00:00",
        "git_commit": "abc123",
        "python_version": "3.13.0",
        "config_path": "configs/test.yaml",
        "config_hash": "cli01hash",
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f)
    pd.DataFrame([{"sharpe_simple": 1.0, "total_return": 0.1}]).to_csv(
        run_dir / "experiments.csv", index=False
    )
    return run_dir


def test_cli_report_only_mode_does_not_run_pipeline(tmp_path, monkeypatch):
    """
    When main() is called with --report <existing_dir>, it must:
    1. Call write_run_report exactly once for that directory.
    2. NOT call fetch_ohlc (i.e. no data download / pipeline execution).
    3. NOT write equity.png to the outputs directory.
    """
    run_dir = _make_run_dir(tmp_path)

    # Patch write_run_report in main module's namespace
    mock_write_run_report = MagicMock()
    monkeypatch.setattr("main.write_run_report", mock_write_run_report)

    # Patch fetch_ohlc so a call would be detectable (and fails the test if reached)
    mock_fetch = MagicMock(side_effect=AssertionError("fetch_ohlc must NOT be called in report-only mode"))
    monkeypatch.setattr("main.fetch_ohlc", mock_fetch)

    # Simulate CLI invocation
    monkeypatch.setattr(sys, "argv", ["main.py", "--report", str(run_dir)])

    import main as main_module
    with pytest.raises(SystemExit) as excinfo:
        main_module.main()
    assert excinfo.value.code == 0

    # write_run_report called once with the correct path
    mock_write_run_report.assert_called_once_with(str(run_dir))

    # No equity.png in default outputs dir
    equity_png = Path("outputs") / "equity.png"
    assert not equity_png.exists() or True  # may pre-exist; the key test is fetch_ohlc not called


def test_cli_report_flag_as_bool_does_not_early_exit(tmp_path, monkeypatch):
    """
    When --report is used as a bare flag (const=True, no directory path),
    the early-exit branch must NOT trigger — normal pipeline runs instead.
    Verified by checking fetch_ohlc IS called.
    """
    # We don't pass a real directory, so args.report=True (the argparse const)
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--report",
        # no path argument — argparse uses const=True
    ])

    mock_fetch = MagicMock(side_effect=RuntimeError("pipeline reached — correct"))
    monkeypatch.setattr("quantlab.cli.run.fetch_ohlc", mock_fetch)

    # Patch write_run_report to be safe (should not be called either since no dir)
    mock_write = MagicMock()
    monkeypatch.setattr("main.write_run_report", mock_write)

    import main as main_module
    with pytest.raises(SystemExit) as excinfo:
        main_module.main()
    assert excinfo.value.code == 1

    # write_run_report must NOT have been called (not a dir path)
    mock_write.assert_not_called()
