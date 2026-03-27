"""
CLI handler for Hyperliquid submit session inspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers import HyperliquidBrokerAdapter
from quantlab.brokers.session_store import (
    HYPERLIQUID_ORDER_STATUS_FILENAME,
    HYPERLIQUID_SIGNED_ACTION_FILENAME,
    HYPERLIQUID_SUBMIT_METADATA_FILENAME,
    HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
    HYPERLIQUID_SUBMIT_STATUS_FILENAME,
    HyperliquidSubmitStore,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_hyperliquid_submit_sessions_commands(args) -> bool:
    if getattr(args, "hyperliquid_submit_sessions_status", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_status,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        signed_action, signed_action_path = load_json_with_fallback(session_dir, HYPERLIQUID_SIGNED_ACTION_FILENAME)
        submit_response, _ = load_json_with_fallback(session_dir, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
        if not signed_action_path:
            raise ConfigError("Hyperliquid submit session must have a signed-action artifact before status refresh.")

        execution_account_id = _extract_execution_account_id(signed_action)
        oid = _extract_session_oid(submit_response)
        cloid = _extract_session_cloid(signed_action, submit_response)

        adapter = HyperliquidBrokerAdapter()
        report = adapter.build_order_status_report(
            source_session_id=summary["session_id"],
            execution_account_id=execution_account_id,
            oid=oid,
            cloid=cloid,
            timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
        ).to_dict()

        store = HyperliquidSubmitStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_order_status(report)
        status = {
            "status": _derive_hyperliquid_submit_session_status(report),
            "updated_at": report["generated_at"],
            "submit_state": summary.get("submit_state"),
            "remote_submit_called": summary.get("remote_submit_called"),
            "submitted": summary.get("submitted"),
            "order_status_known": report["status_known"],
            "order_status_state": report["normalized_state"],
        }
        if report.get("errors"):
            status["message"] = ", ".join(str(item) for item in report["errors"])
        store.write_status(status)

        status_path = session_dir / HYPERLIQUID_ORDER_STATUS_FILENAME
        print("\nHyperliquid submit status refreshed:\n")
        print(f"  session_path   : {session_dir}")
        print(f"  status_path    : {status_path}")
        print(f"  state          : {report['normalized_state']}")
        print(f"  status_known   : {report['status_known']}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_list", None):
        root_dir = _require_directory(args.hyperliquid_submit_sessions_list, "Hyperliquid submit sessions root")
        sessions = [load_hyperliquid_submit_summary(path) for path in scan_hyperliquid_submit_sessions(root_dir)]

        print(f"\nHyperliquid submit sessions in: {root_dir}")
        print(f"Total: {len(sessions)} session(s) found\n")

        if not sessions:
            print("  No valid Hyperliquid submit session directories found.")
            return True

        _print_sessions_table(sessions)
        return True

    if getattr(args, "hyperliquid_submit_sessions_show", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_show,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        print(f"\nHyperliquid submit session: {session_dir}\n")
        for key, val in summary.items():
            print(f"  {key:24s}: {val}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_index", None):
        from quantlab.reporting.hyperliquid_submit_index import write_hyperliquid_submits_index

        root_dir = _require_directory(args.hyperliquid_submit_sessions_index, "Hyperliquid submit sessions root")
        csv_path, json_path = write_hyperliquid_submits_index(root_dir)
        print("\nHyperliquid submit index refreshed:\n")
        print(f"  csv_path : {csv_path}")
        print(f"  json_path: {json_path}")
        return True

    return False


def scan_hyperliquid_submit_sessions(root_dir: str | Path) -> Iterator[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        return

    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_hyperliquid_submit_dir(child):
            yield child


def load_hyperliquid_submit_summary(session_dir: str | Path) -> dict[str, Any]:
    path = Path(session_dir)
    if not path.is_dir():
        raise ConfigError(f"Hyperliquid submit session directory does not exist or is not a directory: {path}")
    if not _is_valid_hyperliquid_submit_dir(path):
        raise ConfigError(f"Not a valid Hyperliquid submit session directory: {path}")

    metadata, metadata_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_METADATA_FILENAME)
    status, status_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_STATUS_FILENAME)
    signed_action, signed_action_path = load_json_with_fallback(path, HYPERLIQUID_SIGNED_ACTION_FILENAME)
    submit_response, response_path = load_json_with_fallback(path, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
    order_status, order_status_path = load_json_with_fallback(path, HYPERLIQUID_ORDER_STATUS_FILENAME)

    envelope = signed_action.get("signature_envelope", {}) if isinstance(signed_action, dict) else {}

    return {
        "session_id": metadata.get("session_id") or status.get("session_id") or path.name,
        "status": status.get("status") or metadata.get("status"),
        "created_at": metadata.get("created_at"),
        "updated_at": status.get("updated_at"),
        "request_id": metadata.get("request_id"),
        "source_artifact_path": metadata.get("source_artifact_path") or submit_response.get("source_artifact_path"),
        "source_signer_id": metadata.get("source_signer_id") or submit_response.get("source_signer_id") or envelope.get("signer_id"),
        "signature_state": envelope.get("signature_state"),
        "submit_state": submit_response.get("submit_state"),
        "remote_submit_called": submit_response.get("remote_submit_called"),
        "submitted": submit_response.get("submitted"),
        "response_type": submit_response.get("response_type"),
        "oid": submit_response.get("oid"),
        "cloid": submit_response.get("cloid") or _extract_session_cloid(signed_action, submit_response),
        "order_status_known": order_status.get("status_known"),
        "latest_order_state": order_status.get("normalized_state"),
        "order_status_present": bool(order_status_path),
        "signed_action_present": bool(signed_action_path),
        "submit_response_present": bool(response_path),
        "path": str(path),
        "metadata_path": str(path / HYPERLIQUID_SUBMIT_METADATA_FILENAME) if metadata_path else None,
        "status_path": str(path / HYPERLIQUID_SUBMIT_STATUS_FILENAME) if status_path else None,
        "signed_action_path": str(path / HYPERLIQUID_SIGNED_ACTION_FILENAME) if signed_action_path else None,
        "submit_response_path": str(path / HYPERLIQUID_SUBMIT_RESPONSE_FILENAME) if response_path else None,
        "order_status_path": str(path / HYPERLIQUID_ORDER_STATUS_FILENAME) if order_status_path else None,
    }


def _is_valid_hyperliquid_submit_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            HYPERLIQUID_SUBMIT_METADATA_FILENAME,
            HYPERLIQUID_SUBMIT_STATUS_FILENAME,
            HYPERLIQUID_SIGNED_ACTION_FILENAME,
            HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
            HYPERLIQUID_ORDER_STATUS_FILENAME,
        )
    )


def _require_directory(path_str: str | Path, label: str) -> Path:
    path = Path(path_str)
    if not path.is_dir():
        raise ConfigError(f"{label} does not exist or is not a directory: {path}")
    return path


def _print_sessions_table(sessions: list[dict[str, Any]]) -> None:
    fields = ["session_id", "status", "submit_state", "latest_order_state", "created_at"]
    widths = {
        field: max(len(field), max((len(str(row.get(field) or "")) for row in sessions), default=0))
        for field in fields
    }

    header = "  ".join(field.ljust(widths[field]) for field in fields)
    print(header)
    print("-" * len(header))

    for session in sessions:
        row = "  ".join(str(session.get(field) or "").ljust(widths[field]) for field in fields)
        print(row)
    print()


def _extract_execution_account_id(signed_action: dict[str, Any]) -> str | None:
    if not isinstance(signed_action, dict):
        return None
    account_readiness = signed_action.get("account_readiness")
    if isinstance(account_readiness, dict):
        execution_context = account_readiness.get("execution_context")
        if isinstance(execution_context, dict):
            value = execution_context.get("execution_account_id")
            return str(value).strip() if isinstance(value, str) and value.strip() else None
    return None


def _extract_session_oid(submit_response: dict[str, Any]) -> int | None:
    oid = submit_response.get("oid") if isinstance(submit_response, dict) else None
    return oid if isinstance(oid, int) and oid >= 0 else None


def _extract_session_cloid(signed_action: dict[str, Any], submit_response: dict[str, Any]) -> str | None:
    if isinstance(submit_response, dict):
        cloid = submit_response.get("cloid")
        if isinstance(cloid, str) and cloid.strip():
            return cloid.strip()
    if not isinstance(signed_action, dict):
        return None
    action_payload = signed_action.get("action_payload")
    if not isinstance(action_payload, dict):
        return None
    orders = action_payload.get("orders")
    if not isinstance(orders, list) or not orders:
        return None
    first_order = orders[0]
    if not isinstance(first_order, dict):
        return None
    cloid = first_order.get("c")
    return cloid.strip() if isinstance(cloid, str) and cloid.strip() else None


def _derive_hyperliquid_submit_session_status(order_status: dict[str, Any]) -> str:
    if bool(order_status.get("status_known")):
        return str(order_status.get("normalized_state") or "submitted")
    return str(order_status.get("normalized_state") or "unknown")
