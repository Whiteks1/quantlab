"""
paper_sessions.py - CLI handler for paper session inspection commands.

Responsibilities:
- list paper sessions in a root directory
- show details for a single paper session
- summarize health across paper sessions
- surface operator-facing alert signals for paper sessions
- refresh a shared paper-session index surface

This module intentionally keeps paper-session inspection separate from the
research-oriented runs navigation surface.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterator

from quantlab.errors import ConfigError
from quantlab.runs.artifacts import (
    CANONICAL_REPORT_FILENAME,
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
    load_json_with_fallback,
)

DEFAULT_PAPER_STALE_MINUTES = 60


def handle_paper_session_commands(args) -> bool:
    """
    Handle paper-session inspection CLI commands.

    Commands:
    - ``--paper-sessions-list <dir>`` : list all paper sessions in a directory
    - ``--paper-sessions-show <dir>`` : show details for a single paper session
    - ``--paper-sessions-health <dir>`` : summarize paper-session health
    - ``--paper-sessions-alerts <dir>`` : emit a machine-readable alert snapshot
    - ``--paper-sessions-index <dir>`` : refresh shared index artifacts for paper sessions

    Returns True if a paper-session command was handled; False otherwise.
    """
    if getattr(args, "paper_sessions_list", None):
        root_dir = _require_directory(args.paper_sessions_list, "Paper sessions root")

        sessions = [load_paper_session_summary(path) for path in scan_paper_sessions(root_dir)]

        print(f"\nPaper sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid paper session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "paper_sessions_show", None):
        session_dir = _require_directory(args.paper_sessions_show, "Paper session directory")

        summary = load_paper_session_summary(session_dir)

        print(f"\nPaper session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:20s}: {val}")
        return True

    if getattr(args, "paper_sessions_health", None):
        root_dir = _require_directory(args.paper_sessions_health, "Paper sessions root")
        health = build_paper_sessions_health(root_dir)

        print(f"\nPaper session health: {root_dir}\n")
        print(f"  total_sessions      : {health['total_sessions']}")
        print(f"  success             : {health['status_counts'].get('success', 0)}")
        print(f"  failed              : {health['status_counts'].get('failed', 0)}")
        print(f"  aborted             : {health['status_counts'].get('aborted', 0)}")
        print(f"  running             : {health['status_counts'].get('running', 0)}")
        print(f"  latest_session_id   : {health.get('latest_session_id')}")
        print(f"  latest_session_at   : {health.get('latest_session_at')}")
        print(f"  latest_session_state: {health.get('latest_session_status')}")
        print(f"  latest_issue_id     : {health.get('latest_issue_session_id')}")
        print(f"  latest_issue_state  : {health.get('latest_issue_status')}")
        print(f"  latest_issue_at     : {health.get('latest_issue_at')}")
        print(f"  latest_issue_error  : {health.get('latest_issue_error_type')}")
        return True

    if getattr(args, "paper_sessions_alerts", None):
        root_dir = _require_directory(args.paper_sessions_alerts, "Paper sessions root")
        alerts = build_paper_sessions_alerts(
            root_dir,
            stale_after_minutes=getattr(args, "paper_stale_minutes", DEFAULT_PAPER_STALE_MINUTES),
        )
        print(json.dumps(alerts, indent=2, sort_keys=True))
        return True

    if getattr(args, "paper_sessions_index", None):
        from quantlab.reporting.paper_session_index import write_paper_sessions_index

        root_dir = _require_directory(args.paper_sessions_index, "Paper sessions root")
        csv_path, json_path = write_paper_sessions_index(root_dir)
        print("\nPaper session index refreshed:\n")
        print(f"  csv_path : {csv_path}")
        print(f"  json_path: {json_path}")
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


def build_paper_sessions_health(root_dir: str | Path) -> dict[str, Any]:
    """
    Build a compact operator-facing health summary for paper sessions.
    """
    root = _require_directory(root_dir, "Paper sessions root")
    sessions = [load_paper_session_summary(path) for path in scan_paper_sessions(root)]

    status_counts = Counter((session.get("status") or "unknown") for session in sessions)
    latest_session = _latest_by_activity(sessions)
    latest_issue = _latest_by_activity(
        [
            session
            for session in sessions
            if (session.get("status") or "").lower() in {"failed", "aborted", "running"}
        ]
    )

    return {
        "root_dir": str(root),
        "total_sessions": len(sessions),
        "status_counts": dict(status_counts),
        "latest_session_id": latest_session.get("session_id") if latest_session else None,
        "latest_session_status": latest_session.get("status") if latest_session else None,
        "latest_session_at": _activity_at(latest_session) if latest_session else None,
        "latest_issue_session_id": latest_issue.get("session_id") if latest_issue else None,
        "latest_issue_status": latest_issue.get("status") if latest_issue else None,
        "latest_issue_at": _activity_at(latest_issue) if latest_issue else None,
        "latest_issue_error_type": latest_issue.get("error_type") if latest_issue else None,
    }


def build_paper_sessions_alerts(
    root_dir: str | Path,
    *,
    stale_after_minutes: int = DEFAULT_PAPER_STALE_MINUTES,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Build a deterministic alert snapshot for paper-session operations.
    """
    if stale_after_minutes <= 0:
        raise ConfigError("paper_stale_minutes must be a positive integer.")

    root = _require_directory(root_dir, "Paper sessions root")
    sessions = [load_paper_session_summary(path) for path in scan_paper_sessions(root)]
    generated_at = now or datetime.now()
    alerts: list[dict[str, Any]] = []

    for session in sessions:
        status = (session.get("status") or "unknown").lower()
        activity_at = _parse_session_activity(session)
        age_minutes = _session_age_minutes(activity_at, generated_at)

        if status == "failed":
            alerts.append(
                _build_alert_entry(
                    code="PAPER_SESSION_FAILED",
                    severity="critical",
                    session=session,
                    activity_at=activity_at,
                    age_minutes=age_minutes,
                    message=session.get("message") or "Paper session failed.",
                )
            )
        elif status == "aborted":
            alerts.append(
                _build_alert_entry(
                    code="PAPER_SESSION_ABORTED",
                    severity="warning",
                    session=session,
                    activity_at=activity_at,
                    age_minutes=age_minutes,
                    message=session.get("message") or "Paper session aborted.",
                )
            )
        elif status == "running" and age_minutes is not None and age_minutes >= stale_after_minutes:
            alerts.append(
                _build_alert_entry(
                    code="PAPER_SESSION_STALE",
                    severity="warning",
                    session=session,
                    activity_at=activity_at,
                    age_minutes=age_minutes,
                    message=(
                        f"Paper session has been running for {age_minutes} minute(s), "
                        f"exceeding stale threshold of {stale_after_minutes} minute(s)."
                    ),
                )
            )

    latest_success = _latest_by_activity(
        [
            session
            for session in sessions
            if (session.get("status") or "").lower() == "success"
        ]
    )
    latest_alert = max(alerts, key=_alert_sort_key) if alerts else None
    alert_counts = Counter(alert["severity"] for alert in alerts)

    if alert_counts.get("critical", 0):
        alert_status = "critical"
    elif alerts:
        alert_status = "warning"
    else:
        alert_status = "ok"

    return {
        "root_dir": str(root),
        "generated_at": generated_at.replace(microsecond=0).isoformat(),
        "stale_after_minutes": stale_after_minutes,
        "total_sessions": len(sessions),
        "status_counts": dict(Counter((session.get("status") or "unknown") for session in sessions)),
        "running_sessions": [
            session["session_id"]
            for session in sessions
            if (session.get("status") or "").lower() == "running"
        ],
        "alert_status": alert_status,
        "has_alerts": bool(alerts),
        "alert_counts": dict(alert_counts),
        "latest_success_session_id": latest_success.get("session_id") if latest_success else None,
        "latest_success_at": _activity_at(latest_success) if latest_success else None,
        "latest_alert_session_id": latest_alert.get("session_id") if latest_alert else None,
        "latest_alert_code": latest_alert.get("alert_code") if latest_alert else None,
        "latest_alert_at": latest_alert.get("activity_at") if latest_alert else None,
        "alerts": alerts,
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


def _require_directory(path_str: str | Path, label: str) -> Path:
    path = Path(path_str)
    if not path.is_dir():
        raise ConfigError(f"{label} does not exist or is not a directory: {path}")
    return path


def _activity_at(session: dict[str, Any] | None) -> str | None:
    if not session:
        return None
    return session.get("updated_at") or session.get("created_at")


def _latest_by_activity(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not sessions:
        return None
    return max(sessions, key=_session_activity_sort_key)


def _session_activity_sort_key(session: dict[str, Any]) -> datetime:
    value = _activity_at(session)
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.min


def _parse_session_activity(session: dict[str, Any]) -> datetime | None:
    value = _activity_at(session)
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _session_age_minutes(activity_at: datetime | None, now: datetime) -> int | None:
    if activity_at is None:
        return None
    delta = now - activity_at
    return max(0, int(delta.total_seconds() // 60))


def _build_alert_entry(
    *,
    code: str,
    severity: str,
    session: dict[str, Any],
    activity_at: datetime | None,
    age_minutes: int | None,
    message: str,
) -> dict[str, Any]:
    return {
        "alert_code": code,
        "severity": severity,
        "session_id": session.get("session_id"),
        "status": session.get("status"),
        "activity_at": activity_at.replace(microsecond=0).isoformat() if activity_at else _activity_at(session),
        "age_minutes": age_minutes,
        "error_type": session.get("error_type"),
        "message": message,
        "path": session.get("path"),
    }


def _alert_sort_key(alert: dict[str, Any]) -> datetime:
    value = alert.get("activity_at")
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.min
