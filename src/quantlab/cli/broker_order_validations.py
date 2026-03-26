"""
CLI handler for broker order-validation session inspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers.session_store import (
    BROKER_ORDER_VALIDATE_FILENAME,
    BROKER_ORDER_VALIDATE_METADATA_FILENAME,
    BROKER_ORDER_VALIDATE_STATUS_FILENAME,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_broker_order_validations_commands(args) -> bool:
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
        "path": str(path),
        "metadata_path": str(path / BROKER_ORDER_VALIDATE_METADATA_FILENAME),
        "status_path": str(path / BROKER_ORDER_VALIDATE_STATUS_FILENAME),
        "report_path": str(path / BROKER_ORDER_VALIDATE_FILENAME),
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
