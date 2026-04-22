"""Report emitter for run_analysis extractive pilot."""

from __future__ import annotations

import json
from pathlib import Path

from .extractor import RunArtifacts

NON_GOALS_ACKNOWLEDGMENT_LITERAL = (
    "The agent layer must not govern or execute trading decisions, "
    "govern or execute risk decisions, or govern or execute runtime behavior."
)


def build_analysis_report(artifacts: RunArtifacts) -> str:
    """Build deterministic Markdown report content from extracted artifacts."""
    metadata_json = json.dumps(artifacts.metadata, indent=2, sort_keys=True)
    metrics_json = json.dumps(artifacts.metrics, indent=2, sort_keys=True)
    report_json = json.dumps(artifacts.report, indent=2, sort_keys=True)
    config_json = (
        json.dumps(artifacts.config, indent=2, sort_keys=True)
        if artifacts.config is not None
        else "null"
    )

    return "\n".join(
        [
            "# Run Analysis (Pilot - Extractive)",
            "",
            f"- run_id: `{artifacts.run_id}`",
            f"- run_path: `{artifacts.run_path}`",
            "",
            "## Non-goals acknowledgment (literal)",
            NON_GOALS_ACKNOWLEDGMENT_LITERAL,
            "",
            "## Extracted metadata.json",
            "```json",
            metadata_json,
            "```",
            "",
            "## Extracted metrics.json",
            "```json",
            metrics_json,
            "```",
            "",
            "## Extracted report.json",
            "```json",
            report_json,
            "```",
            "",
            "## Extracted config.json (optional)",
            "```json",
            config_json,
            "```",
            "",
        ]
    )


def write_analysis_report(report_path: Path, markdown: str) -> None:
    """Write Markdown report without overwriting existing files."""
    with report_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
