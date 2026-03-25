"""
CLI handler for broker dry-run session inspection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers.session_store import (
    BROKER_DRY_RUN_AUDIT_FILENAME,
    BROKER_DRY_RUN_METADATA_FILENAME,
    BROKER_DRY_RUN_STATUS_FILENAME,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_broker_dry_runs_commands(args) -> bool:
    if getattr(args, "broker_dry_runs_list", None):
        root_dir = _require_directory(args.broker_dry_runs_list, "Broker dry-runs root")
        sessions = [load_broker_dry_run_summary(path) for path in scan_broker_dry_runs(root_dir)]

        print(f"\nBroker dry-run sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid broker dry-run session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "broker_dry_runs_show", None):
        session_dir = _require_directory(args.broker_dry_runs_show, "Broker dry-run session directory")
        summary = load_broker_dry_run_summary(session_dir)

        print(f"\nBroker dry-run session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:20s}: {val}")
        return True

    if getattr(args, "broker_dry_runs_index", None):
        from quantlab.reporting.broker_dry_run_index import write_broker_dry_runs_index

        root_dir = _require_directory(args.broker_dry_runs_index, "Broker dry-runs root")
        csv_path, json_path = write_broker_dry_runs_index(root_dir)
        print("\nBroker dry-run index refreshed:\n")
        print(f"  csv_path : {csv_path}")
        print(f"  json_path: {json_path}")
        return True

    return False


def scan_broker_dry_runs(root_dir: str | Path) -> Iterator[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        return

    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_broker_dry_run_dir(child):
            yield child


def load_broker_dry_run_summary(session_dir: str | Path) -> dict[str, Any]:
    path = Path(session_dir)
    if not path.is_dir():
        raise ConfigError(f"Broker dry-run session directory does not exist or is not a directory: {path}")
    if not _is_valid_broker_dry_run_dir(path):
        raise ConfigError(f"Not a valid broker dry-run session directory: {path}")

    metadata, _ = load_json_with_fallback(path, BROKER_DRY_RUN_METADATA_FILENAME)
    status, _ = load_json_with_fallback(path, BROKER_DRY_RUN_STATUS_FILENAME)
    audit, audit_path = load_json_with_fallback(path, BROKER_DRY_RUN_AUDIT_FILENAME)

    return {
        "session_id": metadata.get("session_id") or status.get("session_id") or path.name,
        "adapter_name": metadata.get("adapter_name") or audit.get("adapter_name"),
        "status": status.get("status") or metadata.get("status"),
        "created_at": metadata.get("created_at"),
        "updated_at": status.get("updated_at"),
        "request_id": metadata.get("request_id") or audit.get("intent", {}).get("request_id"),
        "preflight_allowed": audit.get("preflight", {}).get("allowed"),
        "preflight_reasons": audit.get("preflight", {}).get("reasons"),
        "artifact_type": audit.get("artifact_type"),
        "audit_present": bool(audit_path),
        "path": str(path),
        "metadata_path": str(path / BROKER_DRY_RUN_METADATA_FILENAME),
        "status_path": str(path / BROKER_DRY_RUN_STATUS_FILENAME),
        "audit_path": str(path / BROKER_DRY_RUN_AUDIT_FILENAME),
    }


def _is_valid_broker_dry_run_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            BROKER_DRY_RUN_METADATA_FILENAME,
            BROKER_DRY_RUN_STATUS_FILENAME,
            BROKER_DRY_RUN_AUDIT_FILENAME,
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
