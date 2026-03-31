from __future__ import annotations

import json
import types
from pathlib import Path

import pandas as pd
import pytest

from quantlab.cli.run import handle_run_command
from quantlab.errors import DataError


class _FakeStrategy:
    name = "fake_strategy"

    def __init__(self, *args, **kwargs):
        pass

    def generate_signals(self, df):
        return pd.Series([1, 0, -1], index=df.index)


def _make_args() -> types.SimpleNamespace:
    return types.SimpleNamespace(
        ticker="ETH-USD",
        start="2023-01-01",
        end="2023-01-10",
        interval="1d",
        fee=0.002,
        rsi_buy_max=60.0,
        rsi_sell_min=75.0,
        cooldown_days=0,
        outdir=None,
        save_price_plot=False,
        paper=True,
        initial_cash=1000.0,
        slippage_bps=8.0,
        slippage_mode="fixed",
        k_atr=0.05,
        report=True,
        trades_csv=None,
        _request_id="req_paper_session_001",
    )


def _fake_backtest_frame(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "equity": [1.0, 1.02, 1.01],
            "position": [0, 1, 0],
            "trade": [0, 1, -1],
            "strategy_ret_net": [0.0, 0.02, -0.01],
        },
        index=index,
    )


def test_paper_run_creates_dedicated_session_artifacts(monkeypatch, tmp_path):
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
            "total_return": 0.01,
            "max_drawdown": -0.01,
            "sharpe_simple": 0.8,
            "winrate_active_days": 0.5,
            "days": 3,
            "trades": 2,
        },
    )
    monkeypatch.setattr("quantlab.cli.run.plot_basic_equity", lambda *args, **kwargs: None)

    result = handle_run_command(_make_args())

    session_id = result["session_id"]
    session_dir = tmp_path / "outputs" / "paper_sessions" / session_id
    assert result["artifacts_path"] == str(session_dir)
    assert result["mode"] == "paper"
    assert (session_dir / "session_metadata.json").exists()
    assert (session_dir / "session_status.json").exists()
    assert (session_dir / "config.json").exists()
    assert (session_dir / "metrics.json").exists()
    assert (session_dir / "trades.csv").exists()
    assert (session_dir / "report.json").exists()
    assert (session_dir / "run_report.md").exists()

    metadata = json.loads((session_dir / "session_metadata.json").read_text(encoding="utf-8"))
    assert metadata["session_id"] == session_id
    assert metadata["mode"] == "paper"
    assert metadata["command"] == "paper"
    assert metadata["request_id"] == "req_paper_session_001"

    status = json.loads((session_dir / "session_status.json").read_text(encoding="utf-8"))
    assert status["session_id"] == session_id
    assert status["status"] == "success"
    assert status["terminal"] is True
    assert status["status_reason"] == "completed"
    assert status["started_at"]
    assert status["finished_at"]
    assert status["duration_seconds"] >= 0.0

    index_payload = json.loads(
        (tmp_path / "outputs" / "paper_sessions" / "paper_sessions_index.json").read_text(
            encoding="utf-8"
        )
    )
    indexed = {row["session_id"]: row for row in index_payload["sessions"]}
    assert indexed[session_id]["terminal"] is True
    assert indexed[session_id]["status_reason"] == "completed"

    report = json.loads((session_dir / "report.json").read_text(encoding="utf-8"))
    assert report["header"]["mode"] == "paper"
    assert report["machine_contract"]["contract_type"] == "quantlab.paper.result"
    assert report["machine_contract"]["mode"] == "paper"
    assert report["machine_contract"]["artifacts"]["metadata"] == "session_metadata.json"
    assert report["machine_contract"]["artifacts"]["status"] == "session_status.json"


def test_paper_run_persists_failed_session_status(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "quantlab.cli.run.fetch_ohlc",
        lambda *args, **kwargs: pd.DataFrame(columns=["close"]),
    )
    monkeypatch.setattr("quantlab.cli.run.add_indicators", lambda df: df)

    with pytest.raises(DataError):
        handle_run_command(_make_args())

    sessions_root = tmp_path / "outputs" / "paper_sessions"
    session_dirs = [path for path in sessions_root.iterdir() if path.is_dir()]
    assert len(session_dirs) == 1

    status = json.loads((session_dirs[0] / "session_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "failed"
    assert status["error_type"] == "DataError"
    assert status["terminal"] is True
    assert status["status_reason"] == "exception"
    assert status["started_at"]
    assert status["finished_at"]
    assert status["duration_seconds"] >= 0.0

    index_payload = json.loads((sessions_root / "paper_sessions_index.json").read_text(encoding="utf-8"))
    indexed = {row["session_id"]: row for row in index_payload["sessions"]}
    failed_session_id = session_dirs[0].name
    assert indexed[failed_session_id]["status"] == "failed"
    assert indexed[failed_session_id]["status_reason"] == "exception"
