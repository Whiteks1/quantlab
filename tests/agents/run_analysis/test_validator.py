"""Tests for run_analysis input validator scaffold slice."""

from pathlib import Path

import pytest

from quantlab.agents.run_analysis.errors import (
    InvalidRunIdError,
    MissingRunArtifactError,
    RunPathNotDirectoryError,
    RunPathNotFoundError,
)
from quantlab.agents.run_analysis.validator import validate_run_input


def _write_json_file(path: Path) -> None:
    path.write_text("{}", encoding="utf-8")


def test_validate_run_input_rejects_invalid_run_id(tmp_path: Path) -> None:
    with pytest.raises(InvalidRunIdError):
        validate_run_input("bad/run-id", tmp_path)


def test_validate_run_input_raises_when_path_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(RunPathNotFoundError):
        validate_run_input("run_001", tmp_path)


def test_validate_run_input_raises_when_path_is_not_directory(tmp_path: Path) -> None:
    run_id = "run_001"
    (tmp_path / run_id).write_text("not a directory", encoding="utf-8")

    with pytest.raises(RunPathNotDirectoryError):
        validate_run_input(run_id, tmp_path)


def test_validate_run_input_raises_when_metadata_missing(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write_json_file(run_dir / "metrics.json")
    _write_json_file(run_dir / "report.json")

    with pytest.raises(MissingRunArtifactError, match="metadata.json"):
        validate_run_input(run_id, tmp_path)


def test_validate_run_input_raises_when_metrics_missing(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write_json_file(run_dir / "metadata.json")
    _write_json_file(run_dir / "report.json")

    with pytest.raises(MissingRunArtifactError, match="metrics.json"):
        validate_run_input(run_id, tmp_path)


def test_validate_run_input_raises_when_report_missing(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write_json_file(run_dir / "metadata.json")
    _write_json_file(run_dir / "metrics.json")

    with pytest.raises(MissingRunArtifactError, match="report.json"):
        validate_run_input(run_id, tmp_path)


def test_validate_run_input_allows_missing_optional_config(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write_json_file(run_dir / "metadata.json")
    _write_json_file(run_dir / "metrics.json")
    _write_json_file(run_dir / "report.json")

    validated = validate_run_input(run_id, tmp_path)
    assert validated == run_dir


def test_validate_run_input_valid_case_with_config(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write_json_file(run_dir / "metadata.json")
    _write_json_file(run_dir / "metrics.json")
    _write_json_file(run_dir / "report.json")
    _write_json_file(run_dir / "config.json")

    validated = validate_run_input(run_id, tmp_path)
    assert validated == run_dir
