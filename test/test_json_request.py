"""
test_json_request.py — Tests for headless CLI stability (Issue #21).

Covers:
- schema_version validation
- request_id propagation
- explicit command validation for --json-request
- rejection of missing or unknown commands
- param overlay for JSON-driven execution
"""
from __future__ import annotations

import types

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> types.SimpleNamespace:
    """Minimal argparse-like namespace for unit-testing the JSON overlay logic."""
    defaults = dict(
        json_request=None,
        ticker="ETH-USD",
        start="2023-01-01",
        end="2023-12-31",
        interval="1d",
        fee=0.002,
        rsi_buy_max=60.0,
        rsi_sell_min=75.0,
        cooldown_days=0,
        slippage_bps=8.0,
        slippage_mode="fixed",
        k_atr=0.05,
        outdir=None,
        save_price_plot=False,
        paper=False,
        initial_cash=1000.0,
        report=None,
        trades_csv=None,
        sweep=None,
        sweep_outdir=None,
        runs_list=None,
        runs_show=None,
        runs_best=None,
        metric="sharpe_simple",
        list_runs=None,
        best_from=None,
        compare=None,
        advanced_report=None,
        forward_eval=None,
        forward_start=None,
        forward_end=None,
        forward_outdir=None,
        forward_metric="sharpe_simple",
        resume_forward=None,
        portfolio_report=None,
        portfolio_mode="raw_capital",
        portfolio_weights=None,
        portfolio_top_n=None,
        portfolio_rank_metric="total_return",
        portfolio_min_return=None,
        portfolio_max_drawdown=None,
        portfolio_include_tickers=None,
        portfolio_exclude_tickers=None,
        portfolio_include_strategies=None,
        portfolio_exclude_strategies=None,
        portfolio_latest_per_source_run=False,
        portfolio_compare=None,
    )
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _apply_json_overlay(req_dict: dict, args=None):
    """
    Reproduce the current JSON overlay validation logic from main.py.
    Returns (args, json_command).
    Raises SystemExit(2) on invalid input.
    """
    if args is None:
        args = _make_args()

    req = req_dict

    # 1) Validate schema version
    schema_version = req.get("schema_version")
    if schema_version != "1.0":
        raise SystemExit(2)

    # 2) Require command
    json_command = req.get("command")
    if not json_command:
        raise SystemExit(2)

    # 3) Reject unknown commands
    valid_commands = {"run", "sweep", "forward", "portfolio"}
    if json_command not in valid_commands:
        raise SystemExit(2)

    # 4) Propagate request_id
    args._request_id = req.get("request_id")

    # 5) Map params
    params = req.get("params", {})
    if json_command == "sweep":
        config_path = params.get("config_path") or params.get("sweep")
        if not isinstance(config_path, str) or not config_path:
            raise SystemExit(2)
    for k, v in params.items():
        if hasattr(args, k):
            setattr(args, k, v)

    # 6) Explicit param routing for nested/non-obvious flags
    if json_command == "sweep":
        args.sweep = params.get("config_path") or params.get("sweep")
        if "out_dir" in params:
            args.sweep_outdir = params["out_dir"]
        elif "sweep_outdir" in params:
            args.sweep_outdir = params["sweep_outdir"]
    elif json_command == "forward" and "run_dir" in params:
        args.forward_eval = params["run_dir"]

    return args, json_command


# ---------------------------------------------------------------------------
# Tests: Validation
# ---------------------------------------------------------------------------

class TestJsonValidation:
    def test_valid_schema_and_command_passes(self):
        req = {"schema_version": "1.0", "command": "run", "params": {}}
        args, cmd = _apply_json_overlay(req)
        assert cmd == "run"

    def test_missing_schema_version_exits_2(self):
        req = {"command": "run", "params": {}}
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2

    def test_unsupported_schema_version_exits_2(self):
        req = {"schema_version": "2.0", "command": "run", "params": {}}
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2

    def test_missing_command_exits_2(self):
        req = {"schema_version": "1.0", "params": {}}
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2

    def test_empty_command_exits_2(self):
        req = {"schema_version": "1.0", "command": "", "params": {}}
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2

    def test_unknown_command_exits_2(self):
        req = {"schema_version": "1.0", "command": "unknown", "params": {}}
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Tests: request_id propagation
# ---------------------------------------------------------------------------

class TestRequestIdPropagation:
    def test_request_id_stored_on_args(self):
        req = {
            "schema_version": "1.0",
            "request_id": "req_abc123",
            "command": "run",
            "params": {},
        }
        args, _ = _apply_json_overlay(req)
        assert args._request_id == "req_abc123"

    def test_missing_request_id_is_none(self):
        req = {"schema_version": "1.0", "command": "run", "params": {}}
        args, _ = _apply_json_overlay(req)
        assert args._request_id is None


# ---------------------------------------------------------------------------
# Tests: param overlay
# ---------------------------------------------------------------------------

class TestParamOverlay:
    def test_ticker_is_mapped(self):
        req = {
            "schema_version": "1.0",
            "command": "run",
            "params": {"ticker": "BTC-USD"},
        }
        args, _ = _apply_json_overlay(req)
        assert args.ticker == "BTC-USD"

    def test_sweep_config_path_routed(self):
        req = {
            "schema_version": "1.0",
            "command": "sweep",
            "params": {"config_path": "sweep.yaml"},
        }
        args, cmd = _apply_json_overlay(req)
        assert cmd == "sweep"
        assert args.sweep == "sweep.yaml"

    def test_forward_run_dir_routed(self):
        req = {
            "schema_version": "1.0",
            "command": "forward",
            "params": {"run_dir": "outputs/runs/run_001"},
        }
        args, cmd = _apply_json_overlay(req)
        assert cmd == "forward"
        assert args.forward_eval == "outputs/runs/run_001"

    def test_sweep_missing_config_path_exits_2(self):
        req = {
            "schema_version": "1.0",
            "command": "sweep",
            "params": {},
        }
        with pytest.raises(SystemExit) as exc_info:
            _apply_json_overlay(req)
        assert exc_info.value.code == 2

    def test_sweep_out_dir_routed(self):
        req = {
            "schema_version": "1.0",
            "command": "sweep",
            "params": {"config_path": "sweep.yaml", "out_dir": "outputs/stepbit"},
        }
        args, _ = _apply_json_overlay(req)
        assert args.sweep == "sweep.yaml"
        assert args.sweep_outdir == "outputs/stepbit"
