"""Tests for Stage K.2: stitched OOS timeseries artifact and its Stage K consumption."""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from quantlab.experiments.runner import (
    _persist_walkforward_rich_artifacts,
    run_one_with_timeseries,
)
from quantlab.reporting.advanced_metrics import (
    _load_equity_from_artifacts,
    build_advanced_metrics,
)
from quantlab.reporting.advanced_report import write_advanced_report
from quantlab.reporting.charts import generate_charts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bt_frame(n: int = 100, split_name: str = "split_00",
                   start: str = "2023-01-01", seed: int = 42) -> pd.DataFrame:
    """Create a synthetic bt-like DataFrame as run_one_with_timeseries would produce."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=n, freq="B")
    ret = rng.normal(0.0005, 0.012, n)
    equity = np.cumprod(1 + ret)
    return pd.DataFrame({
        "timestamp": dates,
        "split_name": split_name,
        "equity": equity,
        "period_return": ret,
        "cumulative_return": equity - 1.0,
        "close": 100 + np.cumsum(rng.normal(0, 1, n)),
        "signal": rng.choice([0, 1, -1], size=n),
        "position": rng.choice([0, 1], size=n),
    })


def _make_run_dir_with_timeseries(
    tmp_path: Path, n_splits: int = 3, bars_per_split: int = 100,
) -> Path:
    """Create a run dir containing oos_equity_timeseries.csv across n_splits."""
    run_dir = tmp_path / "wf_rich_run"
    run_dir.mkdir()

    # Write run_report.json
    report = {
        "header": {"run_id": "wf_rich_run", "mode": "walkforward",
                   "created_at": "2023-01-01", "git_commit": "abc"},
        "results": [],
        "config_resolved": {},
    }
    with open(run_dir / "run_report.json", "w") as f:
        json.dump(report, f)

    # Stitch OOS timeseries over n_splits
    frames = []
    start_date = pd.Timestamp("2023-01-01")
    for i in range(n_splits):
        start = (start_date + pd.offsets.BDay(i * bars_per_split)).strftime("%Y-%m-%d")
        frames.append(_make_bt_frame(bars_per_split, split_name=f"split_{i:02d}", start=start, seed=i))

    oos_ts = pd.concat(frames, ignore_index=True)
    oos_ts.to_csv(run_dir / "oos_equity_timeseries.csv", index=False)

    return run_dir


# ---------------------------------------------------------------------------
# Tests: artifact persistence
# ---------------------------------------------------------------------------

def test_persist_walkforward_writes_oos_timeseries(tmp_path):
    """_persist_walkforward_rich_artifacts must write oos_equity_timeseries.csv when frames given."""
    frames = [_make_bt_frame(60, "split_00"), _make_bt_frame(60, "split_01", start="2023-04-01")]
    final_df = pd.DataFrame([
        {"split_name": "split_00", "phase": "test", "selected": True, "total_return": 0.1},
        {"split_name": "split_01", "phase": "test", "selected": True, "total_return": 0.05},
    ])
    _persist_walkforward_rich_artifacts(tmp_path, final_df, [], oos_timeseries_frames=frames)

    ts_path = tmp_path / "oos_equity_timeseries.csv"
    assert ts_path.exists(), "oos_equity_timeseries.csv must be created"
    df = pd.read_csv(ts_path)
    assert len(df) == 120   # 60 + 60
    assert "equity" in df.columns
    assert "timestamp" in df.columns


def test_oos_timeseries_chronological(tmp_path):
    """Concatenated splits must be in chronological order."""
    f1 = _make_bt_frame(50, "split_00", start="2023-01-01")
    f2 = _make_bt_frame(50, "split_01", start="2023-04-01")
    _persist_walkforward_rich_artifacts(tmp_path, pd.DataFrame(), [], oos_timeseries_frames=[f1, f2])

    df = pd.read_csv(tmp_path / "oos_equity_timeseries.csv")
    ts = pd.to_datetime(df["timestamp"])
    assert ts.is_monotonic_increasing, "Timestamps must be chronological"


def test_oos_timeseries_none_frames_skipped(tmp_path):
    """None entries in oos_timeseries_frames must be ignored gracefully."""
    frames = [None, _make_bt_frame(30, "split_01"), None]
    _persist_walkforward_rich_artifacts(
        tmp_path, pd.DataFrame(), [], oos_timeseries_frames=frames
    )
    df = pd.read_csv(tmp_path / "oos_equity_timeseries.csv")
    assert len(df) == 30


def test_persist_no_timeseries_frames_no_file(tmp_path):
    """Without OOS frames, oos_equity_timeseries.csv must not be created."""
    _persist_walkforward_rich_artifacts(
        tmp_path, pd.DataFrame(), [], oos_timeseries_frames=[]
    )
    assert not (tmp_path / "oos_equity_timeseries.csv").exists()


# ---------------------------------------------------------------------------
# Tests: Stage K loader priority
# ---------------------------------------------------------------------------

def test_loader_prefers_oos_timeseries_over_curve(tmp_path):
    """oos_equity_timeseries.csv must be preferred over oos_equity_curve.csv."""
    run_dir = tmp_path / "run_pref"
    run_dir.mkdir()

    # Write both artifacts
    ts_frame = _make_bt_frame(200, "split_00")
    ts_frame.to_csv(run_dir / "oos_equity_timeseries.csv", index=False)

    # oos_equity_curve.csv with only 3 rows (K.1 level)
    pd.DataFrame({"split_name": ["s0", "s1", "s2"],
                  "avg_test_return": [0.1, -0.05, 0.08],
                  "cumulative_equity": [1.1, 1.045, 1.129]}).to_csv(
        run_dir / "oos_equity_curve.csv", index=False
    )

    eq = _load_equity_from_artifacts(run_dir)
    assert eq is not None
    # Should have ~200 rows from timeseries, not 4 from curve+prepend
    assert len(eq) == 200


def test_loader_fallback_to_oos_curve_when_no_timeseries(tmp_path):
    """Falls back to oos_equity_curve.csv when timeseries is absent."""
    run_dir = tmp_path / "run_fallback"
    run_dir.mkdir()

    pd.DataFrame({"split_name": ["s0", "s1", "s2"],
                  "avg_test_return": [0.1, -0.05, 0.08],
                  "cumulative_equity": [1.1, 1.045, 1.129]}).to_csv(
        run_dir / "oos_equity_curve.csv", index=False
    )

    eq = _load_equity_from_artifacts(run_dir)
    assert eq is not None
    assert len(eq) == 4   # 3 splits + prepended 1.0


# ---------------------------------------------------------------------------
# Tests: Stage K consumers
# ---------------------------------------------------------------------------

def test_advanced_metrics_uses_timeseries(tmp_path):
    """build_advanced_metrics must populate equity_metrics from timeseries."""
    run_dir = _make_run_dir_with_timeseries(tmp_path, n_splits=4, bars_per_split=100)
    payload = build_advanced_metrics(run_dir)

    em = payload.get("equity_metrics", {})
    assert em.get("n_days") == 400, f"Expected 400 bars, got {em.get('n_days')}"
    assert em.get("total_return") is not None

    json.dumps(payload, allow_nan=False)   # must be strict JSON


def test_advanced_report_generates_charts_from_timeseries(tmp_path):
    """write_advanced_report must produce chart files when timeseries has enough rows."""
    run_dir = _make_run_dir_with_timeseries(tmp_path, n_splits=4, bars_per_split=100)
    json_p, md_p = write_advanced_report(run_dir)

    # At minimum equity and drawdown charts must be created
    chart_files = list(run_dir.glob("chart_*.png"))
    assert len(chart_files) >= 2, f"Expected ≥2 charts, got {chart_files}"

    with open(json_p) as f:
        data = json.load(f)
    assert len(data.get("charts", [])) >= 2


def test_backward_compat_old_run_no_crash(tmp_path):
    """Runs without oos_equity_timeseries.csv must still produce valid output."""
    run_dir = tmp_path / "old_run"
    run_dir.mkdir()
    with open(run_dir / "meta.json", "w") as f:
        json.dump({"run_id": "old_run", "mode": "walkforward"}, f)

    json_p, md_p = write_advanced_report(run_dir)
    assert Path(json_p).exists()
    with open(json_p) as f:
        data = json.load(f)
    # No charts but must be valid JSON
    assert data["trade_distribution"]["n_trades"] == 0
