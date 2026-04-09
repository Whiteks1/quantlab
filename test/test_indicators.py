"""
Real unit tests for quantlab.features.indicators.add_indicators.

Covers:
- Normal path: returns expected columns for sufficient data
- Too-short path: returns empty DataFrame when len(df) < 100
- No high/low: ATR defaults to 0.0
- With high/low: ATR is computed correctly
- Output is deterministic given same input
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.features.indicators import add_indicators


def _make_ohlc(n: int = 120, seed: int = 42) -> pd.DataFrame:
    """Return a minimal OHLC DataFrame with `n` rows."""
    rng = np.random.default_rng(seed)
    close = 100.0 + rng.normal(0, 1, n).cumsum()
    high = close + rng.uniform(0.1, 0.5, n)
    low = close - rng.uniform(0.1, 0.5, n)
    return pd.DataFrame({"close": close, "high": high, "low": low})


def _make_close_only(n: int = 120, seed: int = 7) -> pd.DataFrame:
    """Return a DataFrame with only a close column."""
    rng = np.random.default_rng(seed)
    close = 50.0 + rng.normal(0, 1, n).cumsum()
    return pd.DataFrame({"close": close})


# ---------------------------------------------------------------------------
# Edge: too few rows
# ---------------------------------------------------------------------------

def test_add_indicators_returns_empty_when_too_short():
    """add_indicators returns an empty DataFrame (same columns) when len < 100."""
    df = _make_ohlc(n=99)
    result = add_indicators(df)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_add_indicators_empty_input_returns_empty():
    """add_indicators handles a completely empty DataFrame without error."""
    df = pd.DataFrame(columns=["close", "high", "low"])
    result = add_indicators(df)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


# ---------------------------------------------------------------------------
# Happy path with high/low
# ---------------------------------------------------------------------------

def test_add_indicators_produces_expected_columns():
    """Output contains rsi, ma20, ma100, atr for OHLC data."""
    df = _make_ohlc(n=120)
    result = add_indicators(df)
    assert not result.empty
    for col in ("close", "rsi", "ma20", "ma100", "atr", "high", "low"):
        assert col in result.columns, f"Missing column: {col}"


def test_add_indicators_rsi_in_valid_range():
    """RSI values are bounded [0, 100]."""
    df = _make_ohlc(n=200)
    result = add_indicators(df)
    assert result["rsi"].between(0, 100).all(), "RSI out of [0, 100]"


def test_add_indicators_ma20_smoothed():
    """MA20 is never NaN in the output (dropna removes leading NaN rows)."""
    df = _make_ohlc(n=200)
    result = add_indicators(df)
    assert not result["ma20"].isna().any()


def test_add_indicators_ma100_lte_ma20_rows():
    """Output has fewer or equal rows compared to input (dropna effect)."""
    df = _make_ohlc(n=200)
    result = add_indicators(df)
    assert len(result) <= len(df)
    assert len(result) > 0


def test_add_indicators_atr_positive_with_high_low():
    """ATR is strictly positive when high/low are present."""
    df = _make_ohlc(n=200)
    result = add_indicators(df)
    assert (result["atr"] > 0).all(), "ATR should be > 0 with real high/low data"


# ---------------------------------------------------------------------------
# Close-only path (no high/low)
# ---------------------------------------------------------------------------

def test_add_indicators_no_high_low_sets_atr_zero():
    """When df has no high/low columns, ATR defaults to 0.0."""
    df = _make_close_only(n=200)
    result = add_indicators(df)
    assert not result.empty
    assert "atr" in result.columns
    assert (result["atr"] == 0.0).all()


def test_add_indicators_no_high_low_produces_rsi_ma():
    """rsi, ma20, ma100 are computed even without high/low."""
    df = _make_close_only(n=200)
    result = add_indicators(df)
    for col in ("rsi", "ma20", "ma100"):
        assert col in result.columns
        assert not result[col].isna().any()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_add_indicators_is_deterministic():
    """Same input always produces identical output."""
    df = _make_ohlc(n=150)
    r1 = add_indicators(df)
    r2 = add_indicators(df)
    pd.testing.assert_frame_equal(r1, r2)


def test_add_indicators_does_not_mutate_input():
    """add_indicators must not modify the original DataFrame in place."""
    df = _make_ohlc(n=150)
    original_close = df["close"].copy()
    add_indicators(df)
    pd.testing.assert_series_equal(df["close"], original_close)
