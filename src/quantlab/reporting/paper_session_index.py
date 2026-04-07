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
PAPER_SESSIONS_INDEX_MD_FILENAME = "paper_sessions_index.md"

_INDEX_FIELDS = [
    "session_id",
    "status",
    "created_at",
    "started_at",
    "updated_at",
    "finished_at",
    "terminal",
    "status_reason",
    "duration_seconds",
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


def render_paper_sessions_index_md(payload: dict[str, Any]) -> str:
    sessions = payload.get("sessions", [])
    lines = [
        "# Paper Sessions Index",
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
        lines.append("_No valid paper session directories found._")
        return "\n".join(lines)

    columns = [
        "session_id",
        "status",
        "created_at",
        "started_at",
        "updated_at",
        "finished_at",
        "terminal",
        "status_reason",
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


def write_paper_sessions_index(root_dir: str | Path) -> tuple[str, str, str]:
    """
    Write `paper_sessions_index.csv`, `paper_sessions_index.json`, and `paper_sessions_index.md` into *root_dir*.
    """
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_paper_sessions_index(root)
    sessions = payload.get("sessions", [])

    csv_path = root / PAPER_SESSIONS_INDEX_CSV_FILENAME
    json_path = root / PAPER_SESSIONS_INDEX_JSON_FILENAME
    md_path = root / PAPER_SESSIONS_INDEX_MD_FILENAME

    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_INDEX_FIELDS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_paper_sessions_index_md(payload))

    return str(csv_path), str(json_path), str(md_path)
