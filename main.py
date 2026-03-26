# Backward compatibility for tests
import argparse
import json
import os
import sys
import datetime as _dt
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if SRC_ROOT.exists():
    src_root_str = str(SRC_ROOT)
    if src_root_str not in sys.path:
        sys.path.insert(0, src_root_str)

from quantlab import __version__
from quantlab.cli.health import build_health_report
from quantlab.errors import QuantLabError, ConfigError, DataError, StrategyError

fetch_ohlc = None
handle_sweep_command = None
handle_portfolio_commands = None
handle_forward_commands = None
handle_report_commands = None
handle_run_command = None
handle_runs_commands = None
handle_paper_session_commands = None
handle_broker_preflight_commands = None
handle_broker_dry_run_commands = None
handle_broker_dry_runs_commands = None
handle_broker_order_validations_commands = None
run_sweep = None
write_run_report = None
write_advanced_report = None
write_runs_index = None
build_runs_index = None
write_comparison = None
write_portfolio_report = None
write_mode_comparison_report = None


class SignalEmitter:
    """
    Best-effort signalling via append-only JSON Lines file.
    """

    def __init__(self, signal_file: Optional[str], schema_version: str = "1.0"):
        self.signal_file = signal_file
        self.schema_version = schema_version

    def emit(self, event: str, status: str, **kwargs) -> None:
        if not self.signal_file:
            return

        payload = {
            "schema_version": self.schema_version,
            "event": event,
            "status": status,
            "timestamp": _dt.datetime.now().replace(microsecond=0).isoformat(),
        }
        payload.update(kwargs)

        try:
            with open(self.signal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            # Signal failure must not crash the main execution path.
            print(
                f"Warning: Failed to write signal to {self.signal_file}: {e}",
                file=sys.stderr,
            )


def _validate_json_request_contract(command: str, params: object) -> None:
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ConfigError("'params' in JSON request must be an object.")

    if command == "sweep":
        config_path = params.get("config_path") or params.get("sweep")
        if not isinstance(config_path, str) or not config_path.strip():
            raise ConfigError(
                "JSON request for 'sweep' requires params.config_path as a non-empty string."
            )


def _emit_version() -> None:
    print(__version__)


def _emit_health_check() -> int:
    report = build_health_report(
        project_root=PROJECT_ROOT,
        main_path=PROJECT_ROOT / "main.py",
        src_root=SRC_ROOT,
        interpreter=sys.executable,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 2


def _refresh_runs_index_if_needed(
    *,
    session_mode: str,
    result_ctx: object,
) -> dict[str, str]:
    if session_mode not in {"run", "sweep", "forward"}:
        return {}
    if not isinstance(result_ctx, dict):
        return {}
    if result_ctx.get("status") not in (None, "success"):
        return {}

    root = result_ctx.get("runs_index_root")
    root_path = Path(root) if isinstance(root, str) and root.strip() else PROJECT_ROOT / "outputs" / "runs"
    csv_path, json_path, md_path = write_runs_index(str(root_path))
    return {
        "runs_index_root": str(root_path),
        "runs_index_csv": csv_path,
        "runs_index_json": json_path,
        "runs_index_md": md_path,
    }


def _load_runtime_dependencies() -> None:
    global fetch_ohlc
    global handle_sweep_command
    global handle_portfolio_commands
    global handle_forward_commands
    global handle_report_commands
    global handle_run_command
    global handle_runs_commands
    global handle_paper_session_commands
    global handle_broker_preflight_commands
    global handle_broker_dry_run_commands
    global handle_broker_dry_runs_commands
    global handle_broker_order_validations_commands
    global run_sweep
    global write_run_report
    global write_advanced_report
    global write_runs_index
    global build_runs_index
    global write_comparison
    global write_portfolio_report
    global write_mode_comparison_report

    if fetch_ohlc is None:
        from quantlab.data.sources import fetch_ohlc as _fetch_ohlc

        fetch_ohlc = _fetch_ohlc
    if handle_sweep_command is None:
        from quantlab.cli.sweep import handle_sweep_command as _handle_sweep_command

        handle_sweep_command = _handle_sweep_command
    if handle_portfolio_commands is None:
        from quantlab.cli.portfolio import (
            handle_portfolio_commands as _handle_portfolio_commands,
        )

        handle_portfolio_commands = _handle_portfolio_commands
    if handle_forward_commands is None:
        from quantlab.cli.forward import handle_forward_commands as _handle_forward_commands

        handle_forward_commands = _handle_forward_commands
    if handle_report_commands is None:
        from quantlab.cli.report import handle_report_commands as _handle_report_commands

        handle_report_commands = _handle_report_commands
    if handle_run_command is None:
        from quantlab.cli.run import handle_run_command as _handle_run_command

        handle_run_command = _handle_run_command
    if handle_runs_commands is None:
        from quantlab.cli.runs import handle_runs_commands as _handle_runs_commands

        handle_runs_commands = _handle_runs_commands
    if handle_paper_session_commands is None:
        from quantlab.cli.paper_sessions import (
            handle_paper_session_commands as _handle_paper_session_commands,
        )

        handle_paper_session_commands = _handle_paper_session_commands
    if handle_broker_dry_run_commands is None:
        from quantlab.cli.broker_dry_run import (
            handle_broker_dry_run_commands as _handle_broker_dry_run_commands,
        )

        handle_broker_dry_run_commands = _handle_broker_dry_run_commands
    if handle_broker_preflight_commands is None:
        from quantlab.cli.broker_preflight import (
            handle_broker_preflight_commands as _handle_broker_preflight_commands,
        )

        handle_broker_preflight_commands = _handle_broker_preflight_commands
    if handle_broker_dry_runs_commands is None:
        from quantlab.cli.broker_dry_runs import (
            handle_broker_dry_runs_commands as _handle_broker_dry_runs_commands,
        )

        handle_broker_dry_runs_commands = _handle_broker_dry_runs_commands
    if handle_broker_order_validations_commands is None:
        from quantlab.cli.broker_order_validations import (
            handle_broker_order_validations_commands as _handle_broker_order_validations_commands,
        )

        handle_broker_order_validations_commands = _handle_broker_order_validations_commands
    if run_sweep is None:
        from quantlab.experiments import run_sweep as _run_sweep

        run_sweep = _run_sweep
    if write_run_report is None:
        from quantlab.reporting.run_report import write_report as _write_run_report

        write_run_report = _write_run_report
    if write_advanced_report is None:
        from quantlab.reporting.advanced_report import (
            write_advanced_report as _write_advanced_report,
        )

        write_advanced_report = _write_advanced_report
    if write_runs_index is None or build_runs_index is None:
        from quantlab.reporting.run_index import (
            write_runs_index as _write_runs_index,
            build_runs_index as _build_runs_index,
        )

        write_runs_index = _write_runs_index
        build_runs_index = _build_runs_index
    if write_comparison is None:
        from quantlab.reporting.compare_runs import write_comparison as _write_comparison

        write_comparison = _write_comparison
    if write_portfolio_report is None:
        from quantlab.reporting.portfolio_report import (
            write_portfolio_report as _write_portfolio_report,
        )

        write_portfolio_report = _write_portfolio_report
    if write_mode_comparison_report is None:
        from quantlab.reporting.portfolio_mode_compare import (
            write_mode_comparison_report as _write_mode_comparison_report,
        )

        write_mode_comparison_report = _write_mode_comparison_report


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="QuantLab MVP: research-first trading experiment engine."
    )
    # Global / Request params
    parser.add_argument(
        "--json-request",
        help="Pass a V1 Stepbit Request JSON string directly.",
    )
    parser.add_argument(
        "--signal-file",
        help="Path to an append-only JSON Lines file for session signals.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the current QuantLab version and exit.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run lightweight runtime health checks and exit.",
    )

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
    parser.add_argument(
        "--outdir", default=None, help="Output directory (default: outputs)"
    )
    parser.add_argument("--save_price_plot", action="store_true")

    # Paper broker
    parser.add_argument(
        "--paper",
        action="store_true",
        help="Ejecuta paper broker + CSV de trades",
    )
    parser.add_argument(
        "--initial_cash",
        type=float,
        default=1000.0,
        help="Cash inicial para paper broker",
    )

    # Slippage
    parser.add_argument(
        "--slippage_bps",
        type=float,
        default=8.0,
        help="Slippage fijo en bps (10bps=0.10%%)",
    )
    parser.add_argument("--slippage_mode", default="fixed", choices=["fixed", "atr"])
    parser.add_argument(
        "--k_atr",
        type=float,
        default=0.05,
        help="Sensibilidad slippage ATR (si slippage_mode=atr)",
    )

    # Reporting / Sweep
    parser.add_argument(
        "--report",
        nargs="?",
        const=True,
        help="Genera report para un run (pasa el path) o para la ejecución actual",
    )
    parser.add_argument("--trades_csv", default=None)
    parser.add_argument("--sweep", help="Path a .yaml de configuración para grid search")
    parser.add_argument("--sweep_outdir", default=None)

    # Run navigation (Stage N)
    parser.add_argument(
        "--runs-list",
        metavar="ROOT_DIR",
        default=None,
        help="List all runs in a directory.",
    )
    parser.add_argument(
        "--runs-show",
        metavar="RUN_DIR",
        default=None,
        help="Show details for a single run.",
    )
    parser.add_argument(
        "--runs-best",
        metavar="ROOT_DIR",
        default=None,
        help="Find the best run by a metric.",
    )
    parser.add_argument(
        "--paper-sessions-list",
        metavar="ROOT_DIR",
        default=None,
        help="List paper sessions in a directory.",
    )
    parser.add_argument(
        "--paper-sessions-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single paper session.",
    )
    parser.add_argument(
        "--paper-sessions-health",
        metavar="ROOT_DIR",
        default=None,
        help="Summarize paper session health in a directory.",
    )
    parser.add_argument(
        "--paper-sessions-alerts",
        metavar="ROOT_DIR",
        default=None,
        help="Emit a deterministic alert snapshot for paper sessions in a directory.",
    )
    parser.add_argument(
        "--paper-stale-minutes",
        type=int,
        default=60,
        help="Minutes before a running paper session is treated as stale.",
    )
    parser.add_argument(
        "--paper-sessions-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared paper-session index artifacts in a directory.",
    )
    parser.add_argument(
        "--kraken-dry-run-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken dry-run audit artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-preflight-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken read-only preflight artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-auth-preflight-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken authenticated read-only preflight artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-account-readiness-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken authenticated account snapshot and intent readiness artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-order-validate-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken validate-only order probe artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-order-validate-session",
        action="store_true",
        help="Persist a canonical broker order-validation session under outputs/broker_order_validations.",
    )
    parser.add_argument(
        "--kraken-preflight-timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for Kraken public preflight probes.",
    )
    parser.add_argument("--kraken-api-key", default=None)
    parser.add_argument("--kraken-api-secret", default=None)
    parser.add_argument("--kraken-api-key-env", default="KRAKEN_API_KEY")
    parser.add_argument("--kraken-api-secret-env", default="KRAKEN_API_SECRET")
    parser.add_argument(
        "--kraken-dry-run-session",
        action="store_true",
        help="Persist a canonical Kraken dry-run session under outputs/broker_dry_runs.",
    )
    parser.add_argument(
        "--broker-dry-runs-root",
        metavar="ROOT_DIR",
        default=None,
        help="Root directory for canonical broker dry-run sessions.",
    )
    parser.add_argument(
        "--broker-dry-runs-list",
        metavar="ROOT_DIR",
        default=None,
        help="List broker dry-run sessions in a directory.",
    )
    parser.add_argument(
        "--broker-dry-runs-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single broker dry-run session.",
    )
    parser.add_argument(
        "--broker-dry-runs-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared broker dry-run index artifacts in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-root",
        metavar="ROOT_DIR",
        default=None,
        help="Root directory for canonical broker order-validation sessions.",
    )
    parser.add_argument(
        "--broker-order-validations-list",
        metavar="ROOT_DIR",
        default=None,
        help="List broker order-validation sessions in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single broker order-validation session.",
    )
    parser.add_argument(
        "--broker-order-validations-health",
        metavar="ROOT_DIR",
        default=None,
        help="Summarize broker submission health in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-alerts",
        metavar="ROOT_DIR",
        default=None,
        help="Emit a deterministic alert snapshot for broker submission sessions in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared broker order-validation index artifacts in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-approve",
        metavar="SESSION_DIR",
        default=None,
        help="Approve a broker order-validation session locally.",
    )
    parser.add_argument(
        "--broker-order-validations-bundle",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a pre-submit bundle from an approved broker order-validation session.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-gate",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a supervised submit gate artifact from a pre-submit bundle.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-stub",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a supervised submit stub artifact from a submit gate.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-real",
        metavar="SESSION_DIR",
        default=None,
        help="Submit a real Kraken order from a supervised submit gate and persist the response artifact.",
    )
    parser.add_argument(
        "--broker-order-validations-reconcile",
        metavar="SESSION_DIR",
        default=None,
        help="Reconcile an existing broker submit response against Kraken order state.",
    )
    parser.add_argument(
        "--broker-order-validations-status",
        metavar="SESSION_DIR",
        default=None,
        help="Refresh normalized post-submit order status for a broker order-validation session.",
    )
    parser.add_argument(
        "--broker-approval-reviewer",
        default=None,
        help="Reviewer name/id for local broker approval actions.",
    )
    parser.add_argument(
        "--broker-approval-note",
        default=None,
        help="Optional note for local broker approval actions.",
    )
    parser.add_argument(
        "--broker-submit-reviewer",
        default=None,
        help="Reviewer name/id for supervised submit gate actions.",
    )
    parser.add_argument(
        "--broker-submit-note",
        default=None,
        help="Optional note for supervised submit gate actions.",
    )
    parser.add_argument(
        "--broker-submit-confirm",
        action="store_true",
        help="Explicit confirmation flag required for supervised submit gate and real submit actions.",
    )
    parser.add_argument(
        "--broker-submit-live",
        action="store_true",
        help="Explicit live-submit flag required before sending a real broker order.",
    )
    parser.add_argument("--broker-symbol", default=None)
    parser.add_argument("--broker-side", default=None)
    parser.add_argument("--broker-quantity", type=float, default=None)
    parser.add_argument("--broker-notional", type=float, default=None)
    parser.add_argument("--broker-account-id", default=None)
    parser.add_argument("--broker-strategy-id", default=None)
    parser.add_argument("--broker-max-notional", type=float, default=None)
    parser.add_argument("--broker-allowed-symbols", default=None)
    parser.add_argument("--broker-kill-switch", action="store_true")
    parser.add_argument("--broker-allow-missing-account-id", action="store_true")
    parser.add_argument(
        "--metric",
        default="sharpe_simple",
        help="Metric to rank by (used with --runs-best, --best-from).",
    )

    # Stage J/K/L/M Flags (legacy — use --runs-* equivalents)
    parser.add_argument(
        "--list-runs",
        metavar="ROOT_DIR",
        default=None,
        help="[Deprecated] Use --runs-list.",
    )
    parser.add_argument(
        "--best-from",
        metavar="ROOT_DIR",
        default=None,
        help="[Deprecated] Use --runs-best.",
    )
    parser.add_argument("--compare", nargs="+", metavar="RUN_DIR")
    parser.add_argument("--advanced-report", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-eval", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-start", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-end", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-outdir", metavar="DIR", default=None)
    parser.add_argument("--forward-metric", default="sharpe_simple")
    parser.add_argument("--resume-forward", metavar="SESSION_DIR", default=None)
    parser.add_argument("--portfolio-report", metavar="ROOT_DIR", default=None)
    parser.add_argument(
        "--portfolio-mode",
        default="raw_capital",
        choices=["raw_capital", "equal_weight", "custom_weight"],
    )
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

    if args.version:
        _emit_version()
        sys.exit(0)

    if args.check:
        sys.exit(_emit_health_check())

    _load_runtime_dependencies()

    emitter = SignalEmitter(args.signal_file)
    session_metadata = {"mode": "unknown", "request_id": None}

    try:
        # --- JSON Request Overlay ---
        _json_command: str | None = None  # tracks command for explicit dispatch below

        if args.json_request:
            try:
                req = json.loads(args.json_request)

                # 1) Validate schema version
                schema_version = req.get("schema_version")
                if schema_version != "1.0":
                    raise ConfigError(
                        f"Unsupported or missing schema_version '{schema_version}'. Expected '1.0'."
                    )

                # 2) Require command
                _json_command = req.get("command")
                if not _json_command:
                    raise ConfigError("Missing 'command' in JSON request.")

                # 3) Propagate request_id
                args._request_id = req.get("request_id")
                session_metadata["request_id"] = args._request_id

                # 4) Map params
                params = req.get("params", {})
                _validate_json_request_contract(_json_command, params)
                for k, v in params.items():
                    if hasattr(args, k):
                        setattr(args, k, v)

                # 5) Explicit param routing for nested/non-obvious flags
                if _json_command == "sweep":
                    args.sweep = params.get("config_path") or params.get("sweep")
                    if "out_dir" in params:
                        args.sweep_outdir = params["out_dir"]
                    elif "sweep_outdir" in params:
                        args.sweep_outdir = params["sweep_outdir"]
                elif _json_command == "forward" and "run_dir" in params:
                    args.forward_eval = params["run_dir"]

            except (json.JSONDecodeError, TypeError) as e:
                raise ConfigError(f"Invalid --json-request payload: {e}")

        # Determine mode for signalling after validation and just before execution
        if _json_command:
            session_metadata["mode"] = _json_command
        elif args.sweep:
            session_metadata["mode"] = "sweep"
        elif args.forward_eval or args.resume_forward:
            session_metadata["mode"] = "forward"
        elif args.portfolio_report or args.portfolio_compare:
            session_metadata["mode"] = "portfolio"
        elif args.paper:
            session_metadata["mode"] = "paper"
        elif args.report:
            session_metadata["mode"] = "report"
        elif (
            args.paper_sessions_list
            or args.paper_sessions_show
            or args.paper_sessions_health
            or args.paper_sessions_alerts
            or args.paper_sessions_index
        ):
            session_metadata["mode"] = "paper_sessions"
        elif (
            args.kraken_preflight_outdir
            or args.kraken_auth_preflight_outdir
            or args.kraken_account_readiness_outdir
        ):
            session_metadata["mode"] = "broker_preflight"
        elif (
            args.kraken_order_validate_outdir
            or args.kraken_order_validate_session
            or args.broker_order_validations_list
            or args.broker_order_validations_show
            or args.broker_order_validations_health
            or args.broker_order_validations_alerts
            or args.broker_order_validations_index
            or args.broker_order_validations_approve
            or args.broker_order_validations_bundle
            or args.broker_order_validations_submit_gate
            or args.broker_order_validations_submit_stub
            or args.broker_order_validations_submit_real
            or args.broker_order_validations_reconcile
            or args.broker_order_validations_status
        ):
            session_metadata["mode"] = "broker_validate"
        elif (
            args.kraken_dry_run_outdir
            or args.kraken_dry_run_session
            or args.broker_dry_runs_list
            or args.broker_dry_runs_show
            or args.broker_dry_runs_index
        ):
            session_metadata["mode"] = "broker_dry_run"
        elif args.runs_list or args.runs_show or args.runs_best:
            session_metadata["mode"] = "runs"
        else:
            session_metadata["mode"] = "run"

        emitter.emit("SESSION_STARTED", "running", **session_metadata)

        # --- COMMAND ROUTING (Order matters: specific -> generic) ---
        result_ctx = None

        # Explicit dispatch for machine-driven requests via --json-request.
        if _json_command:
            if _json_command == "run":
                result_ctx = handle_run_command(args)
            elif _json_command == "sweep":
                result_ctx = handle_sweep_command(args, run_sweep=run_sweep)
            elif _json_command == "forward":
                result_ctx = handle_forward_commands(args)
            elif _json_command == "portfolio":
                result_ctx = handle_portfolio_commands(
                    args,
                    write_portfolio_report=write_portfolio_report,
                    write_mode_comparison_report=write_mode_comparison_report,
                )
            else:
                raise ConfigError(
                    f"Unknown command '{_json_command}'. "
                    "Valid commands: run, sweep, forward, portfolio."
                )

        # --- Standard flag-driven routing (human CLI use) ---
        if result_ctx in (None, False):
            result_ctx = handle_broker_preflight_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_broker_dry_run_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_broker_dry_runs_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_broker_order_validations_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_paper_session_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_runs_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_report_commands(
                args,
                write_run_report=write_run_report,
                write_advanced_report=write_advanced_report,
                write_runs_index=write_runs_index,
                build_runs_index=build_runs_index,
                write_comparison=write_comparison,
            )

        if result_ctx in (None, False):
            result_ctx = handle_forward_commands(args)

        if result_ctx in (None, False):
            result_ctx = handle_portfolio_commands(
                args,
                write_portfolio_report=write_portfolio_report,
                write_mode_comparison_report=write_mode_comparison_report,
            )

        if result_ctx in (None, False):
            result_ctx = handle_sweep_command(
                args,
                run_sweep=run_sweep,
            )

        # Final fallthrough: classic run
        if result_ctx in (None, False):
            result_ctx = handle_run_command(args)

        extra_ctx = result_ctx if isinstance(result_ctx, dict) else {}
        extra_ctx.update(
            _refresh_runs_index_if_needed(
                session_mode=session_metadata["mode"],
                result_ctx=result_ctx,
            )
        )
        completion_ctx = dict(session_metadata)
        completion_ctx.update(extra_ctx)
        completion_ctx.pop("status", None)
        completion_ctx.pop("event", None)
        emitter.emit(
            "SESSION_COMPLETED",
            "success",
            **completion_ctx,
        )
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nAborted by user.")
        emitter.emit(
            "SESSION_FAILED",
            "error",
            **session_metadata,
            exit_code=1,
            error_type="KeyboardInterrupt",
            message="Aborted by user",
        )
        sys.exit(1)
    except QuantLabError as e:
        # Known QuantLab errors: print clean message to stderr, exit with mapped code, no traceback.
        print(f"ERROR: {e}", file=sys.stderr)

        exit_code = 1
        if isinstance(e, ConfigError):
            exit_code = 2
        elif isinstance(e, DataError):
            exit_code = 3
        elif isinstance(e, StrategyError):
            exit_code = 4

        emitter.emit(
            "SESSION_FAILED",
            "error",
            **session_metadata,
            exit_code=exit_code,
            error_type=e.__class__.__name__,
            message=str(e),
        )
        sys.exit(exit_code)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        emitter.emit(
            "SESSION_FAILED",
            "error",
            **session_metadata,
            exit_code=1,
            error_type=e.__class__.__name__,
            message=str(e),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
