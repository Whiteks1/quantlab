from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def _parse_list(value: str | None):
    return [item.strip() for item in value.split(",")] if value else None


def _load_weights(weights_path: str | None):
    if not weights_path:
        return None

    with open(weights_path, "r", encoding="utf-8") as f:
        return json.load(f)


def handle_portfolio_commands(
    args,
    *,
    write_portfolio_report: Callable[..., Any],
    write_mode_comparison_report: Callable[..., Any],
) -> bool:
    """
    Handle portfolio-related CLI modes.

    Returns True if a portfolio command was executed and the caller
    should exit early.
    Returns False otherwise.
    """

    # --- PORTFOLIO REPORT MODE ---
    if args.portfolio_report:
        root = Path(args.portfolio_report)
        if not root.exists():
            print(f"ERROR: Portfolio root directory not found: {root}")
            return True

        print("\n=== STAGE M: PORTFOLIO AGGREGATION ===")
        print(f"  Scanning: {root}")

        sessions = [d for d in root.iterdir() if d.is_dir() and (d / "portfolio_state.json").exists()]
        if not sessions:
            print(f"  No valid forward sessions found in {root}")
            return True

        print(f"  Found {len(sessions)} sessions.")

        try:
            weights = _load_weights(args.portfolio_weights)
        except Exception as e:
            print(f"ERROR: Could not load portfolio weights from {args.portfolio_weights}: {e}")
            return True

        json_p, md_p = write_portfolio_report(
            sessions,
            root,
            mode=args.portfolio_mode,
            weights=weights,
            top_n=args.portfolio_top_n,
            rank_metric=args.portfolio_rank_metric,
            min_return=args.portfolio_min_return,
            max_drawdown=args.portfolio_max_drawdown,
            include_tickers=_parse_list(args.portfolio_include_tickers),
            exclude_tickers=_parse_list(args.portfolio_exclude_tickers),
            include_strategies=_parse_list(args.portfolio_include_strategies),
            exclude_strategies=_parse_list(args.portfolio_exclude_strategies),
            latest_per_source_run=args.portfolio_latest_per_source_run,
        )
        print(f"  Portfolio report generated ({args.portfolio_mode}):")
        print(f"    -> {json_p}")
        print(f"    -> {md_p}")
        return True

    # --- PORTFOLIO COMPARISON MODE ---
    if args.portfolio_compare:
        root = Path(args.portfolio_compare)
        if not root.exists():
            print(f"ERROR: Portfolio root directory not found: {root}")
            return True

        print("\n=== STAGE M.4: PORTFOLIO MODE COMPARISON ===")
        print(f"  Scanning: {root}")

        sessions = [d for d in root.iterdir() if d.is_dir() and (d / "portfolio_state.json").exists()]
        if not sessions:
            print(f"  No valid forward sessions found in {root}")
            return True

        try:
            weights = _load_weights(args.portfolio_weights)
        except Exception as e:
            print(f"ERROR: Could not load portfolio weights from {args.portfolio_weights}: {e}")
            return True

        json_p, md_p = write_mode_comparison_report(
            sessions,
            root,
            weights=weights,
            top_n=args.portfolio_top_n,
            rank_metric=args.portfolio_rank_metric,
            min_return=args.portfolio_min_return,
            max_drawdown=args.portfolio_max_drawdown,
            include_tickers=_parse_list(args.portfolio_include_tickers),
            exclude_tickers=_parse_list(args.portfolio_exclude_tickers),
            include_strategies=_parse_list(args.portfolio_include_strategies),
            exclude_strategies=_parse_list(args.portfolio_exclude_strategies),
            latest_per_source_run=args.portfolio_latest_per_source_run,
        )
        print("  Comparison report generated:")
        print(f"    -> {json_p}")
        print(f"    -> {md_p}")
        return True

    return False
