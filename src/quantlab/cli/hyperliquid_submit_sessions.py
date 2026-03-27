"""
CLI handler for Hyperliquid submit session inspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers.session_store import (
    HYPERLIQUID_SIGNED_ACTION_FILENAME,
    HYPERLIQUID_SUBMIT_METADATA_FILENAME,
    HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
    HYPERLIQUID_SUBMIT_STATUS_FILENAME,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_hyperliquid_submit_sessions_commands(args) -> bool:
    if getattr(args, "hyperliquid_submit_sessions_list", None):
        root_dir = _require_directory(args.hyperliquid_submit_sessions_list, "Hyperliquid submit sessions root")
        sessions = [load_hyperliquid_submit_summary(path) for path in scan_hyperliquid_submit_sessions(root_dir)]

        print(f"\nHyperliquid submit sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid Hyperliquid submit session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "hyperliquid_submit_sessions_show", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_show,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        print(f"\nHyperliquid submit session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:24s}: {val}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_index", None):
        from quantlab.reporting.hyperliquid_submit_index import write_hyperliquid_submits_index

        root_dir = _require_directory(args.hyperliquid_submit_sessions_index, "Hyperliquid submit sessions root")
        csv_path, json_path = write_hyperliquid_submits_index(root_dir)
        print("\nHyperliquid submit index refreshed:\n")
        print(f"  csv_path : {csv_path}")
        print(f"  json_path: {json_path}")
        return True

    return False


def scan_hyperliquid_submit_sessions(root_dir: str | Path) -> Iterator[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        return

    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_hyperliquid_submit_dir(child):
            yield child


def load_hyperliquid_submit_summary(session_dir: str | Path) -> dict[str, Any]:
    path = Path(session_dir)
    if not path.is_dir():
        raise ConfigError(f"Hyperliquid submit session directory does not exist or is not a directory: {path}")
    if not _is_valid_hyperliquid_submit_dir(path):
        raise ConfigError(f"Not a valid Hyperliquid submit session directory: {path}")

    metadata, metadata_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_METADATA_FILENAME)
    status, status_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_STATUS_FILENAME)
    signed_action, signed_action_path = load_json_with_fallback(path, HYPERLIQUID_SIGNED_ACTION_FILENAME)
    submit_response, response_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)

    envelope = signed_action.get("signature_envelope", {}) if isinstance(signed_action, dict) else {}

    return {
        "session_id": metadata.get("session_id") or status.get("session_id") or path.name,
        "status": status.get("status") or metadata.get("status"),
        "created_at": metadata.get("created_at"),
        "updated_at": status.get("updated_at"),
        "request_id": metadata.get("request_id"),
        "source_artifact_path": metadata.get("source_artifact_path") or submit_response.get("source_artifact_path"),
        "source_signer_id": metadata.get("source_signer_id") or submit_response.get("source_signer_id") or envelope.get("signer_id"),
        "signature_state": envelope.get("signature_state"),
        "submit_state": submit_response.get("submit_state"),
        "remote_submit_called": submit_response.get("remote_submit_called"),
        "submitted": submit_response.get("submitted"),
        "response_type": submit_response.get("response_type"),
        "signed_action_present": bool(signed_action_path),
        "submit_response_present": bool(response_path),
        "path": str(path),
        "metadata_path": str(path / HYPERLIQUID_SUBMIT_METADATA_FILENAME) if metadata_path else None,
        "status_path": str(path / HYPERLIQUID_SUBMIT_STATUS_FILENAME) if status_path else None,
        "signed_action_path": str(path / HYPERLIQUID_SIGNED_ACTION_FILENAME) if signed_action_path else None,
        "submit_response_path": str(path / HYPERLIQUID_SUBMIT_RESPONSE_FILENAME) if response_path else None,
    }


def _is_valid_hyperliquid_submit_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            HYPERLIQUID_SUBMIT_METADATA_FILENAME,
            HYPERLIQUID_SUBMIT_STATUS_FILENAME,
            HYPERLIQUID_SIGNED_ACTION_FILENAME,
            HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
        )
    )


def _require_directory(path_str: str | Path, label: str) -> Path:
    path = Path(path_str)
    if not path.is_dir():
        raise ConfigError(f"{label} does not exist or is not a directory: {path}")
    return path


def _print_sessions_table(sessions: list[dict[str, Any]]) -> None:
    fields = ["session_id", "status", "submit_state", "created_at"]
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
