from __future__ import annotations

import pandas as pd
import pytest

from quantlab.backtest.engine import available_backtest_backends, run_backtest


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


def test_reports_python_backend_as_available():
    assert "python" in available_backtest_backends()


def test_numba_backend_matches_python_for_fixed_slippage():
    pytest.importorskip("numba")
    df = pd.DataFrame(
        {
            "close": [100.0, 101.0, 99.5, 102.0, 104.0],
            "atr": [1.0, 1.2, 1.1, 1.0, 0.9],
        },
        index=pd.date_range("2026-01-01", periods=5, freq="D"),
    )
    signals = pd.Series([1, 0, -1, 1, 0], index=df.index)

    python_bt = run_backtest(df=df, signals=signals, slippage_mode="fixed", backend="python")
    numba_bt = run_backtest(df=df, signals=signals, slippage_mode="fixed", backend="numba")

    pd.testing.assert_series_equal(python_bt["position"], numba_bt["position"], check_dtype=False)
    pd.testing.assert_series_equal(python_bt["trade"], numba_bt["trade"], check_dtype=False)
    pd.testing.assert_series_equal(python_bt["fees"], numba_bt["fees"], check_dtype=False)
    pd.testing.assert_series_equal(python_bt["slip_cost"], numba_bt["slip_cost"], check_dtype=False)
    pd.testing.assert_series_equal(
        python_bt["strategy_ret_net"],
        numba_bt["strategy_ret_net"],
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )


def test_numba_backend_matches_python_for_atr_slippage():
    pytest.importorskip("numba")
    df = pd.DataFrame(
        {
            "close": [100.0, 101.0, 99.5, 102.0, 104.0],
            "atr": [1.0, 1.2, 1.1, 1.0, 0.9],
        },
        index=pd.date_range("2026-01-01", periods=5, freq="D"),
    )
    signals = pd.Series([1, 0, -1, 1, 0], index=df.index)

    python_bt = run_backtest(df=df, signals=signals, slippage_mode="atr", backend="python", k_atr=0.05)
    numba_bt = run_backtest(df=df, signals=signals, slippage_mode="atr", backend="numba", k_atr=0.05)

    pd.testing.assert_series_equal(python_bt["fees"], numba_bt["fees"], check_dtype=False)
    pd.testing.assert_series_equal(
        python_bt["slip_cost"],
        numba_bt["slip_cost"],
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )
    pd.testing.assert_series_equal(
        python_bt["strategy_ret_net"],
        numba_bt["strategy_ret_net"],
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )
