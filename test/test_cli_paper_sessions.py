from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from quantlab.cli.paper_sessions import (
    build_paper_sessions_health,
    handle_paper_session_commands,
)
from quantlab.errors import ConfigError


@pytest.fixture()
def paper_sessions_root(tmp_path: Path) -> Path:
    root = tmp_path / "paper_sessions"
    root.mkdir()

    for session_id, status, request_id, created_at, updated_at in [
        ("paper_001", "success", "req_001", "2026-03-25T12:00:00", "2026-03-25T12:05:00"),
        ("paper_002", "failed", "req_002", "2026-03-25T12:10:00", "2026-03-25T12:15:00"),
        ("paper_003", "running", "req_003", "2026-03-25T12:20:00", "2026-03-25T12:25:00"),
    ]:
        session_dir = root / session_id
        session_dir.mkdir()
        (session_dir / "artifacts").mkdir()

        (session_dir / "session_metadata.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "run_id": session_id,
                    "mode": "paper",
                    "command": "paper",
                    "status": status,
                    "created_at": created_at,
                    "request_id": request_id,
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "session_status.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "mode": "paper",
                    "command": "paper",
                    "status": status,
                    "request_id": request_id,
                    "updated_at": updated_at,
                    "message": "boom" if status == "failed" else None,
                    "error_type": "DataError" if status == "failed" else None,
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "report.json").write_text(
            json.dumps(
                {
                    "status": status,
                    "header": {"run_id": session_id, "mode": "paper"},
                    "machine_contract": {
                        "contract_type": "quantlab.paper.result",
                    },
                }
            ),
            encoding="utf-8",
        )

    return root


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "paper_sessions_list": None,
        "paper_sessions_show": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestPaperSessionsList:
    def test_returns_true_when_run(self, paper_sessions_root: Path):
        args = _make_args(paper_sessions_list=str(paper_sessions_root))
        result = handle_paper_session_commands(args)
        assert result is True

    def test_prints_session_ids_and_status(self, paper_sessions_root: Path, capsys):
        args = _make_args(paper_sessions_list=str(paper_sessions_root))
        handle_paper_session_commands(args)
        out = capsys.readouterr().out
        assert "paper_001" in out
        assert "paper_002" in out
        assert "paper_003" in out
        assert "success" in out
        assert "failed" in out

    def test_invalid_root_raises_config_error(self, tmp_path: Path):
        args = _make_args(paper_sessions_list=str(tmp_path / "missing"))
        with pytest.raises(ConfigError):
            handle_paper_session_commands(args)


class TestPaperSessionsHealth:
    def test_builds_compact_health_summary(self, paper_sessions_root: Path):
        health = build_paper_sessions_health(paper_sessions_root)

        assert health["total_sessions"] == 3
        assert health["status_counts"]["success"] == 1
        assert health["status_counts"]["failed"] == 1
        assert health["status_counts"]["running"] == 1
        assert health["latest_session_id"] == "paper_003"
        assert health["latest_session_status"] == "running"
        assert health["latest_issue_session_id"] == "paper_003"
        assert health["latest_issue_status"] == "running"

    def test_prints_health_summary(self, paper_sessions_root: Path, capsys):
        args = _make_args(paper_sessions_health=str(paper_sessions_root))
        result = handle_paper_session_commands(args)
        assert result is True

        out = capsys.readouterr().out
        assert "total_sessions" in out
        assert "latest_session_id" in out
        assert "paper_003" in out
        assert "failed" in out
        assert "running" in out

    def test_invalid_root_raises_config_error(self, tmp_path: Path):
        args = _make_args(paper_sessions_health=str(tmp_path / "missing"))
        with pytest.raises(ConfigError):
            handle_paper_session_commands(args)


class TestPaperSessionsShow:
    def test_returns_true_when_run(self, paper_sessions_root: Path):
        args = _make_args(paper_sessions_show=str(paper_sessions_root / "paper_001"))
        result = handle_paper_session_commands(args)
        assert result is True

    def test_prints_key_session_fields(self, paper_sessions_root: Path, capsys):
        args = _make_args(paper_sessions_show=str(paper_sessions_root / "paper_002"))
        handle_paper_session_commands(args)
        out = capsys.readouterr().out
        assert "paper_002" in out
        assert "quantlab.paper.result" in out
        assert "DataError" in out
        assert "boom" in out

    def test_invalid_session_dir_raises_config_error(self, paper_sessions_root: Path):
        invalid_dir = paper_sessions_root / "not_a_session"
        invalid_dir.mkdir()
        args = _make_args(paper_sessions_show=str(invalid_dir))
        with pytest.raises(ConfigError):
            handle_paper_session_commands(args)


class TestNoMatch:
    def test_returns_false_when_no_command(self):
        args = _make_args()
        assert handle_paper_session_commands(args) is False
