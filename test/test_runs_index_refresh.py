from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import main as main_module


def _prepare_main_mocks(monkeypatch, *, result_ctx: dict):
    captured: dict[str, object] = {}

    def fake_write_runs_index(root_dir: str):
        captured["root_dir"] = root_dir
        return (
            str(Path(root_dir) / "runs_index.csv"),
            str(Path(root_dir) / "runs_index.json"),
            str(Path(root_dir) / "runs_index.md"),
        )

    monkeypatch.setattr(main_module, "_load_runtime_dependencies", lambda: None)
    monkeypatch.setattr(main_module, "write_runs_index", fake_write_runs_index)
    monkeypatch.setattr(main_module, "handle_run_command", lambda args: result_ctx)
    monkeypatch.setattr(
        main_module,
        "handle_sweep_command",
        lambda args, run_sweep: result_ctx if getattr(args, "sweep", None) else None,
    )
    monkeypatch.setattr(
        main_module,
        "handle_forward_commands",
        lambda args: result_ctx if (getattr(args, "forward_eval", None) or getattr(args, "resume_forward", None)) else None,
    )
    monkeypatch.setattr(main_module, "handle_runs_commands", lambda args: None)
    monkeypatch.setattr(
        main_module,
        "handle_report_commands",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        main_module,
        "handle_portfolio_commands",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(main_module, "run_sweep", lambda *args, **kwargs: None)
    return captured


@pytest.mark.parametrize(
    ("argv", "result_ctx", "expected_root"),
    [
        (
            ["main.py"],
            {
                "run_id": "20260324_010000_run_deadbee",
                "artifacts_path": "outputs/runs/20260324_010000_run_deadbee",
                "report_path": "outputs/runs/20260324_010000_run_deadbee/report.json",
                "status": "success",
                "mode": "run",
                "runs_index_root": "outputs/runs",
            },
            str(Path("outputs") / "runs"),
        ),
        (
            [
                "main.py",
                "--json-request",
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "command": "sweep",
                        "params": {"config_path": "configs/test.yaml"},
                    }
                ),
            ],
            {
                "run_id": "20260324_010500_grid_deadbee",
                "artifacts_path": "outputs/runs/20260324_010500_grid_deadbee",
                "report_path": "outputs/runs/20260324_010500_grid_deadbee/report.json",
                "status": "success",
                "mode": "grid",
                "runs_index_root": "outputs/runs",
            },
            str(Path("outputs") / "runs"),
        ),
        (
            [
                "main.py",
                "--json-request",
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "command": "forward",
                        "params": {"run_dir": "outputs/runs/run_001"},
                    }
                ),
            ],
            {
                "run_id": "fwd_20260324_011000",
                "artifacts_path": "outputs/forward_runs/fwd_20260324_011000",
                "report_path": "outputs/forward_runs/fwd_20260324_011000/report.json",
                "status": "success",
                "mode": "forward",
                "runs_index_root": "outputs/runs",
            },
            str(Path("outputs") / "runs"),
        ),
    ],
)
def test_main_refreshes_runs_index_after_successful_run_producing_commands(
    monkeypatch,
    argv,
    result_ctx,
    expected_root,
):
    captured = _prepare_main_mocks(monkeypatch, result_ctx=result_ctx)
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 0
    assert captured["root_dir"] == expected_root
