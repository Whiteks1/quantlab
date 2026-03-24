from __future__ import annotations

import json
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


def _make_args(tmp_path: Path, trades_csv: Path | None = None) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        ticker="ETH-USD",
        start="2023-01-01",
        end="2023-01-10",
        interval="1d",
        fee=0.002,
        rsi_buy_max=60.0,
        rsi_sell_min=75.0,
        cooldown_days=0,
        outdir=str(tmp_path / "legacy_outputs"),
        save_price_plot=False,
        paper=False,
        initial_cash=1000.0,
        slippage_bps=8.0,
        slippage_mode="fixed",
        k_atr=0.05,
        report=True,
        trades_csv=str(trades_csv) if trades_csv else None,
        _request_id="req_run_contract_001",
    )


def _fake_backtest_frame(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "equity": [1.0, 1.02, 1.03],
            "position": [0, 1, 1],
            "trade": [0, 1, 0],
            "strategy_ret_net": [0.0, 0.02, 0.01],
        },
        index=index,
    )


def test_run_creates_canonical_run_directory_and_artifacts(monkeypatch, tmp_path):
    idx = pd.date_range("2023-01-01", periods=3, freq="D")
    price_df = pd.DataFrame(
        {
            "close": [100.0, 101.0, 102.0],
            "ma20": [99.0, 100.0, 101.0],
            "rsi": [50.0, 51.0, 52.0],
        },
        index=idx,
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("quantlab.cli.run.fetch_ohlc", lambda *args, **kwargs: price_df)
    monkeypatch.setattr("quantlab.cli.run.add_indicators", lambda df: df)
    monkeypatch.setattr("quantlab.cli.run.RsiMaAtrStrategy", _FakeStrategy)
    monkeypatch.setattr(
        "quantlab.cli.run.run_backtest",
        lambda **kwargs: _fake_backtest_frame(idx),
    )
    monkeypatch.setattr(
        "quantlab.cli.run.compute_metrics",
        lambda bt: {
            "total_return": 0.03,
            "max_drawdown": -0.01,
            "sharpe_simple": 1.25,
            "winrate_active_days": 1.0,
            "days": 3,
            "trades": 1,
        },
    )
    monkeypatch.setattr("quantlab.cli.run.plot_basic_equity", lambda *args, **kwargs: None)

    result = handle_run_command(_make_args(tmp_path))

    run_id = result["run_id"]
    assert run_id is not None
    run_dir = tmp_path / "outputs" / "runs" / run_id
    assert result["artifacts_path"] == str(run_dir)
    assert result["report_path"] == str(run_dir / "report.json")
    assert result["runs_index_root"] == str(tmp_path / "outputs" / "runs")

    assert (run_dir / "metadata.json").exists()
    assert (run_dir / "config.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "run_report.md").exists()

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == run_id
    assert metadata["mode"] == "run"
    assert metadata["command"] == "run"
    assert metadata["request_id"] == "req_run_contract_001"

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["status"] == "success"
    assert metrics["summary"]["trades"] == 1

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["header"]["run_id"] == run_id
    assert report["header"]["mode"] == "run"
    assert report["results"][0]["sharpe_simple"] == 1.25
    assert "machine_contract" not in report


def test_run_copies_explicit_trades_csv_into_canonical_run_dir(monkeypatch, tmp_path):
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

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("quantlab.cli.run.fetch_ohlc", lambda *args, **kwargs: price_df)
    monkeypatch.setattr("quantlab.cli.run.add_indicators", lambda df: df)
    monkeypatch.setattr("quantlab.cli.run.RsiMaAtrStrategy", _FakeStrategy)
    monkeypatch.setattr(
        "quantlab.cli.run.run_backtest",
        lambda **kwargs: _fake_backtest_frame(idx),
    )
    monkeypatch.setattr(
        "quantlab.cli.run.compute_metrics",
        lambda bt: {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_simple": 0.0,
            "winrate_active_days": 0.0,
            "days": 3,
            "trades": 0,
        },
    )
    monkeypatch.setattr("quantlab.cli.run.plot_basic_equity", lambda *args, **kwargs: None)

    result = handle_run_command(_make_args(tmp_path, trades_csv))

    run_dir = Path(result["artifacts_path"])
    copied_trades = run_dir / "trades.csv"
    assert copied_trades.exists()

    copied = pd.read_csv(copied_trades)
    assert list(copied["timestamp"]) == ["2023-01-01"]
