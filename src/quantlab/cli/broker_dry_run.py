"""
CLI handler for local broker dry-run artifact generation.

This surface intentionally remains small in Stage D.1 and only materializes
local audit artifacts for the Kraken dry-run adapter.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.brokers import ExecutionIntent, ExecutionPolicy, KrakenBrokerAdapter
from quantlab.errors import ConfigError


def handle_broker_dry_run_commands(args) -> dict[str, object] | bool:
    """
    Handle broker dry-run CLI commands.

    Commands:
    - ``--kraken-dry-run-outdir <DIR>`` : build and persist a local Kraken dry-run audit
    """
    if not getattr(args, "kraken_dry_run_outdir", None):
        return False

    outdir = Path(args.kraken_dry_run_outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    intent = _build_execution_intent_from_args(args)
    policy = _build_execution_policy_from_args(args)

    adapter = KrakenBrokerAdapter()
    audit = adapter.build_dry_run_audit(intent, policy).to_dict()

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
