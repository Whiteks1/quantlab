"""
paper_session_index.py - shared registry/export surface for paper sessions.

Builds a deterministic paper-session index under a paper root, analogous in
spirit to the run registry but intentionally separate from `runs_index.*`.
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
from typing import Any

PAPER_SESSIONS_INDEX_JSON_FILENAME = "paper_sessions_index.json"
PAPER_SESSIONS_INDEX_CSV_FILENAME = "paper_sessions_index.csv"

_INDEX_FIELDS = [
    "session_id",
    "status",
    "created_at",
    "updated_at",
    "request_id",
    "error_type",
    "report_contract_type",
    "path",
]


def build_paper_sessions_index(root_dir: str | Path) -> dict[str, Any]:
    """
    Build a deterministic index payload for all valid paper sessions in *root_dir*.
    """
    from quantlab.cli.paper_sessions import load_paper_session_summary, scan_paper_sessions

    root = Path(root_dir)
    sessions: list[dict[str, Any]] = []
    for session_dir in scan_paper_sessions(root):
        summary = load_paper_session_summary(session_dir)
        sessions.append({field: summary.get(field) for field in _INDEX_FIELDS})

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "root_dir": str(root),
        "n_sessions": len(sessions),
        "sessions": sessions,
    }


def write_paper_sessions_index(root_dir: str | Path) -> tuple[str, str]:
    """
    Write `paper_sessions_index.csv` and `paper_sessions_index.json` into *root_dir*.
    """
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_paper_sessions_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / PAPER_SESSIONS_INDEX_CSV_FILENAME
    json_path = root / PAPER_SESSIONS_INDEX_JSON_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return str(csv_path), str(json_path)
