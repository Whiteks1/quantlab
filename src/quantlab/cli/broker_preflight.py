"""
CLI handler for read-only broker preflight probes.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.brokers import KrakenBrokerAdapter
from quantlab.cli.broker_dry_run import (
    _build_execution_intent_from_args,
    _build_execution_policy_from_args,
)
from quantlab.errors import ConfigError


def handle_broker_preflight_commands(args) -> dict[str, object] | bool:
    """
    Handle broker preflight CLI commands.

    Commands:
    - ``--kraken-preflight-outdir <DIR>`` : run read-only Kraken readiness probes and persist artifact
    - ``--kraken-auth-preflight-outdir <DIR>`` : run authenticated Kraken read-only preflight and persist artifact
    - ``--kraken-account-readiness-outdir <DIR>`` : run authenticated account snapshot and intent readiness check
    - ``--kraken-order-validate-outdir <DIR>`` : run validate-only Kraken order probe and persist artifact
    """
    if getattr(args, "kraken_preflight_outdir", None):
        symbol = getattr(args, "broker_symbol", None) or getattr(args, "ticker", None)
        if not isinstance(symbol, str) or not symbol.strip():
            raise ConfigError("broker_symbol or ticker must be provided for Kraken preflight.")

        outdir = Path(args.kraken_preflight_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        adapter = KrakenBrokerAdapter()
        report = adapter.build_public_preflight_report(
            symbol,
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        artifact_path = outdir / "broker_preflight.json"
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        print("\nKraken preflight generated:\n")
        print(f"  artifact_path        : {artifact_path}")
        print(f"  public_api_reachable : {report['public_api_reachable']}")
        print(f"  pair_supported       : {report['pair_supported']}")

        return {
            "status": "success",
            "mode": "broker_preflight",
            "adapter_name": report["adapter_name"],
            "artifact_path": str(artifact_path),
            "pair_supported": report["pair_supported"],
            "public_api_reachable": report["public_api_reachable"],
        }

    if getattr(args, "kraken_auth_preflight_outdir", None):
        outdir = Path(args.kraken_auth_preflight_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        adapter = KrakenBrokerAdapter()
        report = adapter.build_authenticated_preflight_report(
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        artifact_path = outdir / "broker_auth_preflight.json"
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        print("\nKraken auth preflight generated:\n")
        print(f"  artifact_path       : {artifact_path}")
        print(f"  credentials_present : {report['credentials_present']}")
        print(f"  authenticated       : {report['authenticated']}")

        return {
            "status": "success",
            "mode": "broker_auth_preflight",
            "adapter_name": report["adapter_name"],
            "artifact_path": str(artifact_path),
            "credentials_present": report["credentials_present"],
            "authenticated": report["authenticated"],
        }

    if getattr(args, "kraken_account_readiness_outdir", None):
        intent = _build_execution_intent_from_args(args)
        policy = _build_execution_policy_from_args(args)

        outdir = Path(args.kraken_account_readiness_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        adapter = KrakenBrokerAdapter()
        report = adapter.build_account_snapshot_report(
            intent,
            policy,
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        artifact_path = outdir / "broker_account_snapshot.json"
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        readiness = report["intent_readiness"]
        print("\nKraken account readiness generated:\n")
        print(f"  artifact_path         : {artifact_path}")
        print(f"  authenticated         : {report['authenticated_preflight']['authenticated']}")
        print(f"  account_snapshot_ok   : {report['account_snapshot_available']}")
        print(f"  readiness_allowed     : {readiness['allowed']}")

        return {
            "status": "success",
            "mode": "broker_account_readiness",
            "adapter_name": report["adapter_name"],
            "artifact_path": str(artifact_path),
            "authenticated": report["authenticated_preflight"]["authenticated"],
            "account_snapshot_available": report["account_snapshot_available"],
            "readiness_allowed": readiness["allowed"],
        }

    if getattr(args, "kraken_order_validate_outdir", None):
        intent = _build_execution_intent_from_args(args)
        policy = _build_execution_policy_from_args(args)

        outdir = Path(args.kraken_order_validate_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        adapter = KrakenBrokerAdapter()
        report = adapter.build_order_validate_report(
            intent,
            policy,
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        artifact_path = outdir / "broker_order_validate.json"
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        print("\nKraken order validate generated:\n")
        print(f"  artifact_path           : {artifact_path}")
        print(f"  remote_validation_called: {report['remote_validation_called']}")
        print(f"  validation_accepted     : {report['validation_accepted']}")

        return {
            "status": "success",
            "mode": "broker_order_validate",
            "adapter_name": report["adapter_name"],
            "artifact_path": str(artifact_path),
            "remote_validation_called": report["remote_validation_called"],
            "validation_accepted": report["validation_accepted"],
        }

    return False
