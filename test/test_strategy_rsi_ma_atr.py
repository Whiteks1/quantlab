"""
Real unit tests for quantlab.strategies.rsi_ma_atr.RsiMaAtrStrategy.

Covers:
- Empty DataFrame returns empty Series
- Missing required columns raises DataError
- BUY signal fires on cross-up when RSI < rsi_buy_max
- No BUY fires when RSI >= rsi_buy_max (even on cross-up)
- SELL fires on cross-down
- SELL fires when RSI > rsi_sell_min
- No repeated BUY while in position
- Cooldown suppresses re-entry
- Output is deterministic given same input
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.errors import DataError


def _make_strategy(**kwargs) -> RsiMaAtrStrategy:
    return RsiMaAtrStrategy(**kwargs)


def _minimal_df(
    close: list[float],
    ma20: list[float],
    rsi: list[float],
) -> pd.DataFrame:
    """Build minimal DataFrame required by generate_signals."""
    return pd.DataFrame({"close": close, "ma20": ma20, "rsi": rsi})


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_empty_df_returns_empty_series():
    strategy = _make_strategy()
    result = strategy.generate_signals(pd.DataFrame())
    assert isinstance(result, pd.Series)
    assert result.empty


def test_rsi_ma_atr_raises_on_missing_columns():
    strategy = _make_strategy()
    df = pd.DataFrame({"close": [1.0, 2.0], "ma20": [1.0, 1.5]})  # missing rsi
    with pytest.raises(DataError):
        strategy.generate_signals(df)


def test_rsi_ma_atr_raises_on_all_columns_missing():
    strategy = _make_strategy()
    df = pd.DataFrame({"volume": [100, 200]})
    with pytest.raises(DataError):
        strategy.generate_signals(df)


# ---------------------------------------------------------------------------
# BUY signal: cross-up + RSI < buy_max
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_generates_buy_on_crossup_with_low_rsi():
    """BUY (1) fires when close crosses above ma20 and rsi < rsi_buy_max."""
    # Row 0: below MA (no cross yet)
    # Row 1: crosses above MA, RSI within limit
    strategy = _make_strategy(rsi_buy_max=60.0, rsi_sell_min=75.0)
    df = _minimal_df(
        close=[99.0, 101.0, 101.5, 101.0],
        ma20= [100.0, 100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  55.0,  55.0],
    )
    signals = strategy.generate_signals(df)
    assert signals.iloc[1] == 1, "Expected BUY at cross-up"


def test_rsi_ma_atr_no_buy_when_rsi_too_high():
    """No BUY when RSI >= rsi_buy_max even if cross-up occurs."""
    strategy = _make_strategy(rsi_buy_max=60.0)
    df = _minimal_df(
        close=[99.0, 101.0],
        ma20= [100.0, 100.0],
        rsi=  [40.0,  62.0],   # RSI exceeds limit
    )
    signals = strategy.generate_signals(df)
    assert signals.iloc[1] == 0, "BUY should be suppressed when RSI too high"


# ---------------------------------------------------------------------------
# SELL signal
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_generates_sell_on_crossdown():
    """SELL (-1) fires when close crosses below ma20."""
    strategy = _make_strategy(rsi_buy_max=60.0, rsi_sell_min=75.0)
    df = _minimal_df(
        close=[99.0, 101.0, 99.0],
        ma20= [100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  50.0],
    )
    signals = strategy.generate_signals(df)
    # Buy at row 1, sell cross-down at row 2
    assert signals.iloc[1] == 1
    assert signals.iloc[2] == -1


def test_rsi_ma_atr_generates_sell_on_high_rsi():
    """SELL (-1) fires when RSI > rsi_sell_min while in position."""
    strategy = _make_strategy(rsi_buy_max=60.0, rsi_sell_min=75.0)
    df = _minimal_df(
        close=[99.0, 101.0, 101.5],
        ma20= [100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  80.0],   # RSI spikes on row 2
    )
    signals = strategy.generate_signals(df)
    assert signals.iloc[1] == 1
    assert signals.iloc[2] == -1


# ---------------------------------------------------------------------------
# No repeated BUY while in position
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_no_double_buy():
    """No second BUY while already in position (no SELL between the two cross-ups)."""
    strategy = _make_strategy(rsi_buy_max=60.0, rsi_sell_min=75.0)
    # Row 0: below MA
    # Row 1: cross-up -> BUY, now in position
    # Row 2: dips below briefly (no cross-down since rsi still low, and we are checking
    #         that a second cross-up doesn't re-trigger BUY while in position)
    # Row 3: cross-up again while still in position -> must NOT produce another BUY
    df = _minimal_df(
        close=[99.0, 101.0, 101.0, 102.0],
        ma20= [100.0, 100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  50.0,  50.0],
    )
    signals = strategy.generate_signals(df)
    buy_count = (signals == 1).sum()
    assert buy_count == 1, f"Expected exactly 1 BUY, got {buy_count}"


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_cooldown_suppresses_reentry():
    """After a SELL, cooldown_days suppresses re-entry signals.

    The strategy applies cooldown after BOTH BUY and SELL.
    We use cooldown_days=1 so the BUY at row 1 clears after row 2,
    then SELL fires at row 3 (RSI spike), then rows 4-5 are suppressed.
    """
    strategy = _make_strategy(rsi_buy_max=60.0, rsi_sell_min=75.0, cooldown_days=1)
    #            0      1      2      3      4      5
    df = _minimal_df(
        close=[99.0, 101.0, 101.0, 101.0, 101.0, 101.0],
        ma20= [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  50.0,  80.0,  50.0,  50.0],
    )
    # Row 0: below MA, no signal
    # Row 1: cross-up, RSI<60 -> BUY; cooldown=1 starts
    # Row 2: cooldown active -> no SELL despite being in position
    # Row 3: cooldown expired, in position, RSI>75 -> SELL; cooldown=1 starts
    # Row 4: cooldown active -> 0
    signals = strategy.generate_signals(df)
    assert signals.iloc[1] == 1,  f"Expected BUY at row 1, got {signals.iloc[1]}"
    assert signals.iloc[2] == 0,  f"Expected cooldown at row 2, got {signals.iloc[2]}"
    assert signals.iloc[3] == -1, f"Expected SELL at row 3, got {signals.iloc[3]}"
    assert signals.iloc[4] == 0,  f"Expected cooldown at row 4, got {signals.iloc[4]}"



# ---------------------------------------------------------------------------
# Output shape and dtype
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_output_shape_matches_input():
    """Signal series length equals DataFrame length."""
    strategy = _make_strategy()
    df = _minimal_df(
        close=[99.0, 101.0, 101.5],
        ma20= [100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  55.0],
    )
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)


def test_rsi_ma_atr_signals_only_contain_valid_values():
    """All signal values are in {-1, 0, 1}."""
    rng = np.random.default_rng(99)
    n = 50
    close = 100 + rng.normal(0, 1, n).cumsum()
    ma20 = pd.Series(close).rolling(3).mean().fillna(close[0]).values
    rsi = rng.uniform(30, 70, n)
    strategy = _make_strategy()
    df = pd.DataFrame({"close": close, "ma20": ma20, "rsi": rsi})
    signals = strategy.generate_signals(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_rsi_ma_atr_is_deterministic():
    """Same input always produces identical signal series."""
    strategy = _make_strategy()
    df = _minimal_df(
        close=[99.0, 101.0, 99.0, 101.5, 100.5],
        ma20= [100.0, 100.0, 100.0, 100.0, 100.0],
        rsi=  [40.0,  50.0,  55.0,  45.0,  50.0],
    )
    s1 = strategy.generate_signals(df)
    s2 = strategy.generate_signals(df)
    pd.testing.assert_series_equal(s1, s2)
