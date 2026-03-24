from __future__ import annotations

import json
from typing import Any, Callable
from pathlib import Path

from quantlab.errors import ConfigError, QuantLabError
from quantlab.runs.artifacts import CANONICAL_REPORT_FILENAME


def handle_sweep_command(
    args,
    *,
    run_sweep: Callable[..., Any],
) -> dict | None:
    """
    Handle sweep-related CLI mode.

    Returns a metadata dictionary if sweep mode was executed,
    else None.
    """
    if args.sweep:
        config_path = Path(args.sweep)
        if not config_path.exists():
            raise ConfigError(f"Sweep config not found: {config_path}")

        out_dir = args.sweep_outdir or args.outdir
        sweep_result = run_sweep(
            str(config_path),
            out_dir=out_dir,
            request_id=getattr(args, "_request_id", None),
        )
        run_dir = Path(sweep_result["run_dir"])
        report_path = Path(sweep_result["report_path"])
        if not report_path.exists():
            raise QuantLabError(
                f"Sweep completed without canonical {CANONICAL_REPORT_FILENAME}: {report_path}"
            )

        with open(report_path, "r", encoding="utf-8") as fh:
            report = json.load(fh)
        machine_contract = report.get("machine_contract", {})

        return {
            "run_id": machine_contract.get("run_id", run_dir.name),
            "artifacts_path": str(run_dir),
            "report_path": str(report_path),
            "status": machine_contract.get("status", "success"),
            "summary": machine_contract.get("summary", {}),
            "mode": machine_contract.get("mode"),
            "runs_index_root": str(run_dir.parent),
        }

    return None
