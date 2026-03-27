"""
Compatibility bootstrap for the QuantLab CLI.

This file intentionally stays small:
- preserve the long-lived `python main.py ...` contract
- preserve monkeypatch-friendly globals used by legacy tests
- delegate real CLI behavior to the packaged app in `quantlab.app`
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if SRC_ROOT.exists():
    src_root_str = str(SRC_ROOT)
    if src_root_str not in sys.path:
        sys.path.insert(0, src_root_str)

import quantlab.app as _app

_SYNC_NAMES = [
    "fetch_ohlc",
    "handle_sweep_command",
    "handle_portfolio_commands",
    "handle_forward_commands",
    "handle_report_commands",
    "handle_run_command",
    "handle_runs_commands",
    "handle_paper_session_commands",
    "handle_broker_preflight_commands",
    "handle_broker_dry_run_commands",
    "handle_broker_dry_runs_commands",
    "handle_broker_order_validations_commands",
    "handle_hyperliquid_submit_sessions_commands",
    "handle_pretrade_handoff_commands",
    "run_sweep",
    "write_run_report",
    "write_advanced_report",
    "write_runs_index",
    "build_runs_index",
    "write_comparison",
    "write_portfolio_report",
    "write_mode_comparison_report",
]


def _sync_from_app() -> None:
    for name in _SYNC_NAMES:
        globals()[name] = getattr(_app, name)


def _sync_to_app() -> None:
    for name in _SYNC_NAMES:
        setattr(_app, name, globals()[name])


_sync_from_app()

SignalEmitter = _app.SignalEmitter
_validate_json_request_contract = _app._validate_json_request_contract
_emit_version = _app._emit_version
_emit_health_check = _app._emit_health_check
_refresh_runs_index_if_needed = _app._refresh_runs_index_if_needed
_load_runtime_dependencies = _app._load_runtime_dependencies


def main() -> None:
    _sync_to_app()
    try:
        _app.main()
    finally:
        _sync_from_app()


if __name__ == "__main__":
    main()
