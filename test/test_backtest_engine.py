from __future__ import annotations

import pandas as pd
import pytest

from quantlab.backtest.engine import run_backtest


def _make_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": [100.0, 101.0, 102.0],
            "atr": [1.0, 1.0, 1.0],
        },
        index=pd.date_range("2026-01-01", periods=3, freq="D"),
    )


def test_initial_entry_is_counted_as_trade_and_costed():
    df = _make_df()
    signals = pd.Series([1, 0, 0], index=df.index)

    bt = run_backtest(df=df, signals=signals, fee_rate=0.01, slippage_bps=10.0)

    assert bt["trade"].tolist() == [1, 0, 0]
    assert bt["fees"].iloc[0] == pytest.approx(0.01)
    assert bt["slip_cost"].iloc[0] > 0.0
