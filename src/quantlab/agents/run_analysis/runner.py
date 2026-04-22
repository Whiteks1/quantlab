"""Runner wiring for run_analysis extractive pilot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import RunAnalysisOutputExistsError
from .extractor import extract_run_artifacts
from .log_writer import build_analysis_log, write_analysis_log
from .report_emitter import build_analysis_report, write_analysis_report
from .validator import validate_run_input

DEFAULT_RUNS_ROOT = Path("outputs/runs")
DEFAULT_REPORTS_ROOT = Path("outputs/agent_reports")


@dataclass(frozen=True)
class RunAnalysisResult:
    """Output summary for one run_analysis execution."""

    run_id: str
    report_path: Path
    log_path: Path
    files_written: tuple[Path, Path]


def run_analysis(
    run_id: str,
    runs_root: str | Path = DEFAULT_RUNS_ROOT,
    reports_root: str | Path = DEFAULT_REPORTS_ROOT,
) -> RunAnalysisResult:
    """Execute extractive run analysis and persist report + structured log."""
    validate_run_input(run_id, runs_root)
    artifacts = extract_run_artifacts(run_id, runs_root)

    reports_dir = Path(reports_root)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"{run_id}_analysis.md"
    log_path = reports_dir / f"{run_id}_analysis.log.json"

    if report_path.exists():
        raise RunAnalysisOutputExistsError(report_path)
    if log_path.exists():
        raise RunAnalysisOutputExistsError(log_path)

    report_markdown = build_analysis_report(artifacts)
    log_payload = build_analysis_log(
        run_id=run_id,
        report_path=report_path,
        log_path=log_path,
        artifacts=artifacts,
        report_markdown=report_markdown,
    )

    try:
        write_analysis_log(log_path, log_payload)
        write_analysis_report(report_path, report_markdown)
    except Exception:
        if report_path.exists():
            report_path.unlink()
        if log_path.exists():
            log_path.unlink()
        raise

    return RunAnalysisResult(
        run_id=run_id,
        report_path=report_path,
        log_path=log_path,
        files_written=(report_path, log_path),
    )
