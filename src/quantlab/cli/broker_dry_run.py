"""
CLI handler for local broker dry-run artifact generation.

This surface intentionally remains small in Stage D.1 and only materializes
local audit artifacts for the Kraken dry-run adapter.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from quantlab.brokers import ExecutionIntent, ExecutionPolicy, KrakenBrokerAdapter
from quantlab.brokers.session_store import BrokerDryRunStore
from quantlab.errors import ConfigError
from quantlab.reporting.broker_dry_run_index import write_broker_dry_runs_index
from quantlab.runs.run_id import generate_run_id


def handle_broker_dry_run_commands(args) -> dict[str, object] | bool:
    """
    Handle broker dry-run CLI commands.

    Commands:
    - ``--kraken-dry-run-outdir <DIR>`` : build and persist a local Kraken dry-run audit
    - ``--kraken-dry-run-session`` : build and persist a canonical broker dry-run session
    """
    if not getattr(args, "kraken_dry_run_outdir", None) and not getattr(args, "kraken_dry_run_session", False):
        return False

    intent = _build_execution_intent_from_args(args)
    policy = _build_execution_policy_from_args(args)

    adapter = KrakenBrokerAdapter()
    audit = adapter.build_dry_run_audit(intent, policy).to_dict()
    request_id = getattr(args, "_request_id", None)

    if getattr(args, "kraken_dry_run_session", False):
        session_id = generate_run_id(
            "broker_dry_run",
            {
                "broker_target": intent.broker_target,
                "symbol": intent.symbol,
                "side": intent.side,
                "quantity": intent.quantity,
                "notional": intent.notional,
                "request_id": request_id,
            },
        )
        root_dir = Path(getattr(args, "broker_dry_runs_root", None) or "outputs/broker_dry_runs").resolve()
        store = BrokerDryRunStore(session_id, base_dir=str(root_dir))
        session_path = store.initialize().resolve()

        metadata = {
            "session_id": session_id,
            "adapter_name": adapter.adapter_name,
            "status": "success" if audit["preflight"]["allowed"] else "rejected",
            "created_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "request_id": request_id,
        }
        status = {
            "session_id": session_id,
            "status": metadata["status"],
            "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "preflight_allowed": audit["preflight"]["allowed"],
            "preflight_reasons": audit["preflight"]["reasons"],
        }
        if audit["preflight"]["reasons"]:
            status["message"] = ", ".join(audit["preflight"]["reasons"])

        store.write_metadata(metadata)
        store.write_status(status)
        store.write_audit(audit)
        csv_path, json_path = write_broker_dry_runs_index(root_dir)

        print("\nKraken dry-run session generated:\n")
        print(f"  session_path  : {session_path}")
        print(f"  preflight_ok  : {audit['preflight']['allowed']}")
        print(f"  adapter_name  : {audit['adapter_name']}")
        print(f"  index_csv     : {csv_path}")
        print(f"  index_json    : {json_path}")

        return {
            "status": "success",
            "mode": "broker_dry_run",
            "adapter_name": audit["adapter_name"],
            "artifacts_path": str(session_path),
            "session_id": session_id,
            "preflight_allowed": audit["preflight"]["allowed"],
        }

    outdir = Path(args.kraken_dry_run_outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    artifact_path = outdir / "broker_dry_run.json"
    with open(artifact_path, "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2, ensure_ascii=False)

    print("\nKraken dry-run audit generated:\n")
    print(f"  artifact_path : {artifact_path}")
    print(f"  preflight_ok  : {audit['preflight']['allowed']}")
    print(f"  adapter_name  : {audit['adapter_name']}")

    return {
        "status": "success",
        "mode": "broker_dry_run",
        "adapter_name": audit["adapter_name"],
        "artifact_path": str(artifact_path),
        "preflight_allowed": audit["preflight"]["allowed"],
    }


def _build_execution_intent_from_args(args) -> ExecutionIntent:
    symbol = getattr(args, "broker_symbol", None) or getattr(args, "ticker", None)
    if not isinstance(symbol, str) or not symbol.strip():
        raise ConfigError("broker_symbol or ticker must be provided for Kraken dry-run.")
    symbol = symbol.strip().upper().replace("-", "/")

    quantity = getattr(args, "broker_quantity", None)
    notional = getattr(args, "broker_notional", None)
    side = getattr(args, "broker_side", None)
    account_id = getattr(args, "broker_account_id", None)

    if quantity is None:
        raise ConfigError("broker_quantity is required for Kraken dry-run.")
    if notional is None:
        raise ConfigError("broker_notional is required for Kraken dry-run.")
    if not isinstance(side, str) or not side.strip():
        raise ConfigError("broker_side is required for Kraken dry-run.")

    return ExecutionIntent(
        broker_target="kraken",
        symbol=symbol,
        side=side.strip().lower(),
        quantity=float(quantity),
        notional=float(notional),
        account_id=account_id,
        strategy_id=getattr(args, "broker_strategy_id", None),
        request_id=getattr(args, "_request_id", None),
        dry_run=True,
    )


def _build_execution_policy_from_args(args) -> ExecutionPolicy:
    allowed_symbols_raw = getattr(args, "broker_allowed_symbols", None)
    allowed_symbols = frozenset()
    if isinstance(allowed_symbols_raw, str) and allowed_symbols_raw.strip():
        allowed_symbols = frozenset(
            symbol.strip()
            for symbol in allowed_symbols_raw.split(",")
            if symbol.strip()
        )

    return ExecutionPolicy(
        kill_switch_active=bool(getattr(args, "broker_kill_switch", False)),
        max_notional_per_order=getattr(args, "broker_max_notional", None),
        allowed_symbols=allowed_symbols,
        require_account_id=not bool(getattr(args, "broker_allow_missing_account_id", False)),
    )
