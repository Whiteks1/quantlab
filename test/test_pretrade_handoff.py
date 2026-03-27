from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from quantlab.cli.pretrade_handoff import handle_pretrade_handoff_commands
from quantlab.errors import ConfigError
from quantlab.pretrade.handoff import (
    PRETRADE_HANDOFF_VALIDATION_FILENAME,
    QUANTLAB_HANDOFF_CONTRACT_TYPE,
    QUANTLAB_HANDOFF_CONTRACT_VERSION,
)


def _make_args(**kwargs):
    defaults = {
        "pretrade_handoff_validate": None,
        "pretrade_handoff_validation_outdir": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _valid_handoff_payload() -> dict[str, object]:
    return {
        "machineContract": {
            "contractType": QUANTLAB_HANDOFF_CONTRACT_TYPE,
            "contractVersion": QUANTLAB_HANDOFF_CONTRACT_VERSION,
        },
        "generatedAt": "2026-03-27T12:00:00.000Z",
        "handoffId": "quantlab-example-001-handoff",
        "source": {
            "planner": "contract-fixture",
            "tradePlanContractType": "calculadora_riesgo.trade_plan",
            "tradePlanContractVersion": "1.0",
            "tradePlanId": "quantlab-example-001",
        },
        "pretradeContext": {
            "symbol": "ETH-USD",
            "venue": "hyperliquid",
            "side": "buy",
            "accountId": "acct_demo_001",
            "strategyId": "breakout_v1",
        },
        "quantlabHints": {
            "readyForDraftExecutionIntent": True,
            "missingFields": [],
            "boundaryNote": "Bounded handoff only.",
        },
        "tradePlan": {
            "contractType": "calculadora_riesgo.trade_plan",
            "contractVersion": "1.0",
            "planId": "quantlab-example-001",
        },
    }


def test_handle_pretrade_handoff_commands_writes_validation_artifact(tmp_path: Path, capsys):
    source_path = tmp_path / "quantlab_handoff.json"
    source_path.write_text(json.dumps(_valid_handoff_payload(), indent=2), encoding="utf-8")

    outdir = tmp_path / "validated"
    args = _make_args(
        pretrade_handoff_validate=str(source_path),
        pretrade_handoff_validation_outdir=str(outdir),
    )

    result = handle_pretrade_handoff_commands(args)

    artifact_path = outdir / PRETRADE_HANDOFF_VALIDATION_FILENAME
    assert isinstance(result, dict)
    assert result["accepted"] is True
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["accepted"] is True
    assert payload["pretrade_context"]["symbol"] == "ETH-USD"
    assert payload["quantlab_boundary"]["policy_owner"] == "quantlab"

    output = capsys.readouterr().out
    assert "Pre-trade handoff validation completed" in output
    assert str(artifact_path) in output


def test_handle_pretrade_handoff_commands_rejects_missing_context_field(tmp_path: Path):
    payload = _valid_handoff_payload()
    payload["pretradeContext"].pop("venue")
    payload["quantlabHints"]["readyForDraftExecutionIntent"] = False
    payload["quantlabHints"]["missingFields"] = ["venue"]

    source_path = tmp_path / "quantlab_handoff_invalid.json"
    source_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    args = _make_args(pretrade_handoff_validate=str(source_path))

    with pytest.raises(ConfigError) as exc_info:
        handle_pretrade_handoff_commands(args)

    artifact_path = tmp_path / PRETRADE_HANDOFF_VALIDATION_FILENAME
    assert artifact_path.exists()

    validation = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert validation["accepted"] is False
    assert "pretrade_context_venue_missing" in validation["reasons"]
    assert "Reasons:" in str(exc_info.value)
