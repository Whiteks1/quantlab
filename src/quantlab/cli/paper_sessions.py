"""
paper_sessions.py - CLI handler for paper session inspection commands.

Responsibilities:
- list paper sessions in a root directory
- show details for a single paper session

This module intentionally keeps paper-session inspection separate from the
research-oriented runs navigation surface.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from quantlab.errors import ConfigError
from quantlab.runs.artifacts import (
    CANONICAL_REPORT_FILENAME,
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
    load_json_with_fallback,
)


def handle_paper_session_commands(args) -> bool:
    """
    Handle paper-session inspection CLI commands.

    Commands:
    - ``--paper-sessions-list <dir>`` : list all paper sessions in a directory
    - ``--paper-sessions-show <dir>`` : show details for a single paper session

    Returns True if a paper-session command was handled; False otherwise.
    """
    if getattr(args, "paper_sessions_list", None):
        root_dir = Path(args.paper_sessions_list)
        if not root_dir.is_dir():
            raise ConfigError(f"Paper sessions root does not exist or is not a directory: {root_dir}")

        sessions = [load_paper_session_summary(path) for path in scan_paper_sessions(root_dir)]

        print(f"\nPaper sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid paper session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "paper_sessions_show", None):
        session_dir = Path(args.paper_sessions_show)
        if not session_dir.is_dir():
            raise ConfigError(f"Paper session directory does not exist or is not a directory: {session_dir}")

        summary = load_paper_session_summary(session_dir)

        print(f"\nPaper session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:20s}: {val}")
        return True

    return False


def scan_paper_sessions(root_dir: str | Path) -> Iterator[Path]:
    """
    Yield valid paper-session subdirectories inside *root_dir*.
    """
    root = Path(root_dir)
    if not root.is_dir():
        return

    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_paper_session_dir(child):
            yield child


def load_paper_session_summary(session_dir: str | Path) -> dict[str, Any]:
    """
    Load a normalized summary for a paper session directory.
    """
    path = Path(session_dir)
    if not path.is_dir():
        raise ConfigError(f"Paper session directory does not exist or is not a directory: {path}")
    if not _is_valid_paper_session_dir(path):
        raise ConfigError(f"Not a valid paper session directory: {path}")

    metadata, _ = load_json_with_fallback(path, PAPER_SESSION_METADATA_FILENAME)
    status, _ = load_json_with_fallback(path, PAPER_SESSION_STATUS_FILENAME)
    report, report_path = load_json_with_fallback(path, CANONICAL_REPORT_FILENAME)

    session_id = (
        metadata.get("session_id")
        or status.get("session_id")
        or report.get("header", {}).get("run_id")
        or path.name
    )
    report_contract = report.get("machine_contract", {}).get("contract_type")

    artifacts = {
        "session_metadata_path": str(path / PAPER_SESSION_METADATA_FILENAME),
        "session_status_path": str(path / PAPER_SESSION_STATUS_FILENAME),
        "report_path": str(path / CANONICAL_REPORT_FILENAME),
        "trades_path": str(path / "trades.csv"),
        "run_report_path": str(path / "run_report.md"),
        "artifacts_dir": str(path / "artifacts"),
    }

    return {
        "session_id": session_id,
        "status": status.get("status") or metadata.get("status") or report.get("status"),
        "created_at": metadata.get("created_at"),
        "updated_at": status.get("updated_at"),
        "request_id": metadata.get("request_id") or status.get("request_id"),
        "command": metadata.get("command") or "paper",
        "mode": metadata.get("mode") or report.get("header", {}).get("mode") or "paper",
        "error_type": status.get("error_type"),
        "message": status.get("message"),
        "report_contract_type": report_contract,
        "report_present": bool(report_path),
        "path": str(path),
        **artifacts,
    }


def _is_valid_paper_session_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            PAPER_SESSION_METADATA_FILENAME,
            PAPER_SESSION_STATUS_FILENAME,
            CANONICAL_REPORT_FILENAME,
        )
    )


def _print_sessions_table(sessions: list[dict[str, Any]]) -> None:
    fields = ["session_id", "status", "created_at", "request_id"]
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
