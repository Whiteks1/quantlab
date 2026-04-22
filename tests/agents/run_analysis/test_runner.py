"""Tests for run_analysis runner wiring."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import quantlab.agents.run_analysis.runner as runner_module
from quantlab.agents.run_analysis.errors import RunAnalysisOutputExistsError
from quantlab.agents.run_analysis.log_writer import (
    LOG_SCHEMA_VERSION,
    compute_output_hash,
)
from quantlab.agents.run_analysis.report_emitter import (
    NON_GOALS_ACKNOWLEDGMENT_LITERAL,
)
from quantlab.agents.run_analysis.runner import run_analysis


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _make_valid_run(runs_root: Path, run_id: str = "run_001") -> Path:
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.2}')
    _write(run_dir / "report.json", '{"summary":"ok"}')
    return run_dir


def _normalize_report(report_text: str) -> str:
    return "\n".join(line.rstrip() for line in report_text.replace("\r\n", "\n").split("\n"))


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_run_analysis_valid_writes_report_and_log(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)

    assert result.report_path.exists()
    assert result.log_path.exists()


def test_run_analysis_report_contains_non_goals_ack_literal(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)
    report_text = result.report_path.read_text(encoding="utf-8")

    assert NON_GOALS_ACKNOWLEDGMENT_LITERAL in report_text


def test_run_analysis_log_contains_minimum_schema(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)
    payload = json.loads(result.log_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == LOG_SCHEMA_VERSION
    assert payload["run_id"] == run_id
    assert payload["status"] == "ok"
    assert payload["files_written"] == [str(result.report_path), str(result.log_path)]
    assert payload["input_hash"]
    assert payload["output_hash"]
    assert payload["output_hash"] == compute_output_hash(
        result.report_path.read_text(encoding="utf-8")
    )


def test_run_analysis_same_input_same_report_under_normalization(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root_a = tmp_path / "agent_reports_a"
    reports_root_b = tmp_path / "agent_reports_b"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result_a = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root_a)
    result_b = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root_b)

    report_a = _normalize_report(result_a.report_path.read_text(encoding="utf-8"))
    report_b = _normalize_report(result_b.report_path.read_text(encoding="utf-8"))
    assert report_a == report_b

    payload_a = json.loads(result_a.log_path.read_text(encoding="utf-8"))
    payload_b = json.loads(result_b.log_path.read_text(encoding="utf-8"))
    assert payload_a["input_hash"] == payload_b["input_hash"]
    assert payload_a["output_hash"] == payload_b["output_hash"]


def test_run_analysis_no_overwrite_when_report_exists(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)
    reports_root.mkdir(parents=True)
    existing_report = reports_root / f"{run_id}_analysis.md"
    _write(existing_report, "existing report")

    with pytest.raises(RunAnalysisOutputExistsError):
        run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)

    assert existing_report.read_text(encoding="utf-8") == "existing report"
    assert not (reports_root / f"{run_id}_analysis.log.json").exists()


def test_run_analysis_no_overwrite_is_stable_after_first_success(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    first = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)
    report_before = first.report_path.read_text(encoding="utf-8")
    log_before = first.log_path.read_text(encoding="utf-8")

    with pytest.raises(RunAnalysisOutputExistsError):
        run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)

    assert first.report_path.read_text(encoding="utf-8") == report_before
    assert first.log_path.read_text(encoding="utf-8") == log_before


def test_run_analysis_does_not_leave_partial_report_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)
    reports_root.mkdir(parents=True)

    def _failing_report_writer(report_path: Path, markdown: str) -> None:
        _write(report_path, "partial")
        raise RuntimeError("forced failure")

    monkeypatch.setattr(runner_module, "write_analysis_report", _failing_report_writer)

    with pytest.raises(RuntimeError, match="forced failure"):
        run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)

    assert not (reports_root / f"{run_id}_analysis.md").exists()
    assert not (reports_root / f"{run_id}_analysis.log.json").exists()


def test_run_analysis_files_written_reflects_exactly_report_and_log(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)

    assert result.files_written == (result.report_path, result.log_path)


def test_run_analysis_hashes_are_present_and_consistent(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    _make_valid_run(runs_root, run_id)

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)
    payload = json.loads(result.log_path.read_text(encoding="utf-8"))
    report_text = result.report_path.read_text(encoding="utf-8")

    assert isinstance(payload["input_hash"], str)
    assert isinstance(payload["output_hash"], str)
    assert len(payload["input_hash"]) == 64
    assert len(payload["output_hash"]) == 64
    assert payload["output_hash"] == _sha256_text(report_text.replace("\r\n", "\n"))


@pytest.mark.parametrize("with_config", [False, True])
def test_non_goals_ack_literal_always_present(tmp_path: Path, with_config: bool) -> None:
    runs_root = tmp_path / "runs"
    reports_root = tmp_path / "agent_reports"
    run_id = "run_001"
    run_dir = _make_valid_run(runs_root, run_id)
    if with_config:
        _write(run_dir / "config.json", '{"symbol":"BTC-USD"}')

    result = run_analysis(run_id=run_id, runs_root=runs_root, reports_root=reports_root)
    report_text = result.report_path.read_text(encoding="utf-8")

    assert NON_GOALS_ACKNOWLEDGMENT_LITERAL in report_text
