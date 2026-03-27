import argparse
import json
from collections.abc import Callable

from quantlab.errors import ConfigError


def validate_json_request_contract(command: str, params: object) -> None:
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


def normalize_cli_aliases(args: argparse.Namespace) -> None:
    if getattr(args, "list_runs", None) and not getattr(args, "runs_list", None):
        args.runs_list = args.list_runs
    if getattr(args, "best_from", None) and not getattr(args, "runs_best", None):
        args.runs_best = args.best_from


def apply_json_request_overlay(
    args: argparse.Namespace,
    session_metadata: dict[str, object],
    *,
    validate_contract: Callable[[str, object], None] = validate_json_request_contract,
) -> str | None:
    json_command: str | None = None
    if not args.json_request:
        return json_command

    try:
        req = json.loads(args.json_request)

        schema_version = req.get("schema_version")
        if schema_version != "1.0":
            raise ConfigError(
                f"Unsupported or missing schema_version '{schema_version}'. Expected '1.0'."
            )

        json_command = req.get("command")
        if not json_command:
            raise ConfigError("Missing 'command' in JSON request.")

        args._request_id = req.get("request_id")
        session_metadata["request_id"] = args._request_id

        params = req.get("params", {})
        validate_contract(json_command, params)
        for key, value in params.items():
            if hasattr(args, key):
                setattr(args, key, value)

        if json_command == "sweep":
            args.sweep = params.get("config_path") or params.get("sweep")
            if "out_dir" in params:
                args.sweep_outdir = params["out_dir"]
            elif "sweep_outdir" in params:
                args.sweep_outdir = params["sweep_outdir"]
        elif json_command == "forward" and "run_dir" in params:
            args.forward_eval = params["run_dir"]

    except (json.JSONDecodeError, TypeError) as exc:
        raise ConfigError(f"Invalid --json-request payload: {exc}")

    return json_command


def determine_session_mode(args: argparse.Namespace, json_command: str | None) -> str:
    if json_command:
        return json_command
    if args.sweep:
        return "sweep"
    if args.forward_eval or args.resume_forward:
        return "forward"
    if args.portfolio_report or args.portfolio_compare:
        return "portfolio"
    if args.paper:
        return "paper"
    if args.report:
        return "report"
    if (
        args.paper_sessions_list
        or args.paper_sessions_show
        or args.paper_sessions_health
        or args.paper_sessions_alerts
        or args.paper_sessions_index
    ):
        return "paper_sessions"
    if (
        args.hyperliquid_preflight_outdir
        or args.hyperliquid_account_readiness_outdir
        or args.hyperliquid_signed_action_outdir
        or args.hyperliquid_submit_signed_action
        or args.hyperliquid_submit_session
        or args.kraken_preflight_outdir
        or args.kraken_auth_preflight_outdir
        or args.kraken_account_readiness_outdir
    ):
        return "broker_preflight"
    if (
        args.hyperliquid_submit_sessions_list
        or args.hyperliquid_submit_sessions_show
        or args.hyperliquid_submit_sessions_index
        or args.hyperliquid_submit_sessions_supervise
        or args.hyperliquid_submit_sessions_status
        or args.hyperliquid_submit_sessions_reconcile
        or args.hyperliquid_submit_sessions_fills
        or args.hyperliquid_submit_sessions_cancel
        or args.hyperliquid_submit_sessions_health
        or args.hyperliquid_submit_sessions_alerts
    ):
        return "hyperliquid_submit"
    if args.pretrade_handoff_validate or args.pretrade_handoff_validation_outdir:
        return "pretrade_handoff"
    if (
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
        return "broker_validate"
    if (
        args.kraken_dry_run_outdir
        or args.kraken_dry_run_session
        or args.broker_dry_runs_list
        or args.broker_dry_runs_show
        or args.broker_dry_runs_index
    ):
        return "broker_dry_run"
    if args.runs_list or args.runs_show or args.runs_best:
        return "runs"
    return "run"


def dispatch_json_request_command(
    args: argparse.Namespace,
    json_command: str | None,
    *,
    handle_run_command,
    handle_sweep_command,
    handle_forward_commands,
    handle_portfolio_commands,
    run_sweep,
    write_portfolio_report,
    write_mode_comparison_report,
):
    if not json_command:
        return None
    if json_command == "run":
        return handle_run_command(args)
    if json_command == "sweep":
        return handle_sweep_command(args, run_sweep=run_sweep)
    if json_command == "forward":
        return handle_forward_commands(args)
    if json_command == "portfolio":
        return handle_portfolio_commands(
            args,
            write_portfolio_report=write_portfolio_report,
            write_mode_comparison_report=write_mode_comparison_report,
        )
    raise ConfigError(
        f"Unknown command '{json_command}'. "
        "Valid commands: run, sweep, forward, portfolio."
    )


def dispatch_standard_commands(
    args: argparse.Namespace,
    initial_result: object = None,
    *,
    handle_broker_preflight_commands,
    handle_broker_dry_run_commands,
    handle_broker_dry_runs_commands,
    handle_broker_order_validations_commands,
    handle_hyperliquid_submit_sessions_commands,
    handle_pretrade_handoff_commands,
    handle_paper_session_commands,
    handle_runs_commands,
    handle_report_commands,
    handle_forward_commands,
    handle_portfolio_commands,
    handle_sweep_command,
    handle_run_command,
    write_run_report,
    write_advanced_report,
    write_runs_index,
    build_runs_index,
    write_comparison,
    write_portfolio_report,
    write_mode_comparison_report,
    run_sweep,
):
    result_ctx = initial_result

    if result_ctx in (None, False):
        result_ctx = handle_broker_preflight_commands(args)
    if result_ctx in (None, False):
        result_ctx = handle_broker_dry_run_commands(args)
    if result_ctx in (None, False):
        result_ctx = handle_broker_dry_runs_commands(args)
    if result_ctx in (None, False):
        result_ctx = handle_broker_order_validations_commands(args)
    if result_ctx in (None, False):
        result_ctx = handle_hyperliquid_submit_sessions_commands(args)
    if result_ctx in (None, False):
        result_ctx = handle_pretrade_handoff_commands(args)
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
        result_ctx = handle_sweep_command(args, run_sweep=run_sweep)
    if result_ctx in (None, False):
        result_ctx = handle_run_command(args)
    return result_ctx
