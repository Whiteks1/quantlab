from __future__ import annotations

import json
from pathlib import Path

from quantlab.errors import ConfigError
from quantlab.pretrade.models import PretradePlan, PretradeRequest
from quantlab.pretrade.serializers import markdown_summary, plan_to_dict, summary_to_dict

PRETRADE_CONTRACT_TYPE = "quantlab.pretrade.plan"
PRETRADE_INPUT_FILENAME = "input.json"
PRETRADE_PLAN_FILENAME = "plan.json"
PRETRADE_SUMMARY_FILENAME = "summary.json"
PRETRADE_PLAN_MARKDOWN_FILENAME = "plan.md"
PRETRADE_EXECUTION_BRIDGE_FILENAME = "execution_bridge.json"


def default_pretrade_root(project_root: str | Path) -> Path:
    return Path(project_root) / "outputs" / "pretrade_sessions"


def ensure_pretrade_session_dir(
    root_dir: str | Path,
    session_id: str,
) -> Path:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    session_dir = root / session_id
    if session_dir.exists():
        raise ConfigError(f"Pre-trade session directory already exists: {session_dir}")
    session_dir.mkdir(parents=True, exist_ok=False)
    return session_dir


def write_pretrade_artifacts(
    plan: PretradePlan,
    *,
    root_dir: str | Path,
) -> dict[str, str]:
    session_dir = ensure_pretrade_session_dir(root_dir, plan.session_id)
    request_payload = _request_to_dict(plan.request, generated_at=plan.generated_at)
    plan_payload = plan_to_dict(plan)
    summary_payload = summary_to_dict(plan)
    markdown_payload = markdown_summary(plan)

    _write_json(session_dir / PRETRADE_INPUT_FILENAME, request_payload)
    _write_json(session_dir / PRETRADE_PLAN_FILENAME, plan_payload)
    _write_json(session_dir / PRETRADE_SUMMARY_FILENAME, summary_payload)
    (session_dir / PRETRADE_PLAN_MARKDOWN_FILENAME).write_text(
        markdown_payload,
        encoding="utf-8",
    )

    return {
        "session_dir": str(session_dir),
        "input_path": str(session_dir / PRETRADE_INPUT_FILENAME),
        "plan_path": str(session_dir / PRETRADE_PLAN_FILENAME),
        "summary_path": str(session_dir / PRETRADE_SUMMARY_FILENAME),
        "plan_markdown_path": str(session_dir / PRETRADE_PLAN_MARKDOWN_FILENAME),
    }


def write_pretrade_execution_bridge(
    bridge_payload: dict[str, object],
    *,
    session_dir: str | Path,
) -> str:
    root = Path(session_dir)
    if not root.exists():
        raise ConfigError(f"Pre-trade session directory does not exist: {root}")
    path = root / PRETRADE_EXECUTION_BRIDGE_FILENAME
    _write_json(path, bridge_payload)
    return str(path)


def _request_to_dict(request: PretradeRequest, *, generated_at: str) -> dict[str, object]:
    return {
        "machine_contract": {
            "contract_type": "quantlab.pretrade.input",
            "schema_version": "1.0",
        },
        "generated_at": generated_at,
        "request": {
            "symbol": request.symbol,
            "venue": request.venue,
            "side": request.side,
            "capital": request.capital,
            "risk_percent": request.risk_percent,
            "entry_price": request.entry_price,
            "stop_price": request.stop_price,
            "target_price": request.target_price,
            "estimated_fees": request.estimated_fees,
            "estimated_slippage": request.estimated_slippage,
            "account_id": request.account_id,
            "strategy_id": request.strategy_id,
            "notes": request.notes,
            "session_id": request.session_id,
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
