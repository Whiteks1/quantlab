from __future__ import annotations

from quantlab.backtest.profiling import (
    build_backtest_profile_report,
    generate_synthetic_backtest_inputs,
    profile_backtest_workload,
)


def test_generate_synthetic_backtest_inputs_shapes_match():
    df, signals = generate_synthetic_backtest_inputs(rows=32, seed=7)

    assert len(df) == 32
    assert len(signals) == 32
    assert list(df.columns) == ["close", "atr"]
    assert signals.index.equals(df.index)


def test_profile_backtest_workload_returns_positive_timings():
    result = profile_backtest_workload(rows=128, repeats=2, warmup=0, seed=7)

    assert result.rows == 128
    assert result.repeats == 2
    assert len(result.elapsed_seconds) == 2
    assert all(value >= 0.0 for value in result.elapsed_seconds)
    assert result.mean_seconds >= 0.0
    assert result.rows_per_second_mean > 0.0


def test_build_backtest_profile_report_includes_requested_sizes():
    report = build_backtest_profile_report(sizes=(64, 128), repeats=1, warmup=0, seed=7)

    assert report["artifact_type"] == "quantlab.backtest.profile"
    assert report["sizes"] == [64, 128]
    assert len(report["workloads"]) == 2
    assert report["workloads"][0]["rows"] == 64
    assert report["workloads"][1]["rows"] == 128
