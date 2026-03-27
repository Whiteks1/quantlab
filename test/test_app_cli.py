from __future__ import annotations

from quantlab import app


def test_normalize_cli_aliases_maps_legacy_flags():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--list-runs", "outputs/runs", "--best-from", "outputs/runs"])

    assert args.runs_list is None
    assert args.runs_best is None

    app._normalize_cli_aliases(args)

    assert args.runs_list == "outputs/runs"
    assert args.runs_best == "outputs/runs"


def test_apply_json_request_overlay_sets_request_id_and_sweep_fields():
    parser = app._build_argument_parser()
    args = parser.parse_args(
        [
            "--json-request",
            '{"schema_version":"1.0","request_id":"req_demo","command":"sweep","params":{"config_path":"configs/test.yaml","out_dir":"outputs/stepbit"}}',
        ]
    )
    session_metadata = {"mode": "unknown", "request_id": None}

    json_command = app._apply_json_request_overlay(args, session_metadata)

    assert json_command == "sweep"
    assert session_metadata["request_id"] == "req_demo"
    assert args._request_id == "req_demo"
    assert args.sweep == "configs/test.yaml"
    assert args.sweep_outdir == "outputs/stepbit"


def test_determine_session_mode_for_hyperliquid_submit_health():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--hyperliquid-submit-sessions-health", "outputs/hyperliquid_submits"])

    mode = app._determine_session_mode(args, json_command=None)

    assert mode == "hyperliquid_submit"


def test_determine_session_mode_for_hyperliquid_submit_reconcile():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--hyperliquid-submit-sessions-reconcile", "outputs/hyperliquid_submits/demo"])

    mode = app._determine_session_mode(args, json_command=None)

    assert mode == "hyperliquid_submit"


def test_determine_session_mode_for_hyperliquid_submit_fills():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--hyperliquid-submit-sessions-fills", "outputs/hyperliquid_submits/demo"])

    mode = app._determine_session_mode(args, json_command=None)

    assert mode == "hyperliquid_submit"


def test_determine_session_mode_for_hyperliquid_submit_cancel():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--hyperliquid-submit-sessions-cancel", "outputs/hyperliquid_submits/demo"])

    mode = app._determine_session_mode(args, json_command=None)

    assert mode == "hyperliquid_submit"


def test_determine_session_mode_prefers_json_command():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--paper"])

    mode = app._determine_session_mode(args, json_command="portfolio")

    assert mode == "portfolio"


def test_determine_session_mode_for_pretrade_handoff():
    parser = app._build_argument_parser()
    args = parser.parse_args(["--pretrade-handoff-validate", "outputs/pretrade/handoff.json"])

    mode = app._determine_session_mode(args, json_command=None)

    assert mode == "pretrade_handoff"
