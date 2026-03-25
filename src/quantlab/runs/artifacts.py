from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

CANONICAL_METADATA_FILENAME = "metadata.json"
CANONICAL_CONFIG_FILENAME = "config.json"
CANONICAL_METRICS_FILENAME = "metrics.json"
CANONICAL_REPORT_FILENAME = "report.json"
PAPER_SESSION_METADATA_FILENAME = "session_metadata.json"
PAPER_SESSION_STATUS_FILENAME = "session_status.json"

LEGACY_METADATA_FILENAMES = ("meta.json",)
LEGACY_REPORT_FILENAMES = ("run_report.json",)

CONFIG_RESOLVED_YAML_FILENAME = "config_resolved.yaml"


def _candidate_paths(run_dir: str | Path, filenames: Iterable[str]) -> list[Path]:
    root = Path(run_dir)
    return [root / name for name in filenames]


def first_existing_path(run_dir: str | Path, *filenames: str) -> Optional[Path]:
    for path in _candidate_paths(run_dir, filenames):
        if path.exists():
            return path
    return None


def load_json_with_fallback(run_dir: str | Path, *filenames: str) -> tuple[dict[str, Any], Optional[Path]]:
    path = first_existing_path(run_dir, *filenames)
    if path is None:
        return {}, None

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data, path


def canonical_run_artifact_paths(run_dir: str | Path) -> dict[str, str]:
    root = Path(run_dir)
    return {
        "metadata_path": str(root / CANONICAL_METADATA_FILENAME),
        "config_path": str(root / CANONICAL_CONFIG_FILENAME),
        "metrics_path": str(root / CANONICAL_METRICS_FILENAME),
        "report_path": str(root / CANONICAL_REPORT_FILENAME),
    }


def canonical_run_artifact_names() -> dict[str, str]:
    return {
        "metadata": CANONICAL_METADATA_FILENAME,
        "config": CANONICAL_CONFIG_FILENAME,
        "metrics": CANONICAL_METRICS_FILENAME,
        "report": CANONICAL_REPORT_FILENAME,
    }


def canonical_paper_artifact_names() -> dict[str, str]:
    return {
        "metadata": PAPER_SESSION_METADATA_FILENAME,
        "status": PAPER_SESSION_STATUS_FILENAME,
        "config": CANONICAL_CONFIG_FILENAME,
        "metrics": CANONICAL_METRICS_FILENAME,
        "report": CANONICAL_REPORT_FILENAME,
        "trades": "trades.csv",
    }
