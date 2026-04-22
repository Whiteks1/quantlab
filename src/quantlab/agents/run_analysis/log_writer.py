"""Structured log writer for run_analysis extractive pilot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extractor import RunArtifacts

LOG_SCHEMA_VERSION = "quantlab.run_analysis.log.v1"


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compute_input_hash(run_id: str, artifacts: RunArtifacts) -> str:
    """Compute deterministic hash for the extracted run input contract."""
    canonical_input = {
        "run_id": run_id,
        "metadata": artifacts.metadata,
        "metrics": artifacts.metrics,
        "report": artifacts.report,
        "config": artifacts.config,
    }
    encoded = json.dumps(canonical_input, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return _hash_bytes(encoded)


def compute_output_hash(report_markdown: str) -> str:
    """Compute deterministic hash for emitted report content."""
    normalized = report_markdown.replace("\r\n", "\n")
    return _hash_bytes(normalized.encode("utf-8"))


def build_analysis_log(
    run_id: str,
    report_path: Path,
    log_path: Path,
    artifacts: RunArtifacts,
    report_markdown: str,
) -> dict[str, Any]:
    """Build minimal structured log payload for one analysis run."""
    return {
        "schema_version": LOG_SCHEMA_VERSION,
        "status": "ok",
        "mode": "extractive_pilot",
        "run_id": run_id,
        "run_path": str(artifacts.run_path),
        "files_written": [str(report_path), str(log_path)],
        "artifact_presence": {
            "metadata.json": True,
            "metrics.json": True,
            "report.json": True,
            "config.json": artifacts.config is not None,
        },
        "input_hash": compute_input_hash(run_id=run_id, artifacts=artifacts),
        "output_hash": compute_output_hash(report_markdown=report_markdown),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_analysis_log(log_path: Path, payload: dict[str, Any]) -> None:
    """Write JSON log without overwriting existing files."""
    with log_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
