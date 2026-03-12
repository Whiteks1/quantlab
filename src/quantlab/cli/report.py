from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from quantlab.reporting.run_report import write_report as default_write_run_report
from quantlab.reporting.run_index import (
    write_runs_index as default_write_runs_index,
    build_runs_index as default_build_runs_index,
)
from quantlab.reporting.compare_runs import write_comparison as default_write_comparison
from quantlab.reporting.advanced_report import (
    write_advanced_report as default_write_advanced_report,
)


def handle_report_commands(
    args,
    *,
    write_run_report: Callable[[str], Any] = default_write_run_report,
    write_advanced_report: Callable[[str], Any] = default_write_advanced_report,
    write_runs_index: Callable[[str], Any] = default_write_runs_index,
    build_runs_index: Callable[[str], Any] = default_build_runs_index,
    write_comparison: Callable[..., Any] = default_write_comparison,
) -> bool:
    """
    Handle report-related CLI modes.

    Returns True if a report-related command was executed and the caller
    should exit early.
    Returns False if no report-related mode matched.
    """

    # --- REPORT-ONLY MODE ---
    if isinstance(args.report, str) and Path(args.report).is_dir():
        write_run_report(args.report)
        print(f"Standardized run report generated for: {args.report}")
        return True

    # --- ADVANCED REPORT MODE ---
    if args.advanced_report:
        json_p, md_p = write_advanced_report(args.advanced_report)
        print(f"Advanced report generated for: {args.advanced_report}")
        print(f"  JSON: {json_p}")
        print(f"  MD  : {md_p}")
        return True

    # --- LIST-RUNS MODE ---
    if args.list_runs:
        csv_p, json_p, md_p = write_runs_index(args.list_runs)
        print("Runs index written:")
        print(f"  CSV : {csv_p}")
        print(f"  JSON: {json_p}")
        print(f"  MD  : {md_p}")
        return True

    # --- BEST-FROM MODE ---
    if args.best_from:
        payload = build_runs_index(args.best_from)
        runs = payload.get("runs", [])
        metric = args.metric
        valid = [r for r in runs if r.get(metric) is not None]

        if not valid:
            print(f"No runs with metric '{metric}' found in {args.best_from}")
            return True

        best = max(
            valid,
            key=lambda r: float(r[metric]) if r[metric] is not None else float("-inf"),
        )

        print(f"Best run by '{metric}':")
        print(f"  run_id : {best.get('run_id')}")
        print(f"  {metric:12s}: {best.get(metric)}")
        print(f"  path   : {best.get('path')}")
        return True

    # --- COMPARE MODE ---
    if args.compare:
        out_dir = args.outdir or "."
        json_p, md_p = write_comparison(
            args.compare,
            out_path=out_dir,
            sort_by=args.metric,
        )
        print("Comparison report written:")
        print(f"  JSON: {json_p}")
        print(f"  MD  : {md_p}")
        return True

    return False