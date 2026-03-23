"""Tests for src/quantlab/reporting/run_index.py (Stage J)."""

import json
import math
import pytest
from pathlib import Path

import pandas as pd

from quantlab.reporting.run_index import (
    scan_runs,
    load_run_summary,
    build_runs_index,
    render_runs_index_md,
    write_runs_index,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_meta(run_dir: Path, mode: str = "grid", run_id: str | None = None) -> None:
    """Write a minimal metadata.json into run_dir."""
    run_id = run_id or run_dir.name
    meta = {
        "run_id": run_id,
        "mode": mode,
        "created_at": "2023-03-05T22:00:00",
        "git_commit": "abc1234",
        "python_version": "3.13.0",
        "config_path": "configs/test.yaml",
        "config_hash": "testhash",
        "top10": [{"sharpe_simple": 1.5, "total_return": 0.2, "max_drawdown": -0.1, "trades": 10}],
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f)


def _make_report_json(run_dir: Path, sharpe: float = 1.0) -> None:
    """Write a minimal report.json into run_dir."""
    report = {
        "header": {
            "run_id": run_dir.name,
            "mode": "grid",
            "created_at": "2023-03-05T22:00:00",
            "git_commit": "def5678",
        },
        "results": [
            {"sharpe_simple": sharpe, "total_return": 0.1, "max_drawdown": -0.05, "trades": 8},
        ],
        "config_resolved": {"ticker": "BTC-USD", "start": "2023-01-01", "end": "2024-01-01"},
    }
    with open(run_dir / "report.json", "w") as f:
        json.dump(report, f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_scan_runs_finds_valid_dirs(tmp_path):
    """Only directories with canonical or legacy run artifacts should be yielded."""
    valid1 = tmp_path / "run_001"
    valid1.mkdir()
    _make_meta(valid1)

    valid2 = tmp_path / "run_002"
    valid2.mkdir()
    _make_report_json(valid2)

    empty = tmp_path / "run_empty"
    empty.mkdir()

    txt_file = tmp_path / "not_a_dir.txt"
    txt_file.write_text("noise")

    found = list(scan_runs(tmp_path))
    found_names = {p.name for p in found}

    assert "run_001" in found_names
    assert "run_002" in found_names
    assert "run_empty" not in found_names
    assert len(found) == 2


def test_scan_runs_nonexistent_root(tmp_path):
    """scan_runs must not crash on a missing root; just yields nothing."""
    result = list(scan_runs(tmp_path / "does_not_exist"))
    assert result == []


def test_load_run_summary_from_report_json(tmp_path):
    """load_run_summary should prefer report.json over metadata.json."""
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    _make_meta(run_dir, run_id="from_meta")
    _make_report_json(run_dir, sharpe=2.0)

    summary = load_run_summary(run_dir)

    assert summary["path"] == str(run_dir)
    assert summary["sharpe_simple"] == 2.0
    # report.json header wins over metadata.json for git_commit
    assert summary["git_commit"] == "def5678"
    # config_resolved should supply ticker
    assert summary["ticker"] == "BTC-USD"


def test_load_run_summary_fallback_to_meta(tmp_path):
    """When report.json is absent, load_run_summary must use metadata.json."""
    run_dir = tmp_path / "run_b"
    run_dir.mkdir()
    _make_meta(run_dir, mode="walkforward", run_id="meta_only_run")

    summary = load_run_summary(run_dir)

    assert summary["run_id"] == "meta_only_run"
    assert summary["mode"] == "walkforward"
    assert summary["git_commit"] == "abc1234"
    # top10 metrics should be unpacked
    assert summary["sharpe_simple"] == 1.5
    assert summary["total_return"] == 0.2


def test_load_run_summary_missing_dir(tmp_path):
    """A completely empty / invalid directory should not raise."""
    empty_dir = tmp_path / "empty_run"
    empty_dir.mkdir()
    summary = load_run_summary(empty_dir)
    assert summary["path"] == str(empty_dir)
    # All metrics should be None rather than raising
    assert summary["sharpe_simple"] is None


def test_build_runs_index_multiple(tmp_path):
    """build_runs_index must collect summaries for all valid run dirs."""
    for i in range(3):
        d = tmp_path / f"run_{i:03d}"
        d.mkdir()
        _make_meta(d, run_id=f"run_{i:03d}")

    # Add one invalid (no meta)
    (tmp_path / "garbage").mkdir()

    payload = build_runs_index(tmp_path)

    assert payload["n_runs"] == 3
    assert len(payload["runs"]) == 3
    run_ids = {r["run_id"] for r in payload["runs"]}
    assert "run_000" in run_ids
    assert "generated_at" in payload


def test_write_runs_index_creates_artifacts(tmp_path):
    """write_runs_index must create CSV + JSON + MD, all parseable."""
    for name in ("alpha", "beta"):
        d = tmp_path / name
        d.mkdir()
        _make_report_json(d, sharpe=1.0 if name == "alpha" else 2.0)

    csv_p, json_p, md_p = write_runs_index(tmp_path)

    # Files exist
    assert Path(csv_p).exists()
    assert Path(json_p).exists()
    assert Path(md_p).exists()

    # JSON is strict-loadable (no NaN / Inf)
    with open(json_p) as f:
        data = json.load(f)
    assert data["n_runs"] == 2

    # CSV is readable by pandas
    df = pd.read_csv(csv_p)
    assert len(df) == 2

    # Markdown has required headings
    md_content = Path(md_p).read_text(encoding="utf-8")
    assert "# Runs Index" in md_content
    assert "## Summary" in md_content
    assert "## Runs" in md_content


def test_runs_index_strict_json_no_nan(tmp_path):
    """NaN metrics must be serialised as null so JSON is strict-valid."""
    run_dir = tmp_path / "nan_run"
    run_dir.mkdir()
    # Write a report.json that has NaN in results
    report = {
        "header": {"run_id": "nan_run", "mode": "grid", "created_at": "", "git_commit": ""},
        "results": [{"sharpe_simple": float("nan"), "total_return": float("inf")}],
        "config_resolved": {},
    }
    with open(run_dir / "report.json", "w") as f:
        json.dump(report, f)

    _, json_p, _ = write_runs_index(tmp_path)

    # Standard json.load must succeed (no NaN literals in the file)
    with open(json_p) as f:
        data = json.load(f)
    # The nan/inf from the source became None in our summary
    run_entry = data["runs"][0]
    assert run_entry["sharpe_simple"] is None
    assert run_entry["total_return"] is None
