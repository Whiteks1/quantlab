"""
CLI handler for read-only broker preflight probes.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from quantlab.brokers import ExecutionContext, HyperliquidBrokerAdapter, KrakenBrokerAdapter
from quantlab.brokers.session_store import BrokerOrderValidationStore
from quantlab.cli.broker_dry_run import (
    _build_execution_intent_from_args,
    _build_execution_policy_from_args,
)
from quantlab.errors import ConfigError
from quantlab.reporting.broker_order_validation_index import write_broker_order_validations_index
from quantlab.runs.run_id import generate_run_id


def handle_broker_preflight_commands(args) -> dict[str, object] | bool:
    """
    Handle broker preflight CLI commands.

    Commands:
    - ``--hyperliquid-preflight-outdir <DIR>`` : run read-only Hyperliquid venue preflight and persist artifact
    - ``--kraken-preflight-outdir <DIR>`` : run read-only Kraken readiness probes and persist artifact
    - ``--kraken-auth-preflight-outdir <DIR>`` : run authenticated Kraken read-only preflight and persist artifact
    - ``--kraken-account-readiness-outdir <DIR>`` : run authenticated account snapshot and intent readiness check
    - ``--kraken-order-validate-outdir <DIR>`` : run validate-only Kraken order probe and persist artifact
    - ``--kraken-order-validate-session`` : persist a canonical broker order-validation session
    """
    if getattr(args, "hyperliquid_preflight_outdir", None):
        symbol = getattr(args, "broker_symbol", None) or getattr(args, "ticker", None)
        if not isinstance(symbol, str) or not symbol.strip():
            raise ConfigError("broker_symbol or ticker must be provided for Hyperliquid preflight.")

        outdir = Path(args.hyperliquid_preflight_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        adapter = HyperliquidBrokerAdapter()
        context = _build_execution_context_from_args(args)
        report = adapter.build_public_preflight_report(
            symbol,
            intent_account_id=getattr(args, "broker_account_id", None),
            context=context,
            timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
        ).to_dict()

        artifact_path = outdir / "broker_preflight.json"
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)

        print("\nHyperliquid preflight generated:\n")
        print(f"  artifact_path      : {artifact_path}")
        print(f"  market_supported   : {report['market_supported']}")
        print(f"  resolved_transport : {report['execution_context']['resolved_transport']}")

        return {
            "status": "success",
            "mode": "broker_preflight",
            "adapter_name": report["adapter_name"],
            "artifact_path": str(artifact_path),
            "market_supported": report["market_supported"],
            "resolved_transport": report["execution_context"]["resolved_transport"],
        }

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

    if getattr(args, "kraken_order_validate_outdir", None) or getattr(args, "kraken_order_validate_session", False):
        intent = _build_execution_intent_from_args(args)
        policy = _build_execution_policy_from_args(args)

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

        if getattr(args, "kraken_order_validate_session", False):
            request_id = getattr(args, "_request_id", None)
            session_id = generate_run_id(
                "broker_order_validate",
                {
                    "broker_target": intent.broker_target,
                    "symbol": intent.symbol,
                    "side": intent.side,
                    "quantity": intent.quantity,
                    "notional": intent.notional,
                    "request_id": request_id,
                },
            )
            root_dir = Path(
                getattr(args, "broker_order_validations_root", None) or "outputs/broker_order_validations"
            ).resolve()
            store = BrokerOrderValidationStore(session_id, base_dir=str(root_dir))
            session_path = store.initialize().resolve()

            status_value = _derive_order_validation_status(report)
            metadata = {
                "session_id": session_id,
                "adapter_name": report["adapter_name"],
                "status": status_value,
                "created_at": dt.datetime.now().replace(microsecond=0).isoformat(),
                "request_id": request_id,
            }
            status = {
                "session_id": session_id,
                "status": status_value,
                "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
                "remote_validation_called": report["remote_validation_called"],
                "validation_accepted": report["validation_accepted"],
                "validation_reasons": report["validation_reasons"],
            }
            if report["validation_reasons"]:
                status["message"] = ", ".join(report["validation_reasons"])

            store.write_metadata(metadata)
            store.write_status(status)
            store.write_report(report)
            csv_path, json_path = write_broker_order_validations_index(root_dir)

            print("\nKraken order validation session generated:\n")
            print(f"  session_path            : {session_path}")
            print(f"  validation_accepted     : {report['validation_accepted']}")
            print(f"  remote_validation_called: {report['remote_validation_called']}")
            print(f"  index_csv               : {csv_path}")
            print(f"  index_json              : {json_path}")

            return {
                "status": "success",
                "mode": "broker_order_validate",
                "adapter_name": report["adapter_name"],
                "artifacts_path": str(session_path),
                "session_id": session_id,
                "validation_accepted": report["validation_accepted"],
                "remote_validation_called": report["remote_validation_called"],
            }

        outdir = Path(args.kraken_order_validate_outdir)
        outdir.mkdir(parents=True, exist_ok=True)
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


def _build_execution_context_from_args(args) -> ExecutionContext | None:
    raw_signer_type = getattr(args, "execution_signer_type", None)
    raw_routing_target = getattr(args, "execution_routing_target", None)
    raw_transport_preference = getattr(args, "execution_transport_preference", None)
    execution_account_id = getattr(args, "execution_account_id", None)
    signer_id = getattr(args, "execution_signer_id", None)
    expires_after = getattr(args, "execution_expires_after", None)

    if not any(
        value is not None
        for value in (
            raw_signer_type,
            raw_routing_target,
            raw_transport_preference,
            execution_account_id,
            signer_id,
            expires_after,
        )
    ):
        return None

    return ExecutionContext(
        execution_account_id=execution_account_id,
        signer_id=signer_id,
        signer_type=raw_signer_type or "direct",
        routing_target=raw_routing_target or "account",
        transport_preference=raw_transport_preference or "either",
        expires_after=expires_after,
    )


def _derive_order_validation_status(report: dict[str, object]) -> str:
    if bool(report.get("validation_accepted")):
        return "validated"
    if not bool(report.get("remote_validation_called")):
        reasons = report.get("validation_reasons") or []
        if "private_auth_not_ready" in reasons:
            return "auth_not_ready"
        return "rejected_local"
    return "rejected_remote"
