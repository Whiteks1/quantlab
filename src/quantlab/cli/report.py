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
from quantlab.reporting.report import write_report as write_trade_report


def generate_legacy_report(
    *,
    outdir: str,
    ticker: str,
    strategy_name: str,
    backtest_metrics: dict,
    trades_path: str,
) -> str:
    """
    Internal helper for the legacy --report flag (Stage I).
    """
    import os
    meta = {
        "ticker": ticker,
        "strategy_name": strategy_name,
        "backtest_metrics": backtest_metrics,
    }

    report_md = os.path.join(outdir, "report.md")
    report_json = os.path.join(outdir, "report.json")

    payload = write_trade_report(
        trades_csv_path=trades_path,
        out_md_path=report_md,
        out_json_path=report_json,
        meta=meta,
    )

    metrics = payload.get("metrics", {})
    print("\n=== TRADE-LEVEL METRICS ===")
    print(f"Total Trades:  {metrics.get('trades', 0)}")
    print(f"Win Rate:      {metrics.get('win_rate_trades', 0.0):.2%}")
    print(f"Profit Factor: {metrics.get('profit_factor', 0.0):.2f}")
    print(f"Expectancy:    {metrics.get('expectancy_net', 0.0):.4f}")

    return report_md


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