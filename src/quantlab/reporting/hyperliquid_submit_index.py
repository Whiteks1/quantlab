"""
Shared registry/export surface for Hyperliquid submit sessions.
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
from typing import Any

HYPERLIQUID_SUBMITS_INDEX_JSON_FILENAME = "hyperliquid_submits_index.json"
HYPERLIQUID_SUBMITS_INDEX_CSV_FILENAME = "hyperliquid_submits_index.csv"
HYPERLIQUID_SUBMITS_INDEX_MD_FILENAME = "hyperliquid_submits_index.md"

_INDEX_FIELDS = [
    "session_id",
    "status",
    "created_at",
    "updated_at",
    "request_id",
    "source_signer_id",
    "submit_state",
    "cancel_state",
    "cancel_accepted",
    "remote_submit_called",
    "submitted",
    "response_type",
    "order_status_known",
    "latest_order_state",
    "reconciliation_known",
    "latest_reconciliation_state",
    "reconciliation_close_state",
    "reconciliation_fill_state",
    "reconciliation_fill_count",
    "reconciliation_filled_size",
    "fill_summary_state",
    "fill_summary_count",
    "fill_summary_filled_size",
    "fill_summary_total_fee",
    "fill_summary_total_closed_pnl",
    "supervision_state",
    "supervision_attention_required",
    "supervision_poll_count",
    "supervision_monitoring_mode",
    "alert_status",
    "alert_counts",
    "alerts_present",
    "latest_alert_session_id",
    "latest_alert_code",
    "latest_alert_at",
    "effective_order_state",
    "path",
]


def build_hyperliquid_submits_index(root_dir: str | Path) -> dict[str, Any]:
    from quantlab.cli.hyperliquid_submit_sessions import (
        load_hyperliquid_submit_summary,
        scan_hyperliquid_submit_sessions,
    )

    root = Path(root_dir)
    sessions: list[dict[str, Any]] = []
    for session_dir in scan_hyperliquid_submit_sessions(root):
        summary = load_hyperliquid_submit_summary(session_dir)
        sessions.append({field: summary.get(field) for field in _INDEX_FIELDS})

    status_counts: dict[str, int] = {}
    submit_state_counts: dict[str, int] = {}
    alert_status_counts: dict[str, int] = {}
    for session in sessions:
        status_key = str(session.get("status") or "unknown")
        submit_state_key = str(session.get("submit_state") or "no_submit_response")
        alert_status_key = str(session.get("alert_status") or "unknown")
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        submit_state_counts[submit_state_key] = submit_state_counts.get(submit_state_key, 0) + 1
        alert_status_counts[alert_status_key] = alert_status_counts.get(alert_status_key, 0) + 1

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "root_dir": str(root),
        "n_sessions": len(sessions),
        "status_counts": status_counts,
        "submit_state_counts": submit_state_counts,
        "alert_status_counts": alert_status_counts,
        "reconciliation_required_sessions": status_counts.get("reconciliation_required", 0),
        "identifier_missing_sessions": submit_state_counts.get("submitted_remote_identifier_missing", 0),
        "sessions": sessions,
    }


def render_hyperliquid_submits_index_md(payload: dict[str, Any]) -> str:
    sessions = payload.get("sessions", [])
    lines = [
        "# Hyperliquid Submits Index",
        "",
        "## Summary",
        "",
        f"- **Root directory:** `{payload.get('root_dir')}`",
        f"- **Generated at:** {payload.get('generated_at')}",
        f"- **Total sessions found:** {payload.get('n_sessions', len(sessions))}",
        f"- **Reconciliation required sessions:** {payload.get('reconciliation_required_sessions', 0)}",
        f"- **Identifier-missing submit acknowledgements:** {payload.get('identifier_missing_sessions', 0)}",
        "",
        "## Sessions",
        "",
    ]

    if not sessions:
        lines.append("_No valid Hyperliquid submit sessions found._")
        return "\n".join(lines)

    columns = [
        "session_id",
        "status",
        "submit_state",
        "alert_status",
        "latest_alert_code",
        "effective_order_state",
        "path",
    ]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in sessions:
        values = []
        for column in columns:
            value = row.get(column)
            if value is None:
                values.append("")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_hyperliquid_submits_index(root_dir: str | Path) -> tuple[str, str, str]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_hyperliquid_submits_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / HYPERLIQUID_SUBMITS_INDEX_CSV_FILENAME
    json_path = root / HYPERLIQUID_SUBMITS_INDEX_JSON_FILENAME
    md_path = root / HYPERLIQUID_SUBMITS_INDEX_MD_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_hyperliquid_submits_index_md(payload))

    return str(csv_path), str(json_path), str(md_path)
