"""Tests for advanced_report.py (Stage K / K.3)."""

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


def _minimal_payload(
    sortino: float | None = 1.5,
    calmar: float | None = 2.0,
    tw: dict | None = None,
) -> dict:
    """Return a minimal payload dict for render_advanced_report_md tests."""
    return {
        "run_id": "test_render",
        "mode": "grid",
        "created_at": "2023-01-01T00:00:00",
        "equity_metrics": {
            "total_return": 0.2,
            "cagr": 0.18,
            "sharpe": 1.2,
            "sortino": sortino,
            "annualized_volatility": 0.15,
            "n_days": 252,
        },
        "drawdown_metrics": {
            "max_drawdown": -0.12,
            "avg_drawdown": -0.04,
            "calmar": calmar,
            "longest_dd_days": 30,
            "n_drawdown_periods": 5,
        },
        "trade_distribution": {"n_trades": 0},
        "time_window_metrics": tw if tw is not None else {},
        "charts": [],
        "artifacts": [],
        "top_result_summary": {},
    }


# ---------------------------------------------------------------------------
# Pre-existing tests (kept for regression)
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


# ---------------------------------------------------------------------------
# K.3: Markdown rendering of None / unavailable metrics
# ---------------------------------------------------------------------------

class TestRenderNoneMetrics:
    """render_advanced_report_md must handle None metrics gracefully."""

    def test_sortino_none_shows_na(self):
        """Sortino=None → Markdown should contain 'N/A'."""
        payload = _minimal_payload(sortino=None)
        md = render_advanced_report_md(payload)
        assert "N/A" in md, "Expected 'N/A' in Markdown when sortino is None"

    def test_calmar_none_shows_na(self):
        """Calmar=None → Markdown should contain 'N/A'."""
        payload = _minimal_payload(calmar=None)
        md = render_advanced_report_md(payload)
        assert "N/A" in md, "Expected 'N/A' in Markdown when calmar is None"

    def test_sortino_none_annotated(self):
        """Sortino=None should carry an explanatory annotation in the table."""
        payload = _minimal_payload(sortino=None)
        md = render_advanced_report_md(payload)
        assert "insufficient data" in md.lower(), (
            "Expected annotation explaining why sortino is N/A"
        )

    def test_calmar_none_annotated(self):
        """Calmar=None should carry an explanatory annotation in the table."""
        payload = _minimal_payload(calmar=None)
        md = render_advanced_report_md(payload)
        assert "drawdown too small" in md.lower() or "insufficient" in md.lower(), (
            "Expected annotation explaining why calmar is N/A"
        )

    def test_sortino_finite_shows_number(self):
        """When sortino has a real value it should appear as a formatted number."""
        payload = _minimal_payload(sortino=2.345)
        md = render_advanced_report_md(payload)
        assert "2.345" in md, "Expected formatted sortino value in Markdown"

    def test_calmar_finite_shows_number(self):
        """When calmar has a real value it should appear as a formatted number."""
        payload = _minimal_payload(calmar=3.142)
        md = render_advanced_report_md(payload)
        assert "3.142" in md, "Expected formatted calmar value in Markdown"


class TestRenderInsufficientMonthly:
    """Time-window section must render a note for insufficient monthly data."""

    def test_insufficient_data_renders_note(self):
        """insufficient_data=True → note block rendered, no misleading table."""
        tw = {
            "n_months": 1,
            "min_months_required": 3,
            "monthly_returns": [],
            "insufficient_data": True,
            "note": "Only 1 complete monthly period(s) available; at least 3 are needed.",
        }
        payload = _minimal_payload(tw=tw)
        md = render_advanced_report_md(payload)
        assert "insufficient" in md.lower() or "Only 1" in md, (
            "Expected note about insufficient monthly data"
        )
        # Should NOT show best_month / worst_month values
        assert "best_month" not in md
        assert "worst_month" not in md

    def test_sufficient_data_renders_table(self):
        """When n_months >= _MIN_MONTHS the full table should appear."""
        tw = {
            "n_months": 5,
            "best_month": 0.05,
            "worst_month": -0.03,
            "positive_months_pct": 0.6,
            "monthly_returns": [
                {"month": "2023-01", "return": 0.05},
                {"month": "2023-02", "return": -0.02},
            ],
        }
        payload = _minimal_payload(tw=tw)
        md = render_advanced_report_md(payload)
        # Best/worst months should appear formatted as %
        assert "5.0%" in md or "5%" in md, "Expected best_month formatted as %"

    def test_monthly_best_worst_formatted_as_pct(self):
        """Best/worst month values must be % formatted, not raw floats."""
        tw = {
            "n_months": 6,
            "best_month": 0.0432,
            "worst_month": -0.0218,
            "positive_months_pct": 0.667,
            "monthly_returns": [],
        }
        payload = _minimal_payload(tw=tw)
        md = render_advanced_report_md(payload)
        # Raw float e.g. "0.0432" should NOT appear; "4.3%" should
        assert "0.0432" not in md, "best_month must not appear as raw float"
        assert "%" in md, "best/worst month must be formatted as percentage"


class TestRenderStrictJson:
    """build_advanced_report and write_advanced_report must stay JSON-safe."""

    def test_payload_survives_allow_nan_false(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        payload = build_advanced_report(run_dir)
        serialised = json.dumps(payload, allow_nan=False)
        data = json.loads(serialised)
        assert "run_id" in data

    def test_written_json_no_nan(self, tmp_path):
        run_dir = _make_run_dir(tmp_path)
        json_p, _ = write_advanced_report(run_dir)
        content = Path(json_p).read_text(encoding="utf-8")
        data = json.loads(content)  # raises if NaN/Inf present
        assert isinstance(data, dict)
