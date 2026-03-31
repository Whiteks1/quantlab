from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from quantlab.cli.broker_evidence_readiness import (
    ARTIFACT_FILENAME,
    build_broker_evidence_readiness_report,
    handle_broker_evidence_readiness_commands,
)
from quantlab.errors import ConfigError


def _build_args(**overrides) -> Namespace:
    base = {
        "broker_evidence_readiness_outdir": None,
        "broker_evidence_corridor": "auto",
        "kraken_api_key": None,
        "kraken_api_secret": None,
        "kraken_api_key_env": "KRAKEN_API_KEY",
        "kraken_api_secret_env": "KRAKEN_API_SECRET",
        "hyperliquid_private_key": None,
        "hyperliquid_private_key_env": "HYPERLIQUID_PRIVATE_KEY",
        "execution_account_id": None,
        "execution_signer_id": None,
        "execution_signer_type": None,
    }
    base.update(overrides)
    return Namespace(**base)


def test_build_broker_evidence_readiness_report_marks_missing_credentials(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)
    args = _build_args(broker_evidence_corridor="kraken")

    report = build_broker_evidence_readiness_report(args, project_root=tmp_path)

    assert report["ready_for_evidence_pass"] is False
    assert report["resolved_corridor"] == "kraken"
    assert "missing_kraken_api_key" in report["blocking_reasons"]
    assert "missing_kraken_api_secret" in report["blocking_reasons"]


def test_handle_broker_evidence_readiness_writes_artifact_before_failure(monkeypatch, tmp_path: Path):
    project_root = tmp_path / "repo"
    (project_root / "docs").mkdir(parents=True)
    (project_root / "docs" / "supervised-broker-runbook.md").write_text("# runbook\n", encoding="utf-8")
    outdir = tmp_path / "artifacts"
    args = _build_args(
        broker_evidence_readiness_outdir=str(outdir),
        broker_evidence_corridor="hyperliquid",
    )

    monkeypatch.delenv("HYPERLIQUID_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("HYPERLIQUID_ACCOUNT", raising=False)
    monkeypatch.delenv("HYPERLIQUID_ADDRESS", raising=False)

    with pytest.raises(ConfigError):
        handle_broker_evidence_readiness_commands(args, project_root=project_root)

    artifact_path = outdir / ARTIFACT_FILENAME
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["resolved_corridor"] == "hyperliquid"
    assert payload["ready_for_evidence_pass"] is False


def test_handle_broker_evidence_readiness_accepts_ready_kraken_path(monkeypatch, tmp_path: Path):
    project_root = tmp_path / "repo"
    (project_root / "docs").mkdir(parents=True)
    (project_root / "docs" / "supervised-broker-runbook.md").write_text("# runbook\n", encoding="utf-8")
    outdir = tmp_path / "artifacts"
    args = _build_args(
        broker_evidence_readiness_outdir=str(outdir),
        broker_evidence_corridor="kraken",
    )

    monkeypatch.setenv("KRAKEN_API_KEY", "demo-key")
    monkeypatch.setenv("KRAKEN_API_SECRET", "demo-secret")

    result = handle_broker_evidence_readiness_commands(args, project_root=project_root)

    assert result["status"] == "success"
    assert result["resolved_corridor"] == "kraken"
    payload = json.loads((outdir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    assert payload["ready_for_evidence_pass"] is True
