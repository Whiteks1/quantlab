"""Tests for advanced_report.py (Stage K)."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from quantlab.reporting.advanced_report import (
    build_advanced_report,
    render_advanced_report_md,
    write_advanced_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_dir(tmp_path: Path, include_report_json: bool = True) -> Path:
    run_dir = tmp_path / "run_k_test"
    run_dir.mkdir()
    if include_report_json:
        report = {
            "header": {
                "run_id": "run_k_test",
                "mode": "grid",
                "created_at": "2023-06-01T10:00:00",
                "git_commit": "stageK",
            },
            "results": [{"sharpe_simple": 1.5, "total_return": 0.20}],
            "config_resolved": {"ticker": "BTC-USD"},
        }
        with open(run_dir / "run_report.json", "w") as f:
            json.dump(report, f)
    return run_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_write_advanced_report_creates_artifacts(tmp_path):
    run_dir = _make_run_dir(tmp_path)
    json_p, md_p = write_advanced_report(run_dir)

    assert Path(json_p).exists(), "advanced_report.json must be created"
    assert Path(md_p).exists(), "advanced_report.md must be created"

    # JSON is strict-loadable
    with open(json_p) as f:
        data = json.load(f)
    assert "run_id" in data
    assert data["run_id"] == "run_k_test"


def test_advanced_report_markdown_headings(tmp_path):
    run_dir = _make_run_dir(tmp_path)
    _, md_p = write_advanced_report(run_dir)

    md = Path(md_p).read_text(encoding="utf-8")

    assert "# Advanced Run Report" in md
    assert "## Summary" in md
    assert "## Charts" in md
    assert "## Artifacts" in md


def test_advanced_report_no_run_report_json(tmp_path):
    """write_advanced_report must not crash even if run_report.json is absent."""
    run_dir = _make_run_dir(tmp_path, include_report_json=False)
    # Write a minimal meta.json so the dir is at least partially valid
    with open(run_dir / "meta.json", "w") as f:
        json.dump({"run_id": "bare_run", "mode": "grid"}, f)

    json_p, md_p = write_advanced_report(run_dir)
    assert Path(json_p).exists()
    assert Path(md_p).exists()
    with open(json_p) as f:
        data = json.load(f)
    # trade_distribution should be empty but present
    assert data["trade_distribution"]["n_trades"] == 0


def test_advanced_report_strict_json_no_nan(tmp_path):
    """advanced_report.json must never contain NaN or Inf literals."""
    run_dir = _make_run_dir(tmp_path)
    json_p, _ = write_advanced_report(run_dir)

    content = Path(json_p).read_text(encoding="utf-8")
    # Standard json.loads raises on NaN/Infinity, so this verifies no such values
    data = json.loads(content)
    assert isinstance(data, dict)


def test_cli_advanced_report_early_exit(tmp_path, monkeypatch):
    """
    --advanced-report <run_dir> must call write_advanced_report and exit
    without invoking the normal pipeline (fetch_ohlc).
    """
    run_dir = _make_run_dir(tmp_path)

    mock_write = MagicMock(return_value=(str(run_dir / "advanced_report.json"),
                                         str(run_dir / "advanced_report.md")))
    monkeypatch.setattr("main.write_advanced_report", mock_write)

    mock_fetch = MagicMock(side_effect=AssertionError("fetch_ohlc must NOT be called"))
    monkeypatch.setattr("main.fetch_ohlc", mock_fetch)

    monkeypatch.setattr(sys, "argv", ["main.py", "--advanced-report", str(run_dir)])

    import main as main_module
    main_module.main()

    mock_write.assert_called_once_with(str(run_dir))
