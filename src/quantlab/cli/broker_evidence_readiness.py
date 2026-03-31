from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from quantlab.errors import ConfigError


ARTIFACT_FILENAME = "broker_evidence_readiness.json"


def _iso_now() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _normalize_non_empty(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _presence_entry(*, kind: str, source_name: str, present: bool, source: str) -> dict[str, object]:
    return {
        "kind": kind,
        "source_name": source_name,
        "present": present,
        "source": source,
    }


def _path_entry(path_value: Path) -> dict[str, object]:
    return {
        "path": str(path_value),
        "exists": path_value.exists(),
        "is_dir": path_value.is_dir(),
    }


def _resolve_hyperliquid_execution_identity(args) -> dict[str, object]:
    execution_account_id = _normalize_non_empty(getattr(args, "execution_account_id", None))
    if not execution_account_id:
        execution_account_id = _normalize_non_empty(os.getenv("HYPERLIQUID_ACCOUNT"))
    if not execution_account_id:
        execution_account_id = _normalize_non_empty(os.getenv("HYPERLIQUID_ADDRESS"))

    execution_signer_id = _normalize_non_empty(getattr(args, "execution_signer_id", None))
    if not execution_signer_id:
        execution_signer_id = _normalize_non_empty(os.getenv("HYPERLIQUID_SIGNER_ID"))

    execution_signer_type = _normalize_non_empty(getattr(args, "execution_signer_type", None))
    if not execution_signer_type:
        execution_signer_type = _normalize_non_empty(os.getenv("HYPERLIQUID_SIGNER_TYPE"))
    if not execution_signer_type:
        execution_signer_type = "direct"

    return {
        "execution_account_id": execution_account_id,
        "execution_signer_id": execution_signer_id,
        "execution_signer_type": execution_signer_type,
    }


def build_broker_evidence_readiness_report(args, *, project_root: Path) -> dict[str, object]:
    project_root = project_root.resolve()
    outputs_root = project_root / "outputs"
    runbook_path = project_root / "docs" / "supervised-broker-runbook.md"
    paper_sessions_root = outputs_root / "paper_sessions"
    kraken_root = outputs_root / "broker_order_validations"
    hyperliquid_root = outputs_root / "hyperliquid_submits"

    kraken_api_key = _normalize_non_empty(getattr(args, "kraken_api_key", None))
    kraken_api_secret = _normalize_non_empty(getattr(args, "kraken_api_secret", None))
    kraken_api_key_env = _normalize_non_empty(getattr(args, "kraken_api_key_env", None)) or "KRAKEN_API_KEY"
    kraken_api_secret_env = _normalize_non_empty(getattr(args, "kraken_api_secret_env", None)) or "KRAKEN_API_SECRET"

    if not kraken_api_key:
        kraken_api_key = _normalize_non_empty(os.getenv(kraken_api_key_env))
    if not kraken_api_secret:
        kraken_api_secret = _normalize_non_empty(os.getenv(kraken_api_secret_env))

    hyperliquid_private_key = _normalize_non_empty(getattr(args, "hyperliquid_private_key", None))
    hyperliquid_private_key_env = (
        _normalize_non_empty(getattr(args, "hyperliquid_private_key_env", None))
        or "HYPERLIQUID_PRIVATE_KEY"
    )
    if not hyperliquid_private_key:
        hyperliquid_private_key = _normalize_non_empty(os.getenv(hyperliquid_private_key_env))

    execution_identity = _resolve_hyperliquid_execution_identity(args)
    requested_corridor = getattr(args, "broker_evidence_corridor", None) or "auto"

    kraken_reasons: list[str] = []
    if not kraken_api_key:
        kraken_reasons.append("missing_kraken_api_key")
    if not kraken_api_secret:
        kraken_reasons.append("missing_kraken_api_secret")

    hyperliquid_reasons: list[str] = []
    if not hyperliquid_private_key:
        hyperliquid_reasons.append("missing_hyperliquid_private_key")
    if not execution_identity["execution_account_id"]:
        hyperliquid_reasons.append("missing_hyperliquid_execution_account_id")
    if execution_identity["execution_signer_type"] in {"api_wallet", "agent_wallet"} and not execution_identity["execution_signer_id"]:
        hyperliquid_reasons.append("missing_hyperliquid_signer_id")

    kraken_ready = not kraken_reasons
    hyperliquid_ready = not hyperliquid_reasons

    resolved_corridor = None
    if requested_corridor == "kraken":
        resolved_corridor = "kraken"
    elif requested_corridor == "hyperliquid":
        resolved_corridor = "hyperliquid"
    elif kraken_ready:
        resolved_corridor = "kraken"
    elif hyperliquid_ready:
        resolved_corridor = "hyperliquid"

    selected_ready = {
        "kraken": kraken_ready,
        "hyperliquid": hyperliquid_ready,
    }.get(resolved_corridor, False)

    selected_reasons = {
        "kraken": kraken_reasons,
        "hyperliquid": hyperliquid_reasons,
    }.get(resolved_corridor, [])

    artifact = {
        "artifact_type": "quantlab.broker.evidence_readiness",
        "artifact_version": "1.0",
        "generated_at": _iso_now(),
        "project_root": str(project_root),
        "requested_corridor": requested_corridor,
        "resolved_corridor": resolved_corridor,
        "recommended_first_corridor": "kraken",
        "runbook": {
            "path": str(runbook_path),
            "exists": runbook_path.exists(),
        },
        "roots": {
            "paper_sessions": _path_entry(paper_sessions_root),
            "kraken_order_validations": _path_entry(kraken_root),
            "hyperliquid_submits": _path_entry(hyperliquid_root),
        },
        "corridors": {
            "kraken": {
                "ready": kraken_ready,
                "reasons": kraken_reasons,
                "credentials": [
                    _presence_entry(
                        kind="api_key",
                        source_name=kraken_api_key_env,
                        present=bool(kraken_api_key),
                        source="cli" if _normalize_non_empty(getattr(args, "kraken_api_key", None)) else "env",
                    ),
                    _presence_entry(
                        kind="api_secret",
                        source_name=kraken_api_secret_env,
                        present=bool(kraken_api_secret),
                        source="cli" if _normalize_non_empty(getattr(args, "kraken_api_secret", None)) else "env",
                    ),
                ],
                "expected_root": str(kraken_root),
                "corridor_note": "Validate -> approve -> bundle -> submit gate -> submit/reconcile/status/health.",
            },
            "hyperliquid": {
                "ready": hyperliquid_ready,
                "reasons": hyperliquid_reasons,
                "credentials": [
                    _presence_entry(
                        kind="private_key",
                        source_name=hyperliquid_private_key_env,
                        present=bool(hyperliquid_private_key),
                        source="cli" if _normalize_non_empty(getattr(args, "hyperliquid_private_key", None)) else "env",
                    ),
                    _presence_entry(
                        kind="execution_account_id",
                        source_name="execution-account-id/HYPERLIQUID_ACCOUNT/HYPERLIQUID_ADDRESS",
                        present=bool(execution_identity["execution_account_id"]),
                        source="cli_or_env",
                    ),
                    _presence_entry(
                        kind="execution_signer_id",
                        source_name="execution-signer-id/HYPERLIQUID_SIGNER_ID",
                        present=bool(execution_identity["execution_signer_id"]),
                        source="cli_or_env",
                    ),
                ],
                "execution_identity": execution_identity,
                "expected_root": str(hyperliquid_root),
                "corridor_note": "Readiness -> signed action -> submit session -> status/reconcile/fills/supervision/cancel.",
            },
        },
        "ready_for_evidence_pass": bool(resolved_corridor and selected_ready and runbook_path.exists()),
        "blocking_reasons": selected_reasons if resolved_corridor else [
            "no_ready_broker_corridor",
            *([] if runbook_path.exists() else ["missing_supervised_broker_runbook"]),
        ],
    }

    if resolved_corridor and not runbook_path.exists():
        artifact["ready_for_evidence_pass"] = False
        artifact["blocking_reasons"] = [*selected_reasons, "missing_supervised_broker_runbook"]

    return artifact


def write_broker_evidence_readiness_report(report: dict[str, object], *, outdir: Path) -> Path:
    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    artifact_path = outdir / ARTIFACT_FILENAME
    artifact_path.write_text(f"{json.dumps(report, indent=2, sort_keys=True)}\n", encoding="utf-8")
    return artifact_path


def handle_broker_evidence_readiness_commands(args, *, project_root: Path) -> dict[str, object] | bool:
    outdir_value = getattr(args, "broker_evidence_readiness_outdir", None)
    if not outdir_value:
        return False

    report = build_broker_evidence_readiness_report(args, project_root=project_root)
    artifact_path = write_broker_evidence_readiness_report(
        report,
        outdir=Path(outdir_value).resolve(),
    )

    print("\nBroker evidence readiness:\n")
    print(f"  artifact_path             : {artifact_path}")
    print(f"  requested_corridor        : {report['requested_corridor']}")
    print(f"  resolved_corridor         : {report['resolved_corridor'] or '-'}")
    print(f"  ready_for_evidence_pass   : {report['ready_for_evidence_pass']}")
    print(f"  recommended_first_corridor: {report['recommended_first_corridor']}")

    if not report["ready_for_evidence_pass"]:
        reasons = ", ".join(report["blocking_reasons"]) or "broker_evidence_not_ready"
        raise ConfigError(
            "Broker evidence readiness failed. "
            f"Reasons: {reasons}. Readiness artifact: {artifact_path}"
        )

    return {
        "status": "success",
        "mode": "broker_evidence_readiness",
        "artifact_path": str(artifact_path),
        "requested_corridor": report["requested_corridor"],
        "resolved_corridor": report["resolved_corridor"],
        "ready_for_evidence_pass": report["ready_for_evidence_pass"],
    }
