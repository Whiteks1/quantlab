from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

import main as main_module
from quantlab.cli.run import handle_run_command as _real_handle_run_command
from quantlab.cli.sweep import handle_sweep_command as _real_handle_sweep_command


class _FakeStrategy:
    name = "fake_strategy"

    def __init__(self, *args, **kwargs):
        pass

    def generate_signals(self, df):
        return pd.Series([0] * len(df), index=df.index)


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


def _set_json_request_argv(
    monkeypatch: pytest.MonkeyPatch,
    *,
    command: str,
    params: dict[str, object],
    signal_file: Path,
    request_id: str,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--json-request",
            json.dumps(
                {
                    "schema_version": "1.0",
                    "request_id": request_id,
                    "command": command,
                    "params": params,
                }
            ),
            "--signal-file",
            str(signal_file),
        ],
    )


def _read_signal_events(signal_file: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in signal_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_machine_contract(report_path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    return payload["machine_contract"]


def test_stepbit_external_run_boundary_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    idx = pd.date_range("2023-01-01", periods=3, freq="D")
    price_df = pd.DataFrame(
        {
            "close": [100.0, 101.0, 102.0],
            "ma20": [99.0, 100.0, 101.0],
            "rsi": [50.0, 51.0, 52.0],
        },
        index=idx,
    )
    signal_file = tmp_path / "signals.jsonl"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_module, "handle_run_command", _real_handle_run_command)
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

    _set_json_request_argv(
        monkeypatch,
        command="run",
        params={
            "ticker": "ETH-USD",
            "start": "2023-01-01",
            "end": "2023-01-10",
        },
        signal_file=signal_file,
        request_id="req_stepbit_run_001",
    )

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 0

    events = _read_signal_events(signal_file)
    assert events[0]["event"] == "SESSION_STARTED"
    completed = events[-1]
    assert completed["event"] == "SESSION_COMPLETED"
    assert completed["status"] == "success"
    assert completed["mode"] == "run"
    assert completed["request_id"] == "req_stepbit_run_001"

    contract = _read_machine_contract(completed["report_path"])
    assert contract["contract_type"] == "quantlab.run.result"
    assert completed["run_id"] == contract["run_id"]
    assert completed["artifacts_path"] == str(Path(completed["report_path"]).parent)
    assert completed["summary"] == contract["summary"]
    assert completed["summary"]["sharpe_simple"] == 1.25


def test_stepbit_external_sweep_boundary_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    out_dir = tmp_path / "stepbit_outputs"
    out_dir.mkdir()
    run_dir = out_dir / "20260323_120000_grid_deadbee"
    run_dir.mkdir()
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "machine_contract": {
                    "schema_version": "1.0",
                    "contract_type": "quantlab.sweep.result",
                    "command": "sweep",
                    "status": "success",
                    "request_id": "req_stepbit_sweep_001",
                    "run_id": run_dir.name,
                    "mode": "grid",
                    "summary": {
                        "sharpe_simple": 1.7,
                        "total_return": 0.22,
                    },
                    "best_result": {
                        "sharpe_simple": 1.7,
                        "total_return": 0.22,
                    },
                    "artifacts": {
                        "metadata": "metadata.json",
                        "config": "config.json",
                        "metrics": "metrics.json",
                        "report": "report.json",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "smoke_sweep.yaml"
    config_path.write_text("mode: grid\n", encoding="utf-8")
    signal_file = tmp_path / "signals.jsonl"

    def fake_run_sweep(
        config_path_arg: str,
        out_dir: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, str]:
        assert config_path_arg == str(config_path)
        assert out_dir == str(out_dir_path)
        assert request_id == "req_stepbit_sweep_001"
        return {
            "run_dir": str(run_dir),
            "report_path": str(report_path),
        }

    out_dir_path = out_dir
    monkeypatch.setattr(main_module, "handle_sweep_command", _real_handle_sweep_command)
    monkeypatch.setattr(main_module, "run_sweep", fake_run_sweep)
    _set_json_request_argv(
        monkeypatch,
        command="sweep",
        params={
            "config_path": str(config_path),
            "out_dir": str(out_dir),
        },
        signal_file=signal_file,
        request_id="req_stepbit_sweep_001",
    )

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 0

    events = _read_signal_events(signal_file)
    completed = events[-1]
    assert completed["event"] == "SESSION_COMPLETED"
    assert completed["status"] == "success"

    contract = _read_machine_contract(completed["report_path"])
    assert contract["contract_type"] == "quantlab.sweep.result"
    assert completed["run_id"] == contract["run_id"]
    assert completed["artifacts_path"] == str(run_dir)
    assert completed["summary"] == contract["summary"]
    assert completed["summary"]["total_return"] == 0.22


def test_stepbit_external_sweep_boundary_fails_when_report_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    out_dir = tmp_path / "stepbit_outputs"
    out_dir.mkdir()
    run_dir = out_dir / "20260323_120000_grid_deadbee"
    run_dir.mkdir()
    report_path = run_dir / "report.json"
    config_path = tmp_path / "smoke_sweep.yaml"
    config_path.write_text("mode: grid\n", encoding="utf-8")
    signal_file = tmp_path / "signals.jsonl"

    def fake_run_sweep(
        config_path_arg: str,
        out_dir: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, str]:
        assert config_path_arg == str(config_path)
        assert out_dir == str(out_dir_path)
        assert request_id == "req_stepbit_sweep_fail_001"
        return {
            "run_dir": str(run_dir),
            "report_path": str(report_path),
        }

    out_dir_path = out_dir
    monkeypatch.setattr(main_module, "handle_sweep_command", _real_handle_sweep_command)
    monkeypatch.setattr(main_module, "run_sweep", fake_run_sweep)
    _set_json_request_argv(
        monkeypatch,
        command="sweep",
        params={
            "config_path": str(config_path),
            "out_dir": str(out_dir),
        },
        signal_file=signal_file,
        request_id="req_stepbit_sweep_fail_001",
    )

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 1

    events = _read_signal_events(signal_file)
    assert events[0]["event"] == "SESSION_STARTED"
    failure = events[-1]
    assert failure["event"] == "SESSION_FAILED"
    assert failure["status"] == "error"
    assert failure["mode"] == "sweep"
    assert failure["request_id"] == "req_stepbit_sweep_fail_001"
    assert failure["exit_code"] == 1
    assert failure["error_type"] == "QuantLabError"
    assert "without canonical report.json" in failure["message"]
