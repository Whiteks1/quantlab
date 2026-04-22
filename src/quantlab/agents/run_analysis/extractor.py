"""Pure extractor for run_analysis artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import RunAnalysisError
from .validator import validate_run_input


@dataclass(frozen=True)
class RunArtifacts:
    """Stable internal structure for extracted run artifacts."""

    run_id: str
    run_path: Path
    metadata: dict[str, Any]
    metrics: dict[str, Any]
    report: dict[str, Any]
    config: dict[str, Any] | None


class InvalidRunArtifactJsonError(RunAnalysisError):
    """Raised when a run artifact file contains invalid JSON."""

    def __init__(self, artifact_name: str) -> None:
        super().__init__(f"Invalid JSON in '{artifact_name}'")


def _read_json(path: Path, artifact_name: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise InvalidRunArtifactJsonError(artifact_name) from exc

    if not isinstance(payload, dict):
        raise InvalidRunArtifactJsonError(artifact_name)
    return payload


def extract_run_artifacts(run_id: str, runs_root: str | Path) -> RunArtifacts:
    """Load required run artifacts and optional config artifact."""
    run_path = validate_run_input(run_id, runs_root)

    metadata = _read_json(run_path / "metadata.json", "metadata.json")
    metrics = _read_json(run_path / "metrics.json", "metrics.json")
    report = _read_json(run_path / "report.json", "report.json")

    config_path = run_path / "config.json"
    config = _read_json(config_path, "config.json") if config_path.is_file() else None

    return RunArtifacts(
        run_id=run_id,
        run_path=run_path,
        metadata=metadata,
        metrics=metrics,
        report=report,
        config=config,
    )
