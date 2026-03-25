from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from quantlab.cli.broker_dry_runs import (
    handle_broker_dry_runs_commands,
    load_broker_dry_run_summary,
)
from quantlab.errors import ConfigError
from quantlab.reporting.broker_dry_run_index import build_broker_dry_runs_index


@pytest.fixture()
def broker_dry_runs_root(tmp_path: Path) -> Path:
    root = tmp_path / "broker_dry_runs"
    root.mkdir()

    for session_id, status, allowed in [
        ("broker_001", "success", True),
        ("broker_002", "rejected", False),
    ]:
        session_dir = root / session_id
        session_dir.mkdir()
        (session_dir / "session_metadata.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "adapter_name": "kraken",
                    "status": status,
                    "created_at": "2026-03-25T12:00:00",
                    "request_id": f"req_{session_id}",
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "session_status.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "status": status,
                    "updated_at": "2026-03-25T12:05:00",
                    "preflight_allowed": allowed,
                    "preflight_reasons": [] if allowed else ["max_notional_exceeded"],
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "broker_dry_run.json").write_text(
            json.dumps(
                {
                    "artifact_type": "quantlab.kraken.dry_run_audit",
                    "adapter_name": "kraken",
                    "generated_at": "2026-03-25T12:05:00",
                    "preflight": {
                        "allowed": allowed,
                        "reasons": [] if allowed else ["max_notional_exceeded"],
                    },
                    "intent": {"request_id": f"req_{session_id}"},
                    "payload": {"pair": "ETH/USD"} if allowed else None,
                }
            ),
            encoding="utf-8",
        )

    return root


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "broker_dry_runs_list": None,
        "broker_dry_runs_show": None,
        "broker_dry_runs_index": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_lists_broker_dry_run_sessions(broker_dry_runs_root: Path, capsys):
    args = _make_args(broker_dry_runs_list=str(broker_dry_runs_root))
    result = handle_broker_dry_runs_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "broker_001" in out
    assert "broker_002" in out
    assert "kraken" in out
    assert "rejected" in out


def test_shows_single_broker_dry_run_session(broker_dry_runs_root: Path, capsys):
    args = _make_args(broker_dry_runs_show=str(broker_dry_runs_root / "broker_002"))
    result = handle_broker_dry_runs_commands(args)
    assert result is True

    out = capsys.readouterr().out
    assert "broker_002" in out
    assert "max_notional_exceeded" in out
    assert "quantlab.kraken.dry_run_audit" in out


def test_builds_broker_dry_runs_index(broker_dry_runs_root: Path):
    payload = build_broker_dry_runs_index(broker_dry_runs_root)

    assert payload["n_sessions"] == 2
    assert payload["sessions"][0]["session_id"] == "broker_001"
    assert payload["sessions"][1]["preflight_allowed"] is False


def test_invalid_session_dir_raises_config_error(broker_dry_runs_root: Path):
    invalid_dir = broker_dry_runs_root / "not_a_session"
    invalid_dir.mkdir()
    args = _make_args(broker_dry_runs_show=str(invalid_dir))
    with pytest.raises(ConfigError):
        handle_broker_dry_runs_commands(args)


def test_load_summary_requires_valid_dir(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_broker_dry_run_summary(tmp_path / "missing")
