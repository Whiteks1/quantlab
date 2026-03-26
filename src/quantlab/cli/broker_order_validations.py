"""
CLI handler for broker order-validation session inspection.
"""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers import KrakenBrokerAdapter
from quantlab.brokers.session_store import (
    BROKER_ORDER_APPROVAL_FILENAME,
    BROKER_ORDER_STATUS_FILENAME,
    BROKER_PRE_SUBMIT_BUNDLE_FILENAME,
    BROKER_SUBMIT_GATE_FILENAME,
    BROKER_SUBMIT_ATTEMPT_FILENAME,
    BROKER_SUBMIT_RESPONSE_FILENAME,
    BROKER_ORDER_VALIDATE_FILENAME,
    BROKER_ORDER_VALIDATE_METADATA_FILENAME,
    BROKER_ORDER_VALIDATE_STATUS_FILENAME,
    BrokerOrderValidationStore,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_broker_order_validations_commands(args) -> bool:
    if getattr(args, "broker_order_validations_health", None):
        root_dir = _require_directory(args.broker_order_validations_health, "Broker order validations root")
        health = build_broker_submission_health(root_dir)

        print(f"\nBroker submission health: {root_dir}\n")
        print(f"  total_sessions          : {health['total_sessions']}")
        print(f"  approved_sessions       : {health['approved_sessions']}")
        print(f"  submit_gate_sessions    : {health['submit_gate_sessions']}")
        print(f"  submit_response_sessions: {health['submit_response_sessions']}")
        print(f"  submitted_sessions      : {health['submitted_sessions']}")
        print(f"  order_status_known      : {health['order_status_known_sessions']}")
        print(f"  latest_submit_id        : {health.get('latest_submit_session_id')}")
        print(f"  latest_submit_state     : {health.get('latest_submit_state')}")
        print(f"  latest_order_state      : {health.get('latest_order_state')}")
        print(f"  latest_issue_id         : {health.get('latest_issue_session_id')}")
        print(f"  latest_issue_code       : {health.get('latest_issue_code')}")
        print(f"  latest_issue_at         : {health.get('latest_issue_at')}")
        return True

    if getattr(args, "broker_order_validations_alerts", None):
        root_dir = _require_directory(args.broker_order_validations_alerts, "Broker order validations root")
        alerts = build_broker_submission_alerts(root_dir)
        print(json.dumps(alerts, indent=2, sort_keys=True))
        return True

    if getattr(args, "broker_order_validations_status", None):
        session_dir = _require_directory(
            args.broker_order_validations_status,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if summary.get("adapter_name") != "kraken":
            raise ConfigError(f"Unsupported adapter for broker order status refresh: {summary.get('adapter_name')}")

        submit_response, submit_response_path = load_json_with_fallback(session_dir, BROKER_SUBMIT_RESPONSE_FILENAME)
        if not submit_response_path:
            raise ConfigError("Broker order validation session must have a broker submit response artifact before status refresh.")

        txid = submit_response.get("txid")
        if not isinstance(txid, list):
            txid = submit_response.get("reconciliation_matched_txid")

        adapter = KrakenBrokerAdapter()
        order_status = adapter.build_order_status_report(
            source_session_id=summary["session_id"],
            txid=txid if isinstance(txid, list) else None,
            userref=submit_response.get("userref"),
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        submit_response["latest_order_status"] = order_status
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_submit_response(submit_response)
        store.write_order_status(order_status)

        status = {
            "status": _derive_order_status_session_state(order_status),
            "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "remote_validation_called": summary.get("remote_validation_called"),
            "validation_accepted": summary.get("validation_accepted"),
            "validation_reasons": summary.get("validation_reasons"),
            "remote_submit_called": summary.get("submit_response_remote_called"),
            "submitted": summary.get("submit_response_submitted"),
            "txid": order_status.get("matched_txid"),
            "submit_errors": summary.get("submit_errors"),
            "order_status_known": order_status.get("status_known"),
            "order_status_state": order_status.get("normalized_state"),
        }
        if order_status.get("errors"):
            status["message"] = ", ".join(str(item) for item in order_status["errors"])
        elif order_status.get("matched_txid"):
            status["message"] = ", ".join(str(item) for item in order_status["matched_txid"])
        store.write_status(status)

        status_path = session_dir / BROKER_ORDER_STATUS_FILENAME
        print("\nBroker order status refreshed:\n")
        print(f"  session_path   : {session_dir}")
        print(f"  status_path    : {status_path}")
        print(f"  state          : {order_status['normalized_state']}")
        print(f"  status_known   : {order_status['status_known']}")
        return True

    if getattr(args, "broker_order_validations_reconcile", None):
        session_dir = _require_directory(
            args.broker_order_validations_reconcile,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if summary.get("adapter_name") != "kraken":
            raise ConfigError(f"Unsupported adapter for broker reconciliation: {summary.get('adapter_name')}")

        submit_response, submit_response_path = load_json_with_fallback(session_dir, BROKER_SUBMIT_RESPONSE_FILENAME)
        if not submit_response_path:
            raise ConfigError("Broker order validation session must have a broker submit response artifact before reconciliation.")

        adapter = KrakenBrokerAdapter()
        reconciliation = adapter.build_order_reconciliation_report(
            source_session_id=summary["session_id"],
            userref=submit_response.get("userref"),
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
        ).to_dict()

        submit_response["reconciliation"] = reconciliation
        submit_response["reconciliation_attempted"] = reconciliation["reconciliation_attempted"]
        submit_response["reconciled"] = reconciliation["matched"]
        submit_response["reconciliation_matched_txid"] = reconciliation["matched_txid"]
        submit_response["reconciliation_matched_sources"] = reconciliation["matched_sources"]
        submit_response["reconciliation_matched_statuses"] = reconciliation["matched_statuses"]
        submit_response["reconciliation_errors"] = reconciliation["errors"]
        if reconciliation["matched"]:
            submit_response["submitted"] = True
            submit_response["txid"] = reconciliation["matched_txid"]
            submit_response["submit_state"] = _derive_reconciled_submit_state(reconciliation)
        else:
            submit_response["submit_state"] = "reconciliation_not_found"

        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_submit_response(submit_response)
        status = {
            "status": submit_response.get("submit_state"),
            "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "remote_validation_called": summary.get("remote_validation_called"),
            "validation_accepted": summary.get("validation_accepted"),
            "validation_reasons": summary.get("validation_reasons"),
            "remote_submit_called": submit_response.get("remote_submit_called"),
            "submitted": submit_response.get("submitted"),
            "txid": submit_response.get("txid"),
            "submit_errors": submit_response.get("errors"),
            "reconciled": submit_response.get("reconciled"),
        }
        if reconciliation.get("errors"):
            status["message"] = ", ".join(str(item) for item in reconciliation["errors"])
        elif reconciliation.get("matched"):
            status["message"] = ", ".join(str(item) for item in reconciliation["matched_txid"])
        store.write_status(status)

        print("\nBroker submit reconciliation completed:\n")
        print(f"  session_path   : {session_dir}")
        print(f"  reconciled     : {reconciliation['matched']}")
        print(f"  matched_txid   : {', '.join(reconciliation['matched_txid']) if reconciliation['matched_txid'] else '-'}")
        print(f"  submit_state   : {submit_response['submit_state']}")
        return True

    if getattr(args, "broker_order_validations_submit_real", None):
        session_dir = _require_directory(
            args.broker_order_validations_submit_real,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if not summary.get("submit_gate_present"):
            raise ConfigError("Broker order validation session must have a supervised submit gate before a real broker submit.")
        if not bool(summary.get("validation_accepted")):
            raise ConfigError("Broker order validation session must have a successful validate-only result before a real broker submit.")
        if (session_dir / BROKER_SUBMIT_RESPONSE_FILENAME).exists():
            existing_response, _ = load_json_with_fallback(session_dir, BROKER_SUBMIT_RESPONSE_FILENAME)
            existing_state = str(existing_response.get("submit_state") or "")
            if existing_state in {"submit_auth_not_ready", "missing_validate_payload"} and not bool(existing_response.get("remote_submit_called")):
                pass
            else:
                raise ConfigError("Broker order validation session already has a broker submit response artifact. Reconcile or inspect it before any new submit attempt.")

        reviewer = getattr(args, "broker_submit_reviewer", None)
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ConfigError("broker_submit_reviewer is required to perform a real broker submit.")
        if not bool(getattr(args, "broker_submit_confirm", False)):
            raise ConfigError("broker_submit_confirm is required to perform a real broker submit.")
        if not bool(getattr(args, "broker_submit_live", False)):
            raise ConfigError("broker_submit_live is required to perform a real broker submit.")
        if summary.get("adapter_name") != "kraken":
            raise ConfigError(f"Unsupported adapter for supervised submit: {summary.get('adapter_name')}")

        report, _ = load_json_with_fallback(session_dir, BROKER_ORDER_VALIDATE_FILENAME)
        submit_gate, _ = load_json_with_fallback(session_dir, BROKER_SUBMIT_GATE_FILENAME)
        validate_payload = report.get("validate_payload")
        adapter = KrakenBrokerAdapter()
        pending_response = adapter.build_order_submit_report(
            source_session_id=summary["session_id"],
            validate_payload=validate_payload if isinstance(validate_payload, dict) else None,
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
            remote_submit=False,
        ).to_dict()
        submit_note = getattr(args, "broker_submit_note", None)
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        pending_response["submitted_by"] = reviewer.strip()
        pending_response["submit_note"] = submit_note.strip() if isinstance(submit_note, str) and submit_note.strip() else None
        pending_response["source_submit_gate"] = submit_gate
        if pending_response.get("submit_state") == "pending_remote_submit":
            store.write_submit_response(pending_response)

        submit_response = adapter.build_order_submit_report(
            source_session_id=summary["session_id"],
            validate_payload=validate_payload if isinstance(validate_payload, dict) else None,
            api_key=getattr(args, "kraken_api_key", None),
            api_secret=getattr(args, "kraken_api_secret", None),
            api_key_env=getattr(args, "kraken_api_key_env", "KRAKEN_API_KEY"),
            api_secret_env=getattr(args, "kraken_api_secret_env", "KRAKEN_API_SECRET"),
            timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
            remote_submit=True,
        ).to_dict()
        submit_response["submitted_by"] = reviewer.strip()
        submit_response["submit_note"] = submit_note.strip() if isinstance(submit_note, str) and submit_note.strip() else None
        submit_response["source_submit_gate"] = submit_gate
        submit_response.setdefault("reconciliation", None)
        submit_response.setdefault("reconciliation_attempted", False)
        submit_response.setdefault("reconciled", False)
        store.write_submit_response(submit_response)
        status = {
            "status": _derive_order_submit_status(submit_response),
            "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "remote_validation_called": summary.get("remote_validation_called"),
            "validation_accepted": summary.get("validation_accepted"),
            "validation_reasons": summary.get("validation_reasons"),
            "remote_submit_called": submit_response.get("remote_submit_called"),
            "submitted": submit_response.get("submitted"),
            "txid": submit_response.get("txid"),
            "submit_errors": submit_response.get("errors"),
        }
        if submit_response.get("errors"):
            status["message"] = ", ".join(str(item) for item in submit_response["errors"])
        store.write_status(status)

        response_path = session_dir / BROKER_SUBMIT_RESPONSE_FILENAME
        print("\nBroker supervised submit response generated:\n")
        print(f"  session_path         : {session_dir}")
        print(f"  response_path        : {response_path}")
        print(f"  submitted            : {submit_response['submitted']}")
        print(f"  remote_submit_called : {submit_response['remote_submit_called']}")
        print(f"  txid                 : {', '.join(submit_response['txid']) if submit_response['txid'] else '-'}")
        return True

    if getattr(args, "broker_order_validations_submit_stub", None):
        session_dir = _require_directory(
            args.broker_order_validations_submit_stub,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if not summary.get("submit_gate_present"):
            raise ConfigError("Broker order validation session must have a supervised submit gate before generating a submit stub.")

        report, _ = load_json_with_fallback(session_dir, BROKER_ORDER_VALIDATE_FILENAME)
        submit_gate, _ = load_json_with_fallback(session_dir, BROKER_SUBMIT_GATE_FILENAME)
        submit_payload = report.get("validate_payload")
        attempt = {
            "artifact_type": "quantlab.broker.submit_attempt",
            "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "source_session_id": summary["session_id"],
            "submit_mode": "stub",
            "would_submit": True,
            "submit_payload": submit_payload,
            "source_submit_gate": submit_gate,
        }
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_submit_attempt(attempt)

        attempt_path = session_dir / BROKER_SUBMIT_ATTEMPT_FILENAME
        print("\nBroker supervised submit stub generated:\n")
        print(f"  session_path : {session_dir}")
        print(f"  attempt_path : {attempt_path}")
        print("  submit_mode  : stub")
        return True

    if getattr(args, "broker_order_validations_submit_gate", None):
        session_dir = _require_directory(
            args.broker_order_validations_submit_gate,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if not summary.get("pre_submit_bundle_present"):
            raise ConfigError("Broker order validation session must have a pre-submit bundle before generating a supervised submit gate.")
        reviewer = getattr(args, "broker_submit_reviewer", None)
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ConfigError("broker_submit_reviewer is required to generate a supervised submit gate.")
        if not bool(getattr(args, "broker_submit_confirm", False)):
            raise ConfigError("broker_submit_confirm is required to generate a supervised submit gate.")

        bundle, _ = load_json_with_fallback(session_dir, BROKER_PRE_SUBMIT_BUNDLE_FILENAME)
        gate_note = getattr(args, "broker_submit_note", None)
        gate = {
            "artifact_type": "quantlab.broker.submit_gate",
            "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "source_session_id": summary["session_id"],
            "submit_state": "ready_for_supervised_submit_gate",
            "confirmed_by": reviewer.strip(),
            "confirmed_note": gate_note.strip() if isinstance(gate_note, str) and gate_note.strip() else None,
            "source_pre_submit_bundle": bundle,
        }
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_submit_gate(gate)

        gate_path = session_dir / BROKER_SUBMIT_GATE_FILENAME
        print("\nBroker supervised submit gate generated:\n")
        print(f"  session_path : {session_dir}")
        print(f"  gate_path    : {gate_path}")
        print(f"  confirmed_by : {gate['confirmed_by']}")
        return True

    if getattr(args, "broker_order_validations_bundle", None):
        session_dir = _require_directory(
            args.broker_order_validations_bundle,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        if summary.get("approval_status") != "approved":
            raise ConfigError("Broker order validation session must be approved before generating a pre-submit bundle.")

        metadata, _ = load_json_with_fallback(session_dir, BROKER_ORDER_VALIDATE_METADATA_FILENAME)
        status, _ = load_json_with_fallback(session_dir, BROKER_ORDER_VALIDATE_STATUS_FILENAME)
        report, _ = load_json_with_fallback(session_dir, BROKER_ORDER_VALIDATE_FILENAME)
        approval, _ = load_json_with_fallback(session_dir, BROKER_ORDER_APPROVAL_FILENAME)

        bundle = {
            "artifact_type": "quantlab.broker.pre_submit_bundle",
            "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "source_session_id": summary["session_id"],
            "adapter_name": summary.get("adapter_name"),
            "session_metadata": metadata,
            "session_status": status,
            "order_validation": report,
            "approval": approval,
            "bundle_state": "ready_for_supervised_submit",
        }
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_pre_submit_bundle(bundle)

        bundle_path = session_dir / BROKER_PRE_SUBMIT_BUNDLE_FILENAME
        print("\nBroker pre-submit bundle generated:\n")
        print(f"  session_path : {session_dir}")
        print(f"  bundle_path  : {bundle_path}")
        print(f"  session_id   : {summary['session_id']}")
        return True

    if getattr(args, "broker_order_validations_approve", None):
        session_dir = _require_directory(
            args.broker_order_validations_approve,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)
        reviewer = getattr(args, "broker_approval_reviewer", None)
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ConfigError("broker_approval_reviewer is required to approve a broker order validation session.")

        approval_note = getattr(args, "broker_approval_note", None)
        store = BrokerOrderValidationStore(summary["session_id"], base_dir=str(session_dir.parent))
        approval = {
            "session_id": summary["session_id"],
            "status": "approved",
            "reviewed_by": reviewer.strip(),
            "reviewed_at": dt.datetime.now().replace(microsecond=0).isoformat(),
            "note": approval_note.strip() if isinstance(approval_note, str) and approval_note.strip() else None,
            "validation_accepted": summary.get("validation_accepted"),
            "remote_validation_called": summary.get("remote_validation_called"),
        }
        store.write_approval(approval)

        print("\nBroker order validation approved:\n")
        print(f"  session_path : {session_dir}")
        print(f"  reviewed_by  : {approval['reviewed_by']}")
        print(f"  reviewed_at  : {approval['reviewed_at']}")
        return True

    if getattr(args, "broker_order_validations_list", None):
        root_dir = _require_directory(args.broker_order_validations_list, "Broker order validations root")
        sessions = [load_broker_order_validation_summary(path) for path in scan_broker_order_validations(root_dir)]

        print(f"\nBroker order validation sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid broker order-validation session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "broker_order_validations_show", None):
        session_dir = _require_directory(
            args.broker_order_validations_show,
            "Broker order validation session directory",
        )
        summary = load_broker_order_validation_summary(session_dir)

        print(f"\nBroker order validation session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:24s}: {val}")
        return True

    if getattr(args, "broker_order_validations_index", None):
        from quantlab.reporting.broker_order_validation_index import write_broker_order_validations_index

        root_dir = _require_directory(args.broker_order_validations_index, "Broker order validations root")
        csv_path, json_path = write_broker_order_validations_index(root_dir)
        print("\nBroker order validation index refreshed:\n")
        print(f"  csv_path : {csv_path}")
        print(f"  json_path: {json_path}")
        return True

    return False


def scan_broker_order_validations(root_dir: str | Path) -> Iterator[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        return

    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_broker_order_validation_dir(child):
            yield child


def load_broker_order_validation_summary(session_dir: str | Path) -> dict[str, Any]:
    path = Path(session_dir)
    if not path.is_dir():
        raise ConfigError(f"Broker order validation session directory does not exist or is not a directory: {path}")
    if not _is_valid_broker_order_validation_dir(path):
        raise ConfigError(f"Not a valid broker order validation session directory: {path}")

    metadata, _ = load_json_with_fallback(path, BROKER_ORDER_VALIDATE_METADATA_FILENAME)
    status, _ = load_json_with_fallback(path, BROKER_ORDER_VALIDATE_STATUS_FILENAME)
    report, report_path = load_json_with_fallback(path, BROKER_ORDER_VALIDATE_FILENAME)
    approval, approval_path = load_json_with_fallback(path, BROKER_ORDER_APPROVAL_FILENAME)
    bundle, bundle_path = load_json_with_fallback(path, BROKER_PRE_SUBMIT_BUNDLE_FILENAME)
    submit_gate, submit_gate_path = load_json_with_fallback(path, BROKER_SUBMIT_GATE_FILENAME)
    submit_attempt, submit_attempt_path = load_json_with_fallback(path, BROKER_SUBMIT_ATTEMPT_FILENAME)
    submit_response, submit_response_path = load_json_with_fallback(path, BROKER_SUBMIT_RESPONSE_FILENAME)
    order_status, order_status_path = load_json_with_fallback(path, BROKER_ORDER_STATUS_FILENAME)

    return {
        "session_id": metadata.get("session_id") or status.get("session_id") or path.name,
        "adapter_name": metadata.get("adapter_name") or report.get("adapter_name"),
        "status": status.get("status") or metadata.get("status"),
        "created_at": metadata.get("created_at"),
        "updated_at": status.get("updated_at"),
        "request_id": metadata.get("request_id") or report.get("intent", {}).get("request_id"),
        "remote_validation_called": report.get("remote_validation_called"),
        "validation_accepted": report.get("validation_accepted"),
        "validation_reasons": report.get("validation_reasons"),
        "artifact_type": report.get("artifact_type"),
        "report_present": bool(report_path),
        "approval_status": approval.get("status"),
        "approved_by": approval.get("reviewed_by"),
        "approved_at": approval.get("reviewed_at"),
        "approval_note": approval.get("note"),
        "approval_present": bool(approval_path),
        "pre_submit_bundle_present": bool(bundle_path),
        "pre_submit_bundle_state": bundle.get("bundle_state"),
        "submit_gate_present": bool(submit_gate_path),
        "submit_gate_state": submit_gate.get("submit_state"),
        "submit_gate_confirmed_by": submit_gate.get("confirmed_by"),
        "submit_attempt_present": bool(submit_attempt_path),
        "submit_attempt_mode": submit_attempt.get("submit_mode"),
        "submit_attempt_would_submit": submit_attempt.get("would_submit"),
        "submit_response_present": bool(submit_response_path),
        "submit_response_state": submit_response.get("submit_state"),
        "submit_response_generated_at": submit_response.get("generated_at"),
        "submit_response_submitted": submit_response.get("submitted"),
        "submit_response_txid": submit_response.get("txid"),
        "submit_response_remote_called": submit_response.get("remote_submit_called"),
        "submit_response_reconciled": submit_response.get("reconciled"),
        "submit_errors": submit_response.get("errors"),
        "order_status_present": bool(order_status_path),
        "order_status_generated_at": order_status.get("generated_at"),
        "order_status_known": order_status.get("status_known"),
        "order_status_state": order_status.get("normalized_state"),
        "order_status_query_mode": order_status.get("query_mode"),
        "order_status_txid": order_status.get("matched_txid"),
        "order_status_errors": order_status.get("errors"),
        "path": str(path),
        "metadata_path": str(path / BROKER_ORDER_VALIDATE_METADATA_FILENAME),
        "status_path": str(path / BROKER_ORDER_VALIDATE_STATUS_FILENAME),
        "report_path": str(path / BROKER_ORDER_VALIDATE_FILENAME),
        "approval_path": str(path / BROKER_ORDER_APPROVAL_FILENAME),
        "pre_submit_bundle_path": str(path / BROKER_PRE_SUBMIT_BUNDLE_FILENAME),
        "submit_gate_path": str(path / BROKER_SUBMIT_GATE_FILENAME),
        "submit_attempt_path": str(path / BROKER_SUBMIT_ATTEMPT_FILENAME),
        "submit_response_path": str(path / BROKER_SUBMIT_RESPONSE_FILENAME),
        "order_status_path": str(path / BROKER_ORDER_STATUS_FILENAME),
    }


def _is_valid_broker_order_validation_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            BROKER_ORDER_VALIDATE_METADATA_FILENAME,
            BROKER_ORDER_VALIDATE_STATUS_FILENAME,
            BROKER_ORDER_VALIDATE_FILENAME,
        )
    )


def _require_directory(path_str: str | Path, label: str) -> Path:
    path = Path(path_str)
    if not path.is_dir():
        raise ConfigError(f"{label} does not exist or is not a directory: {path}")
    return path


def _print_sessions_table(sessions: list[dict[str, Any]]) -> None:
    fields = ["session_id", "adapter_name", "status", "created_at"]
    widths = {
        field: max(len(field), max((len(str(row.get(field) or "")) for row in sessions), default=0))
        for field in fields
    }

    header = "  ".join(field.ljust(widths[field]) for field in fields)
    print(header)
    print("-" * len(header))

    for session in sessions:
        row = "  ".join(str(session.get(field) or "").ljust(widths[field]) for field in fields)
        print(row)
    print()


def build_broker_submission_health(root_dir: str | Path) -> dict[str, Any]:
    root = _require_directory(root_dir, "Broker order validations root")
    sessions = [load_broker_order_validation_summary(path) for path in scan_broker_order_validations(root)]
    alerts = _collect_broker_submission_alerts(sessions)
    latest_submit = _latest_by_activity(
        [session for session in sessions if session.get("submit_response_present")]
    )
    latest_issue = max(alerts, key=_broker_alert_sort_key) if alerts else None

    return {
        "root_dir": str(root),
        "total_sessions": len(sessions),
        "approved_sessions": sum(1 for session in sessions if session.get("approval_present")),
        "submit_gate_sessions": sum(1 for session in sessions if session.get("submit_gate_present")),
        "submit_response_sessions": sum(1 for session in sessions if session.get("submit_response_present")),
        "submitted_sessions": sum(1 for session in sessions if session.get("submit_response_submitted")),
        "order_status_known_sessions": sum(1 for session in sessions if session.get("order_status_known")),
        "status_counts": dict(Counter((session.get("status") or "unknown") for session in sessions)),
        "submit_state_counts": dict(
            Counter(
                (session.get("submit_response_state") or "no_submit_response")
                for session in sessions
            )
        ),
        "order_state_counts": dict(
            Counter(
                (session.get("order_status_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "latest_submit_session_id": latest_submit.get("session_id") if latest_submit else None,
        "latest_submit_state": latest_submit.get("submit_response_state") if latest_submit else None,
        "latest_order_state": latest_submit.get("order_status_state") if latest_submit else None,
        "latest_submit_at": _activity_at(latest_submit) if latest_submit else None,
        "latest_issue_session_id": latest_issue.get("session_id") if latest_issue else None,
        "latest_issue_code": latest_issue.get("alert_code") if latest_issue else None,
        "latest_issue_at": latest_issue.get("activity_at") if latest_issue else None,
    }


def build_broker_submission_alerts(root_dir: str | Path) -> dict[str, Any]:
    root = _require_directory(root_dir, "Broker order validations root")
    sessions = [load_broker_order_validation_summary(path) for path in scan_broker_order_validations(root)]
    alerts = _collect_broker_submission_alerts(sessions)
    latest_alert = max(alerts, key=_broker_alert_sort_key) if alerts else None
    alert_counts = Counter(alert["severity"] for alert in alerts)

    if alert_counts.get("critical", 0):
        alert_status = "critical"
    elif alerts:
        alert_status = "warning"
    else:
        alert_status = "ok"

    return {
        "root_dir": str(root),
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "total_sessions": len(sessions),
        "submit_response_sessions": sum(1 for session in sessions if session.get("submit_response_present")),
        "submitted_sessions": sum(1 for session in sessions if session.get("submit_response_submitted")),
        "order_state_counts": dict(
            Counter(
                (session.get("order_status_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "alert_status": alert_status,
        "has_alerts": bool(alerts),
        "alert_counts": dict(alert_counts),
        "latest_alert_session_id": latest_alert.get("session_id") if latest_alert else None,
        "latest_alert_code": latest_alert.get("alert_code") if latest_alert else None,
        "latest_alert_at": latest_alert.get("activity_at") if latest_alert else None,
        "alerts": alerts,
    }


def _collect_broker_submission_alerts(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for session in sessions:
        if not session.get("submit_response_present"):
            continue

        submitted = bool(session.get("submit_response_submitted"))
        submit_state = str(session.get("submit_response_state") or session.get("status") or "unknown")
        activity_at = _parse_activity_timestamp(session)

        if submitted:
            if not session.get("order_status_present"):
                alerts.append(
                    _build_broker_alert(
                        code="BROKER_ORDER_STATUS_MISSING",
                        severity="warning",
                        session=session,
                        activity_at=activity_at,
                        message="Submitted broker session has no persistent order-status artifact yet.",
                    )
                )
            elif not bool(session.get("order_status_known")):
                alerts.append(
                    _build_broker_alert(
                        code="BROKER_ORDER_STATUS_UNKNOWN",
                        severity="critical",
                        session=session,
                        activity_at=activity_at,
                        message=_join_reasons(session.get("order_status_errors")) or "Submitted broker session has no known remote order state yet.",
                    )
                )
            elif session.get("order_status_state") in {"canceled", "expired"}:
                normalized_state = str(session.get("order_status_state")).upper()
                alerts.append(
                    _build_broker_alert(
                        code=f"BROKER_ORDER_{normalized_state}",
                        severity="warning",
                        session=session,
                        activity_at=activity_at,
                        message=f"Submitted broker session reached remote order state '{session.get('order_status_state')}'.",
                    )
                )
            continue

        code_map = {
            "submit_auth_not_ready": "BROKER_SUBMIT_AUTH_NOT_READY",
            "submit_not_ready": "BROKER_SUBMIT_NOT_READY",
            "submit_rejected": "BROKER_SUBMIT_REJECTED",
            "reconciliation_not_found": "BROKER_SUBMIT_RECONCILIATION_UNKNOWN",
        }
        severity = "critical" if submit_state in {"submit_rejected", "reconciliation_not_found"} else "warning"
        alerts.append(
            _build_broker_alert(
                code=code_map.get(submit_state, "BROKER_SUBMIT_ATTENTION"),
                severity=severity,
                session=session,
                activity_at=activity_at,
                message=_join_reasons(session.get("submit_errors")) or f"Broker submit session is in state '{submit_state}'.",
            )
        )

    return alerts


def _build_broker_alert(
    *,
    code: str,
    severity: str,
    session: dict[str, Any],
    activity_at: dt.datetime | None,
    message: str,
) -> dict[str, Any]:
    return {
        "alert_code": code,
        "severity": severity,
        "session_id": session.get("session_id"),
        "adapter_name": session.get("adapter_name"),
        "status": session.get("status"),
        "submit_state": session.get("submit_response_state"),
        "order_status_state": session.get("order_status_state"),
        "activity_at": activity_at.replace(microsecond=0).isoformat() if activity_at else None,
        "path": session.get("path"),
        "message": message,
    }


def _join_reasons(values: Any) -> str | None:
    if not isinstance(values, list):
        return None
    parts = [str(value) for value in values if str(value).strip()]
    return ", ".join(parts) if parts else None


def _activity_at(session: dict[str, Any] | None) -> str | None:
    activity_at = _parse_activity_timestamp(session) if session else None
    return activity_at.replace(microsecond=0).isoformat() if activity_at else None


def _parse_activity_timestamp(session: dict[str, Any] | None) -> dt.datetime | None:
    if not session:
        return None

    for key in (
        "order_status_generated_at",
        "submit_response_generated_at",
        "updated_at",
        "approved_at",
        "created_at",
    ):
        value = session.get(key)
        if not value:
            continue
        try:
            return dt.datetime.fromisoformat(str(value))
        except ValueError:
            continue
    return None


def _latest_by_activity(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    dated = [(session, _parse_activity_timestamp(session)) for session in sessions]
    dated = [(session, stamp) for session, stamp in dated if stamp is not None]
    if not dated:
        return None
    dated.sort(key=lambda item: item[1])
    return dated[-1][0]


def _broker_alert_sort_key(alert: dict[str, Any]) -> tuple[dt.datetime, str]:
    activity_at = alert.get("activity_at")
    try:
        parsed = dt.datetime.fromisoformat(str(activity_at)) if activity_at else dt.datetime.min
    except ValueError:
        parsed = dt.datetime.min
    return parsed, str(alert.get("session_id") or "")


def _derive_order_submit_status(submit_response: dict[str, Any]) -> str:
    explicit_state = submit_response.get("submit_state")
    if isinstance(explicit_state, str) and explicit_state.strip():
        return explicit_state
    if bool(submit_response.get("submitted")):
        return "submitted_remote"
    if not bool(submit_response.get("remote_submit_called")):
        errors = submit_response.get("errors") or []
        if "private_auth_not_ready" in errors:
            return "submit_auth_not_ready"
        return "submit_not_ready"
    return "submit_rejected"


def _derive_reconciled_submit_state(reconciliation: dict[str, Any]) -> str:
    sources = reconciliation.get("matched_sources") or []
    if "closed" in sources:
        return "reconciled_closed"
    if "open" in sources:
        return "reconciled_open"
    return "reconciled_matched"


def _derive_order_status_session_state(order_status: dict[str, Any]) -> str:
    normalized_state = order_status.get("normalized_state")
    if isinstance(normalized_state, str) and normalized_state.strip():
        return f"order_{normalized_state}"
    if bool(order_status.get("status_known")):
        return "order_known"
    return "order_unknown"
