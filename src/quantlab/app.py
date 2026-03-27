import argparse
import json
import os
import sys
import datetime as _dt
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
_DEFAULT_PROJECT_ROOT = _REPO_ROOT if (_REPO_ROOT / "main.py").exists() else _THIS_FILE.parents[1]
PROJECT_ROOT = _DEFAULT_PROJECT_ROOT
SRC_ROOT = PROJECT_ROOT / "src" if (PROJECT_ROOT / "src").exists() else _THIS_FILE.parents[1]
if SRC_ROOT.exists():
    src_root_str = str(SRC_ROOT)
    if src_root_str not in sys.path:
        sys.path.insert(0, src_root_str)

from quantlab import __version__
from quantlab.cli.app_args import build_argument_parser as _build_argument_parser_impl
from quantlab.cli.app_routing import (
    apply_json_request_overlay as _apply_json_request_overlay_impl,
    determine_session_mode as _determine_session_mode_impl,
    dispatch_json_request_command as _dispatch_json_request_command_impl,
    dispatch_standard_commands as _dispatch_standard_commands_impl,
    normalize_cli_aliases as _normalize_cli_aliases_impl,
    validate_json_request_contract as _validate_json_request_contract_impl,
)
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
handle_hyperliquid_submit_sessions_commands = None
handle_pretrade_handoff_commands = None
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
    _validate_json_request_contract_impl(command, params)


def _emit_version() -> None:
    print(__version__)


def _emit_health_check() -> int:
    main_path = PROJECT_ROOT / "main.py"
    if not main_path.exists():
        main_path = _THIS_FILE
    report = build_health_report(
        project_root=PROJECT_ROOT,
        main_path=main_path,
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
    global handle_hyperliquid_submit_sessions_commands
    global handle_pretrade_handoff_commands
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
    if handle_hyperliquid_submit_sessions_commands is None:
        from quantlab.cli.hyperliquid_submit_sessions import (
            handle_hyperliquid_submit_sessions_commands as _handle_hyperliquid_submit_sessions_commands,
        )

        handle_hyperliquid_submit_sessions_commands = _handle_hyperliquid_submit_sessions_commands
    if handle_pretrade_handoff_commands is None:
        from quantlab.cli.pretrade_handoff import (
            handle_pretrade_handoff_commands as _handle_pretrade_handoff_commands,
        )

        handle_pretrade_handoff_commands = _handle_pretrade_handoff_commands
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


def _build_argument_parser() -> argparse.ArgumentParser:
    return _build_argument_parser_impl()


def _normalize_cli_aliases(args: argparse.Namespace) -> None:
    _normalize_cli_aliases_impl(args)

def _apply_json_request_overlay(
    args: argparse.Namespace, session_metadata: dict[str, object]
) -> str | None:
    return _apply_json_request_overlay_impl(
        args,
        session_metadata,
        validate_contract=_validate_json_request_contract,
    )


def _determine_session_mode(args: argparse.Namespace, json_command: str | None) -> str:
    return _determine_session_mode_impl(args, json_command)


def _dispatch_json_request_command(args: argparse.Namespace, json_command: str | None):
    return _dispatch_json_request_command_impl(
        args,
        json_command,
        handle_run_command=handle_run_command,
        handle_sweep_command=handle_sweep_command,
        handle_forward_commands=handle_forward_commands,
        handle_portfolio_commands=handle_portfolio_commands,
        run_sweep=run_sweep,
        write_portfolio_report=write_portfolio_report,
        write_mode_comparison_report=write_mode_comparison_report,
    )


def _dispatch_standard_commands(args: argparse.Namespace, initial_result: object = None):
    return _dispatch_standard_commands_impl(
        args,
        initial_result,
        handle_broker_preflight_commands=handle_broker_preflight_commands,
        handle_broker_dry_run_commands=handle_broker_dry_run_commands,
        handle_broker_dry_runs_commands=handle_broker_dry_runs_commands,
        handle_broker_order_validations_commands=handle_broker_order_validations_commands,
        handle_hyperliquid_submit_sessions_commands=handle_hyperliquid_submit_sessions_commands,
        handle_pretrade_handoff_commands=handle_pretrade_handoff_commands,
        handle_paper_session_commands=handle_paper_session_commands,
        handle_runs_commands=handle_runs_commands,
        handle_report_commands=handle_report_commands,
        handle_forward_commands=handle_forward_commands,
        handle_portfolio_commands=handle_portfolio_commands,
        handle_sweep_command=handle_sweep_command,
        handle_run_command=handle_run_command,
        write_run_report=write_run_report,
        write_advanced_report=write_advanced_report,
        write_runs_index=write_runs_index,
        build_runs_index=build_runs_index,
        write_comparison=write_comparison,
        write_portfolio_report=write_portfolio_report,
        write_mode_comparison_report=write_mode_comparison_report,
        run_sweep=run_sweep,
    )


def main() -> None:
    load_dotenv()
    parser = _build_argument_parser()
    args = parser.parse_args()
    _normalize_cli_aliases(args)

    if args.version:
        _emit_version()
        sys.exit(0)

    if args.check:
        sys.exit(_emit_health_check())

    _load_runtime_dependencies()

    emitter = SignalEmitter(args.signal_file)
    session_metadata = {"mode": "unknown", "request_id": None}

    try:
        json_command = _apply_json_request_overlay(args, session_metadata)
        session_metadata["mode"] = _determine_session_mode(args, json_command)

        emitter.emit("SESSION_STARTED", "running", **session_metadata)

        result_ctx = _dispatch_json_request_command(args, json_command)
        result_ctx = _dispatch_standard_commands(args, result_ctx)

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

