"""
CLI handler for broker order-validation session inspection.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers.session_store import (
    BROKER_ORDER_APPROVAL_FILENAME,
    BROKER_PRE_SUBMIT_BUNDLE_FILENAME,
    BROKER_SUBMIT_GATE_FILENAME,
    BROKER_ORDER_VALIDATE_FILENAME,
    BROKER_ORDER_VALIDATE_METADATA_FILENAME,
    BROKER_ORDER_VALIDATE_STATUS_FILENAME,
    BrokerOrderValidationStore,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_broker_order_validations_commands(args) -> bool:
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
        "path": str(path),
        "metadata_path": str(path / BROKER_ORDER_VALIDATE_METADATA_FILENAME),
        "status_path": str(path / BROKER_ORDER_VALIDATE_STATUS_FILENAME),
        "report_path": str(path / BROKER_ORDER_VALIDATE_FILENAME),
        "approval_path": str(path / BROKER_ORDER_APPROVAL_FILENAME),
        "pre_submit_bundle_path": str(path / BROKER_PRE_SUBMIT_BUNDLE_FILENAME),
        "submit_gate_path": str(path / BROKER_SUBMIT_GATE_FILENAME),
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
