from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "research_ui" / "server.py"
SPEC = importlib.util.spec_from_file_location("research_ui_server", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
research_ui_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research_ui_server)


def _write_session(root: Path, session_id: str, status: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "artifacts").mkdir()
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": session_id,
                "mode": "paper",
                "command": "paper",
                "status": status,
                "created_at": "2026-03-25T18:00:00",
                "request_id": f"req_{session_id}",
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
                "request_id": f"req_{session_id}",
                "updated_at": "2026-03-25T18:05:00",
                "error_type": "DataError" if status == "failed" else None,
                "message": "boom" if status == "failed" else None,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "report.json").write_text(
        json.dumps(
            {
                "status": status,
                "header": {"run_id": session_id, "mode": "paper"},
                "machine_contract": {"contract_type": "quantlab.paper.result"},
            }
        ),
        encoding="utf-8",
    )


def test_build_paper_health_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0


def test_build_paper_health_payload_summarizes_existing_sessions(tmp_path: Path):
    paper_root = tmp_path / "outputs" / "paper_sessions"
    _write_session(paper_root, "paper_001", "success")
    _write_session(paper_root, "paper_002", "failed")

    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 2
    assert payload["status_counts"]["success"] == 1
    assert payload["status_counts"]["failed"] == 1
