from __future__ import annotations

import json
import types
from pathlib import Path

import pandas as pd

from quantlab.cli.sweep import handle_sweep_command
from quantlab.reporting.run_report import write_report


def test_write_report_exposes_stable_sweep_machine_contract(tmp_path):
    run_dir = tmp_path / "20260323_120000_grid_deadbee"
    run_dir.mkdir()

    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "mode": "grid",
                "created_at": "2026-03-23T12:00:00",
                "git_commit": "deadbee",
                "config_path": "configs/sweep.yaml",
                "config_hash": "hash123",
                "request_id": "req_123",
                "status": "success",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "config.json").write_text(
        json.dumps({"ticker": "ETH-USD", "start": "2023-01-01", "end": "2024-01-01"}),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "summary": {
                    "total_return": 0.25,
                    "sharpe_simple": 1.8,
                    "max_drawdown": -0.1,
                    "trades": 12,
                    "win_rate": 0.6,
                }
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "sharpe_simple": 1.8,
                "total_return": 0.25,
                "max_drawdown": -0.1,
                "trades": 12,
            }
        ]
    ).to_csv(run_dir / "leaderboard.csv", index=False)

    _md_path, json_path = write_report(str(run_dir))

    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    contract = payload["machine_contract"]
    assert contract["schema_version"] == "1.0"
    assert contract["contract_type"] == "quantlab.sweep.result"
    assert contract["request_id"] == "req_123"
    assert contract["summary"]["sharpe_simple"] == 1.8
    assert contract["artifacts"]["metadata"] == "metadata.json"
    assert contract["artifacts"]["report"] == "report.json"


def test_handle_sweep_command_returns_machine_context(tmp_path):
    run_dir = tmp_path / "run_dir"
    run_dir.mkdir()
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "machine_contract": {
                    "run_id": "run_dir",
                    "mode": "grid",
                    "status": "success",
                    "summary": {"sharpe_simple": 1.5},
                }
            }
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "sweep.yaml"
    config_path.write_text("ticker: ETH-USD\n", encoding="utf-8")

    args = types.SimpleNamespace(
        sweep=str(config_path),
        sweep_outdir=None,
        outdir=None,
        _request_id="req_001",
    )

    result = handle_sweep_command(
        args,
        run_sweep=lambda *args, **kwargs: {
            "run_dir": str(run_dir),
            "report_path": str(report_path),
        },
    )

    assert result["run_id"] == "run_dir"
    assert result["status"] == "success"
    assert result["summary"]["sharpe_simple"] == 1.5
    assert result["report_path"] == str(report_path)
