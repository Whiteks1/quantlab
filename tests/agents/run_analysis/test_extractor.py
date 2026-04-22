"""Tests for pure extraction of run_analysis artifacts."""

from pathlib import Path

import pytest

from quantlab.agents.run_analysis.extractor import (
    InvalidRunArtifactJsonError,
    extract_run_artifacts,
)


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_extract_run_artifacts_valid_with_three_required(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.1}')
    _write(run_dir / "report.json", '{"summary":"ok"}')

    result = extract_run_artifacts(run_id, tmp_path)

    assert result.run_id == run_id
    assert result.run_path == run_dir
    assert result.metadata == {"source": "backtest"}
    assert result.metrics == {"sharpe_simple": 1.1}
    assert result.report == {"summary": "ok"}
    assert result.config is None


def test_extract_run_artifacts_valid_with_config(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.1}')
    _write(run_dir / "report.json", '{"summary":"ok"}')
    _write(run_dir / "config.json", '{"symbol":"BTC-USD"}')

    result = extract_run_artifacts(run_id, tmp_path)

    assert result.config == {"symbol": "BTC-USD"}


def test_extract_run_artifacts_valid_without_config(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.1}')
    _write(run_dir / "report.json", '{"summary":"ok"}')

    result = extract_run_artifacts(run_id, tmp_path)

    assert result.config is None


def test_extract_run_artifacts_raises_on_invalid_metadata_json(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", "{")
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.1}')
    _write(run_dir / "report.json", '{"summary":"ok"}')

    with pytest.raises(InvalidRunArtifactJsonError, match="metadata.json"):
        extract_run_artifacts(run_id, tmp_path)


def test_extract_run_artifacts_raises_on_invalid_metrics_json(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", "{")
    _write(run_dir / "report.json", '{"summary":"ok"}')

    with pytest.raises(InvalidRunArtifactJsonError, match="metrics.json"):
        extract_run_artifacts(run_id, tmp_path)


def test_extract_run_artifacts_raises_on_invalid_report_json(tmp_path: Path) -> None:
    run_id = "run_001"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _write(run_dir / "metadata.json", '{"source":"backtest"}')
    _write(run_dir / "metrics.json", '{"sharpe_simple":1.1}')
    _write(run_dir / "report.json", "{")

    with pytest.raises(InvalidRunArtifactJsonError, match="report.json"):
        extract_run_artifacts(run_id, tmp_path)
