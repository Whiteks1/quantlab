"""
Shared registry/export surface for broker order-validation sessions.
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
from typing import Any

BROKER_ORDER_VALIDATIONS_INDEX_JSON_FILENAME = "broker_order_validations_index.json"
BROKER_ORDER_VALIDATIONS_INDEX_CSV_FILENAME = "broker_order_validations_index.csv"
BROKER_ORDER_VALIDATIONS_INDEX_MD_FILENAME = "broker_order_validations_index.md"

_INDEX_FIELDS = [
    "session_id",
    "adapter_name",
    "status",
    "created_at",
    "updated_at",
    "request_id",
    "remote_validation_called",
    "validation_accepted",
    "validation_reasons",
    "path",
]


def build_broker_order_validations_index(root_dir: str | Path) -> dict[str, Any]:
    from quantlab.cli.broker_order_validations import (
        load_broker_order_validation_summary,
        scan_broker_order_validations,
    )

    root = Path(root_dir)
    sessions: list[dict[str, Any]] = []
    for session_dir in scan_broker_order_validations(root):
        summary = load_broker_order_validation_summary(session_dir)
        sessions.append({field: summary.get(field) for field in _INDEX_FIELDS})

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "root_dir": str(root),
        "n_sessions": len(sessions),
        "sessions": sessions,
    }


def render_broker_order_validations_index_md(payload: dict[str, Any]) -> str:
    sessions = payload.get("sessions", [])
    lines = [
        "# Broker Order Validations Index",
        "",
        "## Summary",
        "",
        f"- **Root directory:** `{payload.get('root_dir')}`",
        f"- **Generated at:** {payload.get('generated_at')}",
        f"- **Total sessions found:** {payload.get('n_sessions', len(sessions))}",
        "",
        "## Sessions",
        "",
    ]

    if not sessions:
        lines.append("_No valid broker order validation sessions found._")
        return "\n".join(lines)

    columns = [
        "session_id",
        "adapter_name",
        "status",
        "validation_accepted",
        "remote_validation_called",
        "request_id",
        "path",
    ]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in sessions:
        values = []
        for column in columns:
            value = row.get(column)
            values.append("" if value is None else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_broker_order_validations_index(root_dir: str | Path) -> tuple[str, str, str]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_broker_order_validations_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / BROKER_ORDER_VALIDATIONS_INDEX_CSV_FILENAME
    json_path = root / BROKER_ORDER_VALIDATIONS_INDEX_JSON_FILENAME
    md_path = root / BROKER_ORDER_VALIDATIONS_INDEX_MD_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_broker_order_validations_index_md(payload))

    return str(csv_path), str(json_path), str(md_path)
