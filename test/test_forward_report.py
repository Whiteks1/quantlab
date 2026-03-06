"""Tests for reporting/forward_report.py (Stage L)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantlab.reporting.forward_report import (
    build_forward_report,
    render_forward_report_md,
    write_forward_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = np.cumprod(1 + rng.normal(0.0005, 0.015, n)) * 100
    return pd.DataFrame({
        "open": close * 0.999, "high": close * 1.005,
        "low": close * 0.995, "close": close,
        "volume": rng.integers(1_000, 100_000, n).astype(float),
    }, index=pd.date_range("2023-01-01", periods=n, freq="B"))


def _make_forward_artifacts(tmp_path: Path, with_trades: bool = True) -> Path:
    """Populate a forward eval output dir with minimal valid artifacts."""
    from quantlab.execution.forward_eval import (
        CandidateConfig, run_forward_evaluation, write_forward_eval_artifacts,
    )

    candidate = CandidateConfig(
        strategy_name="rsi_ma_cross_v2",
        params={"rsi_buy_max": 60.0, "rsi_sell_min": 75.0, "cooldown_days": 0},
        fee_rate=0.002,
        slippage_bps=8.0,
        source_run_id="test_run_fwd",
        source_run_dir=str(tmp_path),
        selection_metric="sharpe_simple",
        selection_value=1.2,
        ticker="ETH-USD",
        interval="1d",
    )

    if with_trades:
        df = _make_ohlcv(200)
    else:
        n = 150
        df = pd.DataFrame({
            "open": [100.0] * n, "high": [101.0] * n,
            "low": [99.0] * n, "close": [100.0] * n, "volume": [1000.0] * n,
        }, index=pd.date_range("2023-01-01", periods=n, freq="B"))

    result = run_forward_evaluation(candidate, df, initial_cash=10_000.0,
                                     eval_start="2023-01-01", eval_end="2023-12-31")
    write_forward_eval_artifacts(result, tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# build_forward_report
# ---------------------------------------------------------------------------

class TestBuildForwardReport:

    def test_basic_payload_keys(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        assert "session_id" in payload
        assert "mode" in payload
        assert "candidate" in payload
        assert "portfolio_state" in payload
        assert "summary" in payload
        assert "artifacts" in payload
        assert "warmup" in payload
        warmup = payload["warmup"]
        assert "bars_fetched_segment" in warmup
        assert "warmup_bars_segment" in warmup
        assert "bars_evaluated_segment" in warmup
        assert "bars_fetched_total" in warmup
        assert "warmup_bars_total" in warmup
        assert "bars_evaluated_total" in warmup

    def test_payload_strict_json(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        serialised = json.dumps(payload, allow_nan=False)
        data = json.loads(serialised)
        assert isinstance(data, dict)

    def test_summary_has_expected_keys(self, tmp_path):
        out = _make_forward_artifacts(tmp_path, with_trades=True)
        payload = build_forward_report(out)
        summary = payload.get("summary", {})
        assert "total_return" in summary
        assert "max_drawdown" in summary
        assert "n_trades" in summary

    def test_no_trades_payload_still_valid(self, tmp_path):
        """Flat data → 0 trades → payload still JSON-safe."""
        out = _make_forward_artifacts(tmp_path, with_trades=False)
        payload = build_forward_report(out)
        assert payload["summary"]["n_trades"] == 0
        json.dumps(payload, allow_nan=False)

    def test_empty_dir_returns_minimal_payload(self, tmp_path):
        """Empty dir (no artifacts) must not crash."""
        out = tmp_path / "empty_fwd"
        out.mkdir()
        payload = build_forward_report(out)
        assert isinstance(payload, dict)
        json.dumps(payload, allow_nan=False)

    def test_artifacts_list_includes_files(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        names = [a["file"] for a in payload.get("artifacts", [])]
        assert "portfolio_state.json" in names
        assert "forward_trades.csv" in names
        assert "forward_equity_curve.csv" in names

    def test_build_forward_report_fallback_resumed(self, tmp_path):
        """
        Verify that in a resumed session with missing last_segment fields,
        the report does NOT misleadingly show total bars as segment bars.
        """
        out_dir = tmp_path / "legacy_resume"
        out_dir.mkdir()
        
        # 1. State with resume_count but NO last_segment fields
        state = {
            "session_id": "legacy_123",
            "resume_count": 1,
            "total_bars_evaluated": 100,
            "bars_fetched": 500,
            "warmup_bars": 100
        }
        with open(out_dir / "portfolio_state.json", "w") as f:
            json.dump(state, f)
            
        # 2. Equity curve with 100 rows
        pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=100),
            "equity": [1.0] * 100
        }).to_csv(out_dir / "forward_equity_curve.csv", index=False)
        
        payload = build_forward_report(out_dir)
        w = payload["warmup"]
        
        # Should NOT fallback to 100 (total) for segment if it's a resume but info is missing
        assert w["bars_evaluated_segment"] == 0
        assert w["bars_evaluated_total"] == 100


# ---------------------------------------------------------------------------
# render_forward_report_md
# ---------------------------------------------------------------------------

class TestRenderForwardReportMd:

    def test_required_headings(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        md = render_forward_report_md(payload)
        assert "# Forward Evaluation Report" in md
        assert "## Candidate" in md
        assert "## Portfolio Summary" in md
        assert "## Closed Trade Summary" in md
        assert "## Charts" in md
        assert "## Artifacts" in md
        assert "Latest Segment" in md
        assert "Bars Fetched (Latest Segment)" in md

    def test_open_position_section_rendered(self, tmp_path):
        """Verify Open Position section appears only when has_open_position is True."""
        # 1. No open position
        payload = {
            "session_id": "op1",
            "portfolio_state": {"has_open_position": False},
            "summary": {"n_trades": 0},
            "performance": {},
            "warmup": {
                "bars_fetched_segment": 0,
                "warmup_bars_segment": 0,
                "bars_evaluated_segment": 0
            },
            "charts": [],
            "artifacts": [],
        }
        md = render_forward_report_md(payload)
        assert "## Open Position" not in md
        
        # 2. With open position
        payload["portfolio_state"] = {
            "has_open_position": True,
            "open_position_qty": 0.5,
            "open_position_entry_price": 2000.0,
            "open_position_mark_price": 2100.0,
            "open_position_market_value": 1050.0,
            "unrealized_pnl": 50.0,
        }
        md = render_forward_report_md(payload)
        assert "## Open Position" in md
        assert "0.500000" in md
        assert "2,100.0000" in md

    def test_none_metrics_show_na(self):
        """Metrics that are None must render as N/A."""
        payload = {
            "session_id": "abc",
            "mode": "forward_paper",
            "eval_start": "2023-01-01",
            "eval_end": "2023-12-31",
            "created_at": "",
            "candidate": {
                "strategy_name": "rsi_ma_cross_v2",
                "source_run_id": "test",
                "selection_metric": "sharpe_simple",
                "selection_value": None,
                "ticker": "ETH-USD",
                "fee_rate": 0.002,
                "slippage_bps": 8.0,
                "params": {},
            },
            "portfolio_state": {"current_equity": None},
            "summary": {
                "total_return": None,
                "max_drawdown": None,
                "n_trades": 0,
                "win_rate": None,
                "expectancy": None,
                "best_trade_pnl": None,
                "worst_trade_pnl": None,
                "total_fees": 0.0,
                "n_bars": None,
                "annualized_volatility": None,
            },
            "charts": [],
            "artifacts": [],
        }
        md = render_forward_report_md(payload)
        assert "N/A" in md, "Expected at least one N/A for None metrics"

    def test_candidate_strategy_shown(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        md = render_forward_report_md(payload)
        assert "rsi_ma_cross_v2" in md

    def test_no_raw_nan_in_md(self, tmp_path):
        out = _make_forward_artifacts(tmp_path, with_trades=False)
        payload = build_forward_report(out)
        md = render_forward_report_md(payload)
        assert "nan" not in md.lower() or "N/A" in md, (
            "Markdown must not contain 'nan' literals"
        )

    def test_artifacts_table_present(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        payload = build_forward_report(out)
        md = render_forward_report_md(payload)
        assert "portfolio_state.json" in md


# ---------------------------------------------------------------------------
# write_forward_report
# ---------------------------------------------------------------------------

class TestWriteForwardReport:

    def test_creates_both_files(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        json_p, md_p = write_forward_report(out)
        assert Path(json_p).exists()
        assert Path(md_p).exists()

    def test_json_strict_parseable(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        json_p, _ = write_forward_report(out)
        content = Path(json_p).read_text(encoding="utf-8")
        data = json.loads(content)  # raises if NaN/Inf present
        assert "session_id" in data

    def test_md_has_headings(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        _, md_p = write_forward_report(out)
        md = Path(md_p).read_text(encoding="utf-8")
        assert "# Forward Evaluation Report" in md

    def test_json_filename(self, tmp_path):
        out = _make_forward_artifacts(tmp_path)
        json_p, md_p = write_forward_report(out)
        assert Path(json_p).name == "forward_report.json"
        assert Path(md_p).name == "forward_report.md"

    def test_no_trades_still_writes_report(self, tmp_path):
        """Zero-trade scenario must produce valid report files."""
        out = _make_forward_artifacts(tmp_path, with_trades=False)
        json_p, md_p = write_forward_report(out)
        data = json.loads(Path(json_p).read_text())
        assert data["summary"]["n_trades"] == 0
