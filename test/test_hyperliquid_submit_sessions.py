from __future__ import annotations

import json
import types

import pytest

from quantlab.cli.hyperliquid_submit_sessions import (
    handle_hyperliquid_submit_sessions_commands,
    load_hyperliquid_submit_summary,
)
from quantlab.errors import ConfigError


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "hyperliquid_submit_sessions_list": None,
        "hyperliquid_submit_sessions_show": None,
        "hyperliquid_submit_sessions_index": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_session(tmp_path, name="20260327_hyperliquid_submit_demo"):
    session_dir = tmp_path / name
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": name,
                "status": "submitted",
                "created_at": "2026-03-27T12:00:00",
                "request_id": "req_demo",
                "source_artifact_path": "C:/tmp/hyperliquid_signed_action.json",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": name,
                "status": "submitted",
                "updated_at": "2026-03-27T12:01:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "signature_envelope": {
                    "signer_id": "0x1111111111111111111111111111111111111111",
                    "signature_state": "signed",
                },
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_submit_response.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.submit_response",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "response_type": "resting",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    return session_dir


def test_load_hyperliquid_submit_summary(tmp_path):
    session_dir = _write_session(tmp_path)
    summary = load_hyperliquid_submit_summary(session_dir)

    assert summary["session_id"] == "20260327_hyperliquid_submit_demo"
    assert summary["status"] == "submitted"
    assert summary["submit_state"] == "submitted_remote"
    assert summary["submitted"] is True
    assert summary["signed_action_present"] is True
    assert summary["submit_response_present"] is True


def test_list_hyperliquid_submit_sessions(tmp_path, capsys):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_list=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit sessions in" in output
    assert "submitted_remote" in output


def test_show_hyperliquid_submit_session(tmp_path, capsys):
    session_dir = _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_show=str(session_dir))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    output = capsys.readouterr().out
    assert "Hyperliquid submit session" in output
    assert "submitted_remote" in output


def test_refresh_hyperliquid_submit_index(tmp_path):
    _write_session(tmp_path)
    args = _make_args(hyperliquid_submit_sessions_index=str(tmp_path))

    assert handle_hyperliquid_submit_sessions_commands(args) is True
    assert (tmp_path / "hyperliquid_submits_index.json").exists()
    assert (tmp_path / "hyperliquid_submits_index.csv").exists()


def test_invalid_hyperliquid_submit_session_raises(tmp_path):
    session_dir = tmp_path / "bad_session"
    session_dir.mkdir()

    with pytest.raises(ConfigError):
        load_hyperliquid_submit_summary(session_dir)
