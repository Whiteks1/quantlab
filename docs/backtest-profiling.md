# Backtest Profiling

QuantLab now includes a small local profiling surface for the current Python backtest engine.

This is not a benchmark suite for the whole repository.

It exists to answer a narrower question:

- is the backtest inner loop actually the first hotspot worth accelerating?

## Command

From the repository root:

```bash
python scripts/profile_backtest.py
```

Example with custom sizes and JSON output:

```bash
python scripts/profile_backtest.py --sizes 1000,10000,50000 --repeats 5 --warmup 1 --json-out outputs/profiling/backtest_profile.json
```

Example targeting the optional Numba pilot:

```bash
python scripts/profile_backtest.py --backend numba --sizes 1000,10000,50000 --repeats 5 --warmup 1
```

## What It Measures

The script:

- generates synthetic OHLC and signal inputs
- runs the current Python backtest engine repeatedly
- can target either the default `python` backend or the optional `numba` backend
- reports timing for small, medium, and large workloads
- summarizes throughput in rows per second

The goal is not to simulate real strategy quality.

The goal is to compare backtest kernel cost across representative sizes before introducing `Numba`, `C++`, or `Rust`.

## How To Read It

The most important fields are:

- `mean_seconds`
- `min_seconds`
- `rows_per_second_avg`
- `rows_per_second_max`
- `backend`

Use the results to answer:

- does the current engine become meaningfully expensive at larger sizes?
- is the performance shape stable enough to justify extracting an inner numeric kernel?
- does the optional `Numba` pilot materially outperform the Python path on the same workload?
- is a compiled extension still justified after trying `Numba`?

Interpretation note:

- for small workloads, `Numba` can still lose because warmup and dispatch overhead are not free
- for larger workloads, the extracted inner loop is the place where `Numba` is most likely to show useful gains

## Current Recommendation

This profiling surface supports the current native-acceleration strategy:

- keep QuantLab Python-first
- target the backtest engine first if profiling confirms it as the main hotspot
- try `Numba` before introducing a compiled extension

To enable the optional `Numba` backend:

```bash
pip install -e .[perf]
```
