"""
Tests for CLI runs commands (Issue #12).

Tests handle_runs_commands with --runs-list, --runs-show, --runs-best.
Each test uses a minimal file-based fixture in a temp directory.
"""
from __future__ import annotations

import json
import shutil
import types
from pathlib import Path

import pytest

from quantlab.cli.runs import handle_runs_commands


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def runs_dir(tmp_path: Path) -> Path:
    """Create a minimal outputs/runs directory with two fake run dirs."""
    runs_root = tmp_path / "runs"
    runs_root.mkdir()

    for run_id, sharpe, total_return in [
        ("run_A", 1.5, 0.30),
        ("run_B", 0.8, 0.12),
    ]:
        run_dir = runs_root / run_id
        run_dir.mkdir()
        report = {
            "header": {
                "run_id": run_id,
                "mode": "backtest",
                "created_at": "2026-01-01T00:00:00",
                "git_commit": None,
            },
            "config_resolved": {
                "ticker": "ETH-USD",
                "start": "2023-01-01",
                "end": "2024-01-01",
            },
            "results": [
                {
                    "sharpe_simple": sharpe,
                    "total_return": total_return,
                    "max_drawdown": -0.10,
                    "trades": 20,
                }
            ],
        }
        (run_dir / "report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )

    return runs_root


def _make_args(**kwargs) -> types.SimpleNamespace:
    """Create a minimal argparse namespace."""
    defaults = {
        "runs_list": None,
        "runs_show": None,
        "runs_best": None,
        "metric": "sharpe_simple",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Tests: --runs-list
# ---------------------------------------------------------------------------

class TestRunsList:
    def test_returns_true_when_run(self, runs_dir: Path, capsys):
        args = _make_args(runs_list=str(runs_dir))
        result = handle_runs_commands(args)
        assert result is True

    def test_prints_both_run_ids(self, runs_dir: Path, capsys):
        args = _make_args(runs_list=str(runs_dir))
        handle_runs_commands(args)
        out = capsys.readouterr().out
        assert "run_A" in out
        assert "run_B" in out

    def test_empty_directory(self, tmp_path: Path, capsys):
        empty = tmp_path / "empty_runs"
        empty.mkdir()
        args = _make_args(runs_list=str(empty))
        result = handle_runs_commands(args)
        assert result is True
        out = capsys.readouterr().out
        assert "0 run(s)" in out or "No valid" in out

    def test_nonexistent_directory(self, tmp_path: Path, capsys):
        args = _make_args(runs_list=str(tmp_path / "does_not_exist"))
        result = handle_runs_commands(args)
        assert result is True


# ---------------------------------------------------------------------------
# Tests: --runs-show
# ---------------------------------------------------------------------------

class TestRunsShow:
    def test_returns_true_when_run(self, runs_dir: Path, capsys):
        run_dir = str(runs_dir / "run_A")
        args = _make_args(runs_show=run_dir)
        result = handle_runs_commands(args)
        assert result is True

    def test_prints_run_id(self, runs_dir: Path, capsys):
        run_dir = str(runs_dir / "run_A")
        args = _make_args(runs_show=run_dir)
        handle_runs_commands(args)
        out = capsys.readouterr().out
        assert "run_A" in out

    def test_prints_sharpe(self, runs_dir: Path, capsys):
        run_dir = str(runs_dir / "run_A")
        args = _make_args(runs_show=run_dir)
        handle_runs_commands(args)
        out = capsys.readouterr().out
        assert "1.5" in out


# ---------------------------------------------------------------------------
# Tests: --runs-best
# ---------------------------------------------------------------------------

class TestRunsBest:
    def test_returns_true_when_run(self, runs_dir: Path, capsys):
        args = _make_args(runs_best=str(runs_dir))
        result = handle_runs_commands(args)
        assert result is True

    def test_identifies_best_run(self, runs_dir: Path, capsys):
        args = _make_args(runs_best=str(runs_dir))
        handle_runs_commands(args)
        out = capsys.readouterr().out
        # run_A has sharpe=1.5, run_B has sharpe=0.8
        assert "run_A" in out

    def test_no_runs_with_metric(self, tmp_path: Path, capsys):
        """Directory with runs, but none have the requested metric."""
        runs_root = tmp_path / "runs"
        runs_root.mkdir()
        run_dir = runs_root / "run_C"
        run_dir.mkdir()
        (run_dir / "report.json").write_text(
            json.dumps({"header": {"run_id": "run_C"}, "results": []}),
            encoding="utf-8",
        )
        args = _make_args(runs_best=str(runs_root), metric="sharpe_simple")
        result = handle_runs_commands(args)
        assert result is True
        out = capsys.readouterr().out
        assert "No runs" in out

    def test_best_by_total_return(self, runs_dir: Path, capsys):
        args = _make_args(runs_best=str(runs_dir), metric="total_return")
        handle_runs_commands(args)
        out = capsys.readouterr().out
        # run_A has total_return=0.30, run_B has 0.12
        assert "run_A" in out


# ---------------------------------------------------------------------------
# Tests: no command matched
# ---------------------------------------------------------------------------

class TestNoMatch:
    def test_returns_false_when_no_command(self):
        args = _make_args()
        result = handle_runs_commands(args)
        assert result is False
