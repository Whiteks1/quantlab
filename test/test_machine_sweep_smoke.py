from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import main as main_module


def test_machine_facing_sweep_smoke_validates_canonical_contract(
    monkeypatch, tmp_path
):
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
                    "request_id": "req_smoke_001",
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

    captured = {}

    def fake_run_sweep(
        config_path_arg: str,
        out_dir: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, str]:
        captured["config_path"] = config_path_arg
        captured["out_dir"] = out_dir
        captured["request_id"] = request_id
        return {
            "run_dir": str(run_dir),
            "report_path": str(report_path),
        }

    monkeypatch.setattr(main_module, "run_sweep", fake_run_sweep)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--json-request",
            json.dumps(
                {
                    "schema_version": "1.0",
                    "request_id": "req_smoke_001",
                    "command": "sweep",
                    "params": {
                        "config_path": str(config_path),
                        "out_dir": str(out_dir),
                    },
                }
            ),
            "--signal-file",
            str(signal_file),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 0
    assert captured == {
        "config_path": str(config_path),
        "out_dir": str(out_dir),
        "request_id": "req_smoke_001",
    }

    lines = [
        json.loads(line)
        for line in signal_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert lines[0]["event"] == "SESSION_STARTED"
    assert lines[-1]["event"] == "SESSION_COMPLETED"
    assert lines[-1]["report_path"] == str(report_path)
    assert lines[-1]["artifacts_path"] == str(run_dir)
    assert lines[-1]["summary"]["sharpe_simple"] == 1.7
    assert lines[-1]["run_id"] == run_dir.name
