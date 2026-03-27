from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from quantlab.errors import ConfigError

QUANTLAB_HANDOFF_CONTRACT_TYPE = "calculadora_riesgo.quantlab_handoff"
QUANTLAB_HANDOFF_CONTRACT_VERSION = "1.0"
PRETRADE_HANDOFF_VALIDATION_FILENAME = "pretrade_handoff_validation.json"
PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE = "quantlab.pretrade.handoff_validation"

_REQUIRED_SOURCE_FIELDS = (
    "planner",
    "tradePlanContractType",
    "tradePlanContractVersion",
    "tradePlanId",
)
_REQUIRED_CONTEXT_FIELDS = ("symbol", "venue", "side")
_VALID_SIDES = {"buy", "sell"}


def load_quantlab_handoff_artifact(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise ConfigError(f"Pre-trade handoff artifact does not exist or is not a file: {artifact_path}")

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Pre-trade handoff artifact is not valid JSON: {artifact_path}") from exc

    if not isinstance(payload, dict):
        raise ConfigError("Pre-trade handoff artifact root must be a JSON object.")

    return payload


def build_quantlab_handoff_validation(
    payload: dict[str, Any],
    *,
    source_artifact_path: str | Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    created_at = (generated_at or datetime.now()).replace(microsecond=0).isoformat()
    source_artifact = str(Path(source_artifact_path))
    reasons: list[str] = []

    machine_contract = payload.get("machineContract")
    if not isinstance(machine_contract, dict):
        machine_contract = {}
        reasons.append("machine_contract_missing")

    contract_type = _clean_text(machine_contract.get("contractType"))
    contract_version = _clean_text(machine_contract.get("contractVersion"))
    if contract_type != QUANTLAB_HANDOFF_CONTRACT_TYPE:
        reasons.append("handoff_contract_type_invalid")
    if contract_version != QUANTLAB_HANDOFF_CONTRACT_VERSION:
        reasons.append("handoff_contract_version_invalid")

    handoff_id = _clean_text(payload.get("handoffId"))
    if not handoff_id:
        reasons.append("handoff_id_missing")

    generated_field = _clean_text(payload.get("generatedAt"))
    if not generated_field:
        reasons.append("generated_at_missing")

    source = payload.get("source")
    if not isinstance(source, dict):
        source = {}
        reasons.append("source_block_missing")

    source_summary = {}
    for field_name in _REQUIRED_SOURCE_FIELDS:
        value = _clean_text(source.get(field_name))
        source_summary[field_name] = value
        if not value:
            reasons.append(f"source_{field_name}_missing")

    pretrade_context = payload.get("pretradeContext")
    if not isinstance(pretrade_context, dict):
        pretrade_context = {}
        reasons.append("pretrade_context_missing")

    context_summary = {}
    derived_missing_fields: list[str] = []
    for field_name in _REQUIRED_CONTEXT_FIELDS:
        value = _clean_text(pretrade_context.get(field_name))
        if field_name == "side" and value:
            value = value.lower()
        context_summary[field_name] = value
        if not value:
            reasons.append(f"pretrade_context_{field_name}_missing")
            derived_missing_fields.append(field_name)

    if context_summary.get("side") and context_summary["side"] not in _VALID_SIDES:
        reasons.append("pretrade_context_side_invalid")

    context_summary["accountId"] = _clean_text(pretrade_context.get("accountId"))
    context_summary["strategyId"] = _clean_text(pretrade_context.get("strategyId"))

    quantlab_hints = payload.get("quantlabHints")
    if not isinstance(quantlab_hints, dict):
        quantlab_hints = {}
        reasons.append("quantlab_hints_missing")

    hinted_ready = bool(quantlab_hints.get("readyForDraftExecutionIntent"))
    hinted_missing_fields = _normalize_missing_fields(quantlab_hints.get("missingFields"))
    boundary_note = _clean_text(quantlab_hints.get("boundaryNote"))
    ready_for_draft_execution_intent = not derived_missing_fields

    if hinted_ready and not ready_for_draft_execution_intent:
        reasons.append("quantlab_hint_ready_mismatch")
    if sorted(hinted_missing_fields) != sorted(derived_missing_fields):
        reasons.append("quantlab_hint_missing_fields_mismatch")

    trade_plan = payload.get("tradePlan")
    if not isinstance(trade_plan, dict):
        trade_plan = {}
        reasons.append("trade_plan_missing")

    trade_plan_contract_type = _clean_text(trade_plan.get("contractType"))
    trade_plan_contract_version = _clean_text(trade_plan.get("contractVersion"))
    trade_plan_plan_id = _clean_text(trade_plan.get("planId"))
    if not trade_plan_contract_type:
        reasons.append("trade_plan_contract_type_missing")
    if not trade_plan_contract_version:
        reasons.append("trade_plan_contract_version_missing")
    if not trade_plan_plan_id:
        reasons.append("trade_plan_plan_id_missing")

    if (
        source_summary["tradePlanContractType"]
        and trade_plan_contract_type
        and source_summary["tradePlanContractType"] != trade_plan_contract_type
    ):
        reasons.append("trade_plan_contract_type_mismatch")
    if (
        source_summary["tradePlanContractVersion"]
        and trade_plan_contract_version
        and source_summary["tradePlanContractVersion"] != trade_plan_contract_version
    ):
        reasons.append("trade_plan_contract_version_mismatch")
    if source_summary["tradePlanId"] and trade_plan_plan_id and source_summary["tradePlanId"] != trade_plan_plan_id:
        reasons.append("trade_plan_id_mismatch")

    accepted = not reasons
    return {
        "artifact_type": PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE,
        "generated_at": created_at,
        "source_artifact_path": source_artifact,
        "accepted": accepted,
        "reasons": reasons,
        "handoff_contract": {
            "contract_type": contract_type,
            "contract_version": contract_version,
            "handoff_id": handoff_id,
            "generated_at": generated_field,
        },
        "source": {
            "planner": source_summary["planner"],
            "trade_plan_contract_type": source_summary["tradePlanContractType"],
            "trade_plan_contract_version": source_summary["tradePlanContractVersion"],
            "trade_plan_id": source_summary["tradePlanId"],
        },
        "pretrade_context": context_summary,
        "quantlab_hints": {
            "ready_for_draft_execution_intent": hinted_ready,
            "missing_fields": hinted_missing_fields,
            "boundary_note": boundary_note,
        },
        "trade_plan": {
            "contract_type": trade_plan_contract_type,
            "contract_version": trade_plan_contract_version,
            "plan_id": trade_plan_plan_id,
        },
        "quantlab_boundary": {
            "ready_for_draft_execution_intent": ready_for_draft_execution_intent,
            "policy_owner": "quantlab",
            "execution_authority": "quantlab",
            "submit_authority": "quantlab",
        },
    }


def write_quantlab_handoff_validation(
    validation: dict[str, Any],
    *,
    outdir: str | Path,
) -> Path:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    artifact_path = root / PRETRADE_HANDOFF_VALIDATION_FILENAME
    artifact_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact_path


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def _normalize_missing_fields(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        cleaned = _clean_text(item)
        if cleaned:
            normalized.append(cleaned)
    return normalized
