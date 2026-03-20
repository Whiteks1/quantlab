# Backward compatibility for tests
from quantlab.data.sources import fetch_ohlc

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# CLI Handlers
from quantlab.cli.sweep import handle_sweep_command
from quantlab.cli.portfolio import handle_portfolio_commands
from quantlab.cli.forward import handle_forward_commands
from quantlab.cli.report import handle_report_commands
from quantlab.cli.run import handle_run_command
from quantlab.cli.runs import handle_runs_commands

# Real Implementation Dependencies
from quantlab.experiments import run_sweep
from quantlab.reporting.run_report import write_report as write_run_report
from quantlab.reporting.advanced_report import write_advanced_report
from quantlab.reporting.run_index import write_runs_index, build_runs_index
from quantlab.reporting.compare_runs import write_comparison
from quantlab.reporting.portfolio_report import write_portfolio_report
from quantlab.reporting.portfolio_mode_compare import write_mode_comparison_report


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="QuantLab MVP: research-first trading experiment engine."
    )
    # Global / Request params
    parser.add_argument("--json-request", help="Pass a V1 Stepbit Request JSON string directly.")
    
    parser.add_argument("--ticker", default="ETH-USD")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--fee", type=float, default=0.002)

    # Strategy (legacy flags)
    parser.add_argument("--rsi_buy_max", type=float, default=60.0)
    parser.add_argument("--rsi_sell_min", type=float, default=75.0)
    parser.add_argument("--cooldown_days", type=int, default=0)

    # Output
    parser.add_argument("--outdir", default=None, help="Output directory (default: outputs)")
    parser.add_argument("--save_price_plot", action="store_true")

    # Paper broker
    parser.add_argument("--paper", action="store_true", help="Ejecuta paper broker + CSV de trades")
    parser.add_argument("--initial_cash", type=float, default=1000.0, help="Cash inicial para paper broker")

    # Slippage
    parser.add_argument("--slippage_bps", type=float, default=8.0, help="Slippage fijo en bps (10bps=0.10%)")
    parser.add_argument("--slippage_mode", default="fixed", choices=["fixed", "atr"])
    parser.add_argument("--k_atr", type=float, default=0.05, help="Sensibilidad slippage ATR (si slippage_mode=atr)")

    # Reporting / Sweep
    parser.add_argument("--report", nargs="?", const=True, help="Genera report para un run (pasa el path) o para la ejecución actual")
    parser.add_argument("--trades_csv", default=None)
    parser.add_argument("--sweep", help="Path a .yaml de configuración para grid search")
    parser.add_argument("--sweep_outdir", default=None)

    # Run navigation (Stage N)
    parser.add_argument("--runs-list", metavar="ROOT_DIR", default=None, help="List all runs in a directory.")
    parser.add_argument("--runs-show", metavar="RUN_DIR", default=None, help="Show details for a single run.")
    parser.add_argument("--runs-best", metavar="ROOT_DIR", default=None, help="Find the best run by a metric.")
    parser.add_argument("--metric", default="sharpe_simple", help="Metric to rank by (used with --runs-best, --best-from).")

    # Stage J/K/L/M Flags (legacy — use --runs-* equivalents)
    parser.add_argument("--list-runs", metavar="ROOT_DIR", default=None, help="[Deprecated] Use --runs-list.")
    parser.add_argument("--best-from", metavar="ROOT_DIR", default=None, help="[Deprecated] Use --runs-best.")
    parser.add_argument("--compare", nargs="+", metavar="RUN_DIR")
    parser.add_argument("--advanced-report", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-eval", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-start", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-end", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-outdir", metavar="DIR", default=None)
    parser.add_argument("--forward-metric", default="sharpe_simple")
    parser.add_argument("--resume-forward", metavar="SESSION_DIR", default=None)
    parser.add_argument("--portfolio-report", metavar="ROOT_DIR", default=None)
    parser.add_argument("--portfolio-mode", default="raw_capital", choices=["raw_capital", "equal_weight", "custom_weight"])
    parser.add_argument("--portfolio-weights", metavar="JSON_FILE", default=None)
    parser.add_argument("--portfolio-top-n", type=int, default=None)
    parser.add_argument("--portfolio-rank-metric", default="total_return")
    parser.add_argument("--portfolio-min-return", type=float, default=None)
    parser.add_argument("--portfolio-max-drawdown", type=float, default=None)
    parser.add_argument("--portfolio-include-tickers", default=None)
    parser.add_argument("--portfolio-exclude-tickers", default=None)
    parser.add_argument("--portfolio-include-strategies", default=None)
    parser.add_argument("--portfolio-exclude-strategies", default=None)
    parser.add_argument("--portfolio-latest-per-source-run", action="store_true")
    parser.add_argument("--portfolio-compare", metavar="ROOT_DIR", default=None)

    args = parser.parse_args()

    # --- Backward-compat aliases: map deprecated flags to new ones ---
    if getattr(args, "list_runs", None) and not getattr(args, "runs_list", None):
        args.runs_list = args.list_runs
    if getattr(args, "best_from", None) and not getattr(args, "runs_best", None):
        args.runs_best = args.best_from

    # --- JSON Request Overlay ---
    if args.json_request:
        try:
            req = json.loads(args.json_request)
            cmd = req.get("command")
            params = req.get("params", {})
            
            # Map params to args for existing handlers
            for k, v in params.items():
                if hasattr(args, k):
                    setattr(args, k, v)
                
            if cmd == "sweep" and "config_path" in params: args.sweep = params["config_path"]
            elif cmd == "forward" and "run_dir" in params: args.forward_eval = params["run_dir"]
        except Exception as e:
            print(f"ERROR: Invalid --json-request payload: {e}")
            sys.exit(2)

    try:
        # --- COMMAND ROUTING (Order matters: specific -> generic) ---
        if handle_runs_commands(args):
            sys.exit(0)

        if handle_report_commands(
            args,
            write_run_report=write_run_report,
            write_advanced_report=write_advanced_report,
            write_runs_index=write_runs_index,
            build_runs_index=build_runs_index,
            write_comparison=write_comparison,
        ):
            sys.exit(0)

        if handle_forward_commands(args):
            sys.exit(0)
        
        if handle_portfolio_commands(
            args,
            write_portfolio_report=write_portfolio_report,
            write_mode_comparison_report=write_mode_comparison_report,
        ):
            sys.exit(0)

        if handle_sweep_command(
            args,
            run_sweep=run_sweep,
        ):
            sys.exit(0)

        # Final fallthrough: classic run
        if handle_run_command(args):
            sys.exit(0)
            
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()