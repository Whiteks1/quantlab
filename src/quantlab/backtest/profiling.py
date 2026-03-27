from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantlab.backtest.engine import available_backtest_backends, run_backtest


@dataclass(frozen=True)
class BacktestProfileResult:
    rows: int
    repeats: int
    warmup: int
    slippage_mode: str
    backend: str
    elapsed_seconds: tuple[float, ...]
    mean_seconds: float
    median_seconds: float
    min_seconds: float
    max_seconds: float
    rows_per_second_mean: float
    rows_per_second_peak: float
    final_equity: float
    trade_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "rows": self.rows,
            "repeats": self.repeats,
            "warmup": self.warmup,
            "slippage_mode": self.slippage_mode,
            "backend": self.backend,
            "elapsed_seconds": list(self.elapsed_seconds),
            "mean_seconds": self.mean_seconds,
            "median_seconds": self.median_seconds,
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "rows_per_second_mean": self.rows_per_second_mean,
            "rows_per_second_peak": self.rows_per_second_peak,
            "final_equity": self.final_equity,
            "trade_count": self.trade_count,
        }


def generate_synthetic_backtest_inputs(
    *,
    rows: int,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    if rows <= 0:
        raise ValueError("rows must be positive")

    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0004, scale=0.02, size=rows)
    close = 100.0 * np.cumprod(1.0 + returns)
    atr = np.maximum(close * 0.01, 0.25)

    signal_values = rng.choice([-1, 0, 1], size=rows, p=[0.05, 0.9, 0.05])
    signal_values[0] = 0

    index = pd.date_range("2024-01-01", periods=rows, freq="h")
    df = pd.DataFrame({"close": close, "atr": atr}, index=index)
    signals = pd.Series(signal_values, index=index, dtype=int)
    return df, signals


def profile_backtest_workload(
    *,
    rows: int,
    repeats: int = 3,
    warmup: int = 1,
    slippage_mode: str = "fixed",
    backend: str = "python",
    seed: int = 42,
) -> BacktestProfileResult:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")

    df, signals = generate_synthetic_backtest_inputs(rows=rows, seed=seed)

    last_result: pd.DataFrame | None = None
    for _ in range(warmup):
        last_result = run_backtest(
            df=df,
            signals=signals,
            slippage_mode=slippage_mode,
            backend=backend,
        )

    timings: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        last_result = run_backtest(
            df=df,
            signals=signals,
            slippage_mode=slippage_mode,
            backend=backend,
        )
        timings.append(time.perf_counter() - started)

    assert last_result is not None
    mean_seconds = statistics.mean(timings)
    median_seconds = statistics.median(timings)
    min_seconds = min(timings)
    max_seconds = max(timings)
    rows_per_second_mean = rows / mean_seconds if mean_seconds > 0 else float("inf")
    rows_per_second_peak = rows / min_seconds if min_seconds > 0 else float("inf")

    return BacktestProfileResult(
        rows=rows,
        repeats=repeats,
        warmup=warmup,
        slippage_mode=slippage_mode,
        backend=backend,
        elapsed_seconds=tuple(timings),
        mean_seconds=mean_seconds,
        median_seconds=median_seconds,
        min_seconds=min_seconds,
        max_seconds=max_seconds,
        rows_per_second_mean=rows_per_second_mean,
        rows_per_second_peak=rows_per_second_peak,
        final_equity=float(last_result["equity"].iloc[-1]),
        trade_count=int((last_result["trade"] != 0).sum()),
    )


def build_backtest_profile_report(
    *,
    sizes: tuple[int, ...] = (1_000, 10_000, 100_000),
    repeats: int = 3,
    warmup: int = 1,
    slippage_mode: str = "fixed",
    backend: str = "python",
    seed: int = 42,
) -> dict[str, object]:
    workloads = [
        profile_backtest_workload(
            rows=size,
            repeats=repeats,
            warmup=warmup,
            slippage_mode=slippage_mode,
            backend=backend,
            seed=seed,
        ).to_dict()
        for size in sizes
    ]
    return {
        "artifact_type": "quantlab.backtest.profile",
        "available_backends": list(available_backtest_backends()),
        "sizes": list(sizes),
        "repeats": repeats,
        "warmup": warmup,
        "slippage_mode": slippage_mode,
        "backend": backend,
        "seed": seed,
        "workloads": workloads,
    }
