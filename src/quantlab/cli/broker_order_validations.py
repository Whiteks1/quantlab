"""
CLI handler for broker order-validation session inspection.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers import KrakenBrokerAdapter
from quantlab.brokers.session_store import (
    BROKER_ORDER_APPROVAL_FILENAME,
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
        "submit_response_submitted": submit_response.get("submitted"),
        "submit_response_txid": submit_response.get("txid"),
        "submit_response_remote_called": submit_response.get("remote_submit_called"),
        "submit_response_reconciled": submit_response.get("reconciled"),
        "path": str(path),
        "metadata_path": str(path / BROKER_ORDER_VALIDATE_METADATA_FILENAME),
        "status_path": str(path / BROKER_ORDER_VALIDATE_STATUS_FILENAME),
        "report_path": str(path / BROKER_ORDER_VALIDATE_FILENAME),
        "approval_path": str(path / BROKER_ORDER_APPROVAL_FILENAME),
        "pre_submit_bundle_path": str(path / BROKER_PRE_SUBMIT_BUNDLE_FILENAME),
        "submit_gate_path": str(path / BROKER_SUBMIT_GATE_FILENAME),
        "submit_attempt_path": str(path / BROKER_SUBMIT_ATTEMPT_FILENAME),
        "submit_response_path": str(path / BROKER_SUBMIT_RESPONSE_FILENAME),
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
