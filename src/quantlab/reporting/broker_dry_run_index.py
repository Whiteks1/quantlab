"""
Shared registry/export surface for broker dry-run sessions.
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
from typing import Any

BROKER_DRY_RUNS_INDEX_JSON_FILENAME = "broker_dry_runs_index.json"
BROKER_DRY_RUNS_INDEX_CSV_FILENAME = "broker_dry_runs_index.csv"

_INDEX_FIELDS = [
    "session_id",
    "adapter_name",
    "status",
    "created_at",
    "updated_at",
    "request_id",
    "preflight_allowed",
    "preflight_reasons",
    "path",
]


def build_broker_dry_runs_index(root_dir: str | Path) -> dict[str, Any]:
    from quantlab.cli.broker_dry_runs import load_broker_dry_run_summary, scan_broker_dry_runs

    root = Path(root_dir)
    sessions: list[dict[str, Any]] = []
    for session_dir in scan_broker_dry_runs(root):
        summary = load_broker_dry_run_summary(session_dir)
        sessions.append({field: summary.get(field) for field in _INDEX_FIELDS})

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "root_dir": str(root),
        "n_sessions": len(sessions),
        "sessions": sessions,
    }


def write_broker_dry_runs_index(root_dir: str | Path) -> tuple[str, str]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_broker_dry_runs_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / BROKER_DRY_RUNS_INDEX_CSV_FILENAME
    json_path = root / BROKER_DRY_RUNS_INDEX_JSON_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return str(csv_path), str(json_path)
