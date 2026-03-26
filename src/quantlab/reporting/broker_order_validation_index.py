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


def write_broker_order_validations_index(root_dir: str | Path) -> tuple[str, str]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_broker_order_validations_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / BROKER_ORDER_VALIDATIONS_INDEX_CSV_FILENAME
    json_path = root / BROKER_ORDER_VALIDATIONS_INDEX_JSON_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return str(csv_path), str(json_path)
