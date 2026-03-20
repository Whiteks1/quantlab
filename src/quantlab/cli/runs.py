"""
runs.py — CLI handler for run navigation commands.

Responsibilities:
- listing all runs in a directory
- showing details for a single run
- finding the best run by a metric

This module delegates all domain logic to run_index.py.
It must not contain quantitative or business logic.
"""
from __future__ import annotations

from typing import Any


def handle_runs_commands(args) -> bool:
    """
    Handle run navigation CLI commands.

    Commands:
    - ``--runs-list <dir>``  : list all runs in a directory
    - ``--runs-show <dir>``  : show details for a single run
    - ``--runs-best <dir>``  : find the best run by a metric

    Returns True if a runs command was handled; False otherwise.
    """

    # --- RUNS LIST ---
    if getattr(args, "runs_list", None):
        from quantlab.reporting.run_index import build_runs_index
        payload = build_runs_index(args.runs_list)
        runs = payload.get("runs", [])
        n = payload.get("n_runs", len(runs))

        print(f"\nRuns in: {args.runs_list}")
        print(f"Total: {n} run(s) found\n")

        if not runs:
            print("  No valid run directories found.")
            return True

        _print_runs_table(runs, metric=getattr(args, "metric", "sharpe_simple"))
        return True

    # --- RUNS SHOW ---
    if getattr(args, "runs_show", None):
        from quantlab.reporting.run_index import load_run_summary
        run_dir = args.runs_show
        summary = load_run_summary(run_dir)

        print(f"\nRun: {run_dir}\n")
        for key, val in summary.items():
            print(f"  {key:20s}: {val}")
        return True

    # --- RUNS BEST ---
    if getattr(args, "runs_best", None):
        from quantlab.reporting.run_index import build_runs_index
        metric = getattr(args, "metric", "sharpe_simple")
        payload = build_runs_index(args.runs_best)
        runs = payload.get("runs", [])
        valid = [r for r in runs if r.get(metric) is not None]

        if not valid:
            print(f"No runs with metric '{metric}' found in {args.runs_best}")
            return True

        best = max(
            valid,
            key=lambda r: float(r[metric]) if r[metric] is not None else float("-inf"),
        )
        print(f"\nBest run by '{metric}':")
        print(f"  run_id  : {best.get('run_id')}")
        print(f"  {metric:12s}: {best.get(metric)}")
        print(f"  path    : {best.get('path')}")
        return True

    return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _print_runs_table(runs: list[dict[str, Any]], metric: str = "sharpe_simple") -> None:
    """Print a compact summary table of runs to stdout."""
    header_fields = ["run_id", "mode", "ticker", "created_at", metric, "trades"]

    # Determine column widths
    col_widths = {f: max(len(f), max((len(str(r.get(f) or "")) for r in runs), default=0))
                  for f in header_fields}

    # Header row
    header = "  ".join(f.ljust(col_widths[f]) for f in header_fields)
    print(header)
    print("-" * len(header))

    for r in runs:
        row = "  ".join(str(r.get(f) or "").ljust(col_widths[f]) for f in header_fields)
        print(row)
    print()