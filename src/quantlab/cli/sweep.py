from __future__ import annotations

from typing import Any, Callable
from pathlib import Path


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
        out_dir = args.sweep_outdir or args.outdir
        run_dir = run_sweep(args.sweep, out_dir=out_dir)
        return {
            "run_id": Path(run_dir).name if run_dir else None,
            "artifacts_path": str(run_dir) if run_dir else None,
            "report_path": str(Path(run_dir) / "report.json") if run_dir else None
        }

    return None