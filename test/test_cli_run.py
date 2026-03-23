from __future__ import annotations

import types
from pathlib import Path

import pandas as pd

from quantlab.cli.run import handle_run_command


class _FakeStrategy:
    name = "fake_strategy"

    def __init__(self, *args, **kwargs):
        pass

    def generate_signals(self, df):
        return pd.Series([0] * len(df), index=df.index)


def _make_args(tmp_path: Path, trades_csv: Path) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        ticker="ETH-USD",
        start="2023-01-01",
        end="2023-01-10",
        interval="1d",
        fee=0.002,
        rsi_buy_max=60.0,
        rsi_sell_min=75.0,
        cooldown_days=0,
        outdir=str(tmp_path / "outputs"),
        save_price_plot=False,
        paper=False,
        initial_cash=1000.0,
        slippage_bps=8.0,
        slippage_mode="fixed",
        k_atr=0.05,
        report=True,
        trades_csv=str(trades_csv),
    )


def test_report_mode_uses_explicit_trades_csv(monkeypatch, tmp_path):
    idx = pd.date_range("2023-01-01", periods=3, freq="D")
    price_df = pd.DataFrame(
        {
            "close": [100.0, 101.0, 102.0],
            "ma20": [99.0, 100.0, 101.0],
            "rsi": [50.0, 51.0, 52.0],
        },
        index=idx,
    )
    trades_csv = tmp_path / "external_trades.csv"
    pd.DataFrame(
        [
            {
                "timestamp": "2023-01-01",
                "ticker": "ETH-USD",
                "side": "BUY",
                "qty": 1.0,
                "price": 100.0,
                "equity_after": 1000.0,
                "fee": 0.1,
                "close": 100.0,
                "exec_price": 100.0,
            }
        ]
    ).to_csv(trades_csv, index=False)

    captured: dict[str, str] = {}

    monkeypatch.setattr("quantlab.cli.run.fetch_ohlc", lambda *args, **kwargs: price_df)
    monkeypatch.setattr("quantlab.cli.run.add_indicators", lambda df: df)
    monkeypatch.setattr("quantlab.cli.run.RsiMaAtrStrategy", _FakeStrategy)
    monkeypatch.setattr("quantlab.cli.run.run_backtest", lambda **kwargs: pd.DataFrame({"equity": [1.0, 1.0, 1.0]}, index=idx))
    monkeypatch.setattr("quantlab.cli.run.compute_metrics", lambda bt: {"total_return": 0.0, "sharpe_simple": 0.0})
    monkeypatch.setattr("quantlab.cli.run.plot_basic_equity", lambda *args, **kwargs: None)
    monkeypatch.setattr("quantlab.cli.run.generate_legacy_report", lambda **kwargs: captured.setdefault("trades_path", kwargs["trades_path"]) or "report.md")

    handle_run_command(_make_args(tmp_path, trades_csv))

    assert captured["trades_path"] == str(trades_csv)
