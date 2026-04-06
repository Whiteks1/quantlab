"""
CLI handler for Hyperliquid submit session inspection.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from quantlab.brokers import HyperliquidBrokerAdapter
from quantlab.brokers.session_store import (
    HYPERLIQUID_CANCEL_RESPONSE_FILENAME,
    HYPERLIQUID_FILL_SUMMARY_FILENAME,
    HYPERLIQUID_ORDER_STATUS_FILENAME,
    HYPERLIQUID_RECONCILIATION_FILENAME,
    HYPERLIQUID_SIGNED_ACTION_FILENAME,
    HYPERLIQUID_SUBMIT_METADATA_FILENAME,
    HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
    HYPERLIQUID_SUBMIT_STATUS_FILENAME,
    HYPERLIQUID_SUPERVISION_FILENAME,
    HyperliquidSubmitStore,
)
from quantlab.errors import ConfigError
from quantlab.runs.artifacts import load_json_with_fallback


def handle_hyperliquid_submit_sessions_commands(args) -> bool:
    if getattr(args, "hyperliquid_submit_sessions_supervise", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_supervise,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        signed_action, signed_action_path = load_json_with_fallback(session_dir, HYPERLIQUID_SIGNED_ACTION_FILENAME)
        submit_response, _ = load_json_with_fallback(session_dir, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
        if not signed_action_path:
            raise ConfigError("Hyperliquid submit session must have a signed-action artifact before supervision.")

        execution_account_id = _extract_execution_account_id(signed_action)
        oid = _extract_session_oid(submit_response)
        cloid = _extract_session_cloid(signed_action, submit_response)
        polls_requested = int(getattr(args, "hyperliquid_supervision_polls", 3))
        interval_seconds = float(getattr(args, "hyperliquid_supervision_interval_seconds", 2.0))
        if polls_requested <= 0:
            raise ConfigError("hyperliquid_supervision_polls must be a positive integer.")
        if interval_seconds < 0:
            raise ConfigError("hyperliquid_supervision_interval_seconds must be >= 0.")

        adapter = HyperliquidBrokerAdapter()
        order_report: dict[str, Any] | None = None
        reconciliation_report: dict[str, Any] | None = None
        fill_summary_report: dict[str, Any] | None = None
        snapshots: list[dict[str, Any]] = []
        ended_early = False

        for poll_index in range(1, polls_requested + 1):
            order_report = adapter.build_order_status_report(
                source_session_id=summary["session_id"],
                execution_account_id=execution_account_id,
                oid=oid,
                cloid=cloid,
                timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
            ).to_dict()
            reconciliation_report = adapter.build_reconciliation_report(
                source_session_id=summary["session_id"],
                execution_account_id=execution_account_id,
                oid=oid,
                cloid=cloid,
                signed_action_artifact=signed_action,
                timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
            ).to_dict()
            fill_summary_report = adapter.build_fill_summary_report(
                source_session_id=summary["session_id"],
                execution_account_id=execution_account_id,
                oid=oid,
                cloid=cloid,
                signed_action_artifact=signed_action,
                timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
            ).to_dict()

            snapshots.append(
                _build_hyperliquid_supervision_snapshot(
                    poll_index=poll_index,
                    order_report=order_report,
                    reconciliation_report=reconciliation_report,
                    fill_summary_report=fill_summary_report,
                )
            )

            if _is_hyperliquid_terminal_state(reconciliation_report.get("normalized_state")):
                ended_early = poll_index < polls_requested
                break
            if poll_index < polls_requested and interval_seconds > 0:
                time.sleep(interval_seconds)

        if order_report is None or reconciliation_report is None or fill_summary_report is None:
            raise ConfigError("Hyperliquid supervision did not produce any monitoring snapshots.")

        supervision_report = _build_hyperliquid_supervision_report(
            summary=summary,
            signed_action=signed_action,
            execution_account_id=execution_account_id,
            oid=oid,
            cloid=cloid,
            polls_requested=polls_requested,
            interval_seconds=interval_seconds,
            ended_early=ended_early,
            snapshots=snapshots,
            order_report=order_report,
            reconciliation_report=reconciliation_report,
            fill_summary_report=fill_summary_report,
        )

        store = HyperliquidSubmitStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_order_status(order_report)
        store.write_reconciliation(reconciliation_report)
        store.write_fill_summary(fill_summary_report)
        store.write_supervision(supervision_report)
        status = {
            "status": _derive_hyperliquid_submit_session_status(reconciliation_report),
            "updated_at": supervision_report["generated_at"],
            "submit_state": summary.get("submit_state"),
            "remote_submit_called": summary.get("remote_submit_called"),
            "submitted": summary.get("submitted"),
            "order_status_known": order_report["status_known"],
            "order_status_state": order_report["normalized_state"],
            "reconciliation_known": reconciliation_report["status_known"],
            "reconciliation_state": reconciliation_report["normalized_state"],
            "reconciliation_source": reconciliation_report["resolution_source"],
            "reconciliation_close_state": reconciliation_report.get("close_state"),
            "reconciliation_fill_state": reconciliation_report.get("fill_state"),
            "reconciliation_fill_count": reconciliation_report.get("fill_count"),
            "reconciliation_filled_size": reconciliation_report.get("filled_size"),
            "fill_summary_known": fill_summary_report["fills_known"],
            "fill_summary_state": fill_summary_report["fill_state"],
            "fill_summary_count": fill_summary_report["fill_count"],
            "fill_summary_filled_size": fill_summary_report["filled_size"],
            "supervision_state": supervision_report["supervision_state"],
            "supervision_attention_required": supervision_report["attention_required"],
            "supervision_poll_count": supervision_report["polls_completed"],
            "supervision_last_observed_at": supervision_report["last_observed_at"],
            "supervision_monitoring_mode": supervision_report["monitoring_mode"],
        }
        supervision_errors = supervision_report.get("errors") or []
        if supervision_errors:
            status["message"] = ", ".join(str(item) for item in supervision_errors)
        store.write_status(status)

        supervision_path = session_dir / HYPERLIQUID_SUPERVISION_FILENAME
        print("\nHyperliquid submit supervision completed:\n")
        print(f"  session_path        : {session_dir}")
        print(f"  supervision_path    : {supervision_path}")
        print(f"  supervision_state   : {supervision_report['supervision_state']}")
        print(f"  polls_completed     : {supervision_report['polls_completed']}")
        print(f"  effective_state     : {supervision_report['final_reconciliation_state']}")
        print(f"  fill_state          : {supervision_report['final_fill_state']}")
        return True
    if getattr(args, "hyperliquid_submit_sessions_fills", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_fills,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        signed_action, signed_action_path = load_json_with_fallback(session_dir, HYPERLIQUID_SIGNED_ACTION_FILENAME)
        submit_response, _ = load_json_with_fallback(session_dir, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
        if not signed_action_path:
            raise ConfigError("Hyperliquid submit session must have a signed-action artifact before fill refresh.")

        execution_account_id = _extract_execution_account_id(signed_action)
        oid = _extract_session_oid(submit_response)
        cloid = _extract_session_cloid(signed_action, submit_response)

        adapter = HyperliquidBrokerAdapter()
        report = adapter.build_fill_summary_report(
            source_session_id=summary["session_id"],
            execution_account_id=execution_account_id,
            oid=oid,
            cloid=cloid,
            signed_action_artifact=signed_action,
            timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
        ).to_dict()

        store = HyperliquidSubmitStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_fill_summary(report)
        status = {
            "status": str(summary.get("status") or summary.get("effective_order_state") or "submitted"),
            "updated_at": report["generated_at"],
            "submit_state": summary.get("submit_state"),
            "remote_submit_called": summary.get("remote_submit_called"),
            "submitted": summary.get("submitted"),
            "fill_summary_known": report["fills_known"],
            "fill_summary_state": report["fill_state"],
            "fill_summary_count": report["fill_count"],
            "fill_summary_filled_size": report["filled_size"],
        }
        if report.get("errors"):
            status["message"] = ", ".join(str(item) for item in report["errors"])
        store.write_status(status)

        fill_path = session_dir / HYPERLIQUID_FILL_SUMMARY_FILENAME
        print("\nHyperliquid submit fill summary refreshed:\n")
        print(f"  session_path   : {session_dir}")
        print(f"  fill_path      : {fill_path}")
        print(f"  fill_state     : {report['fill_state']}")
        print(f"  fill_count     : {report['fill_count']}")
        print(f"  filled_size    : {report['filled_size']}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_cancel", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_cancel,
            "Hyperliquid submit session directory",
        )
        if not bool(getattr(args, "hyperliquid_cancel_confirm", False)):
            raise ConfigError("hyperliquid_cancel_confirm is required for supervised Hyperliquid cancel.")

        reviewer = getattr(args, "hyperliquid_cancel_reviewer", None)
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ConfigError("hyperliquid_cancel_reviewer is required for supervised Hyperliquid cancel.")

        summary = load_hyperliquid_submit_summary(session_dir)
        signed_action, signed_action_path = load_json_with_fallback(session_dir, HYPERLIQUID_SIGNED_ACTION_FILENAME)
        submit_response, submit_response_path = load_json_with_fallback(session_dir, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
        if not signed_action_path:
            raise ConfigError("Hyperliquid submit session must have a signed-action artifact before cancel.")
        if not submit_response_path:
            raise ConfigError("Hyperliquid submit session must have a submit-response artifact before cancel.")

        adapter = HyperliquidBrokerAdapter()
        cancel_note = getattr(args, "hyperliquid_cancel_note", None)
        report = adapter.build_cancel_report(
            source_session_id=summary["session_id"],
            signed_action_artifact=signed_action,
            submit_response_artifact=submit_response,
            reviewer=reviewer.strip(),
            note=cancel_note.strip() if isinstance(cancel_note, str) and cancel_note.strip() else None,
            timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
            signing_private_key=getattr(args, "hyperliquid_private_key", None),
            signing_private_key_env=getattr(args, "hyperliquid_private_key_env", "HYPERLIQUID_PRIVATE_KEY"),
        ).to_dict()

        store = HyperliquidSubmitStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_cancel_response(report)
        status = {
            "status": _derive_hyperliquid_cancel_session_status(summary, report),
            "updated_at": report["generated_at"],
            "submit_state": summary.get("submit_state"),
            "remote_submit_called": summary.get("remote_submit_called"),
            "submitted": summary.get("submitted"),
            "order_status_known": summary.get("order_status_known"),
            "order_status_state": summary.get("latest_order_state"),
            "reconciliation_known": summary.get("reconciliation_known"),
            "reconciliation_state": summary.get("latest_reconciliation_state"),
            "reconciliation_source": summary.get("reconciliation_source"),
            "cancel_state": report["cancel_state"],
            "cancel_remote_called": report["remote_cancel_called"],
            "cancel_accepted": report["cancel_accepted"],
        }
        if report.get("errors"):
            status["message"] = ", ".join(str(item) for item in report["errors"])
        store.write_status(status)

        cancel_path = session_dir / HYPERLIQUID_CANCEL_RESPONSE_FILENAME
        print("\nHyperliquid submit cancel completed:\n")
        print(f"  session_path        : {session_dir}")
        print(f"  cancel_path         : {cancel_path}")
        print(f"  cancel_state        : {report['cancel_state']}")
        print(f"  cancel_accepted     : {report['cancel_accepted']}")
        print(f"  remote_cancel_called: {report['remote_cancel_called']}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_reconcile", None):
        session_dir = _require_directory(
            args.hyperliquid_submit_sessions_reconcile,
            "Hyperliquid submit session directory",
        )
        summary = load_hyperliquid_submit_summary(session_dir)

        signed_action, signed_action_path = load_json_with_fallback(session_dir, HYPERLIQUID_SIGNED_ACTION_FILENAME)
        submit_response, _ = load_json_with_fallback(session_dir, HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)
        if not signed_action_path:
            raise ConfigError("Hyperliquid submit session must have a signed-action artifact before reconciliation.")

        execution_account_id = _extract_execution_account_id(signed_action)
        oid = _extract_session_oid(submit_response)
        cloid = _extract_session_cloid(signed_action, submit_response)

        adapter = HyperliquidBrokerAdapter()
        report = adapter.build_reconciliation_report(
            source_session_id=summary["session_id"],
            execution_account_id=execution_account_id,
            oid=oid,
            cloid=cloid,
            signed_action_artifact=signed_action,
            timeout_seconds=float(getattr(args, "hyperliquid_preflight_timeout", 10.0)),
        ).to_dict()

        store = HyperliquidSubmitStore(summary["session_id"], base_dir=str(session_dir.parent))
        store.write_reconciliation(report)
        status = {
            "status": _derive_hyperliquid_submit_session_status(report),
            "updated_at": report["generated_at"],
            "submit_state": summary.get("submit_state"),
            "remote_submit_called": summary.get("remote_submit_called"),
            "submitted": summary.get("submitted"),
            "order_status_known": report["status_known"],
            "order_status_state": report["normalized_state"],
            "reconciliation_known": report["status_known"],
            "reconciliation_state": report["normalized_state"],
            "reconciliation_source": report["resolution_source"],
            "reconciliation_close_state": report.get("close_state"),
            "reconciliation_fill_state": report.get("fill_state"),
            "reconciliation_fill_count": report.get("fill_count"),
            "reconciliation_filled_size": report.get("filled_size"),
        }
        if report.get("errors"):
            status["message"] = ", ".join(str(item) for item in report["errors"])
        store.write_status(status)

        reconciliation_path = session_dir / HYPERLIQUID_RECONCILIATION_FILENAME
        print("\nHyperliquid submit reconciliation completed:\n")
        print(f"  session_path          : {session_dir}")
        print(f"  reconciliation_path   : {reconciliation_path}")
        print(f"  resolution_source     : {report['resolution_source']}")
        print(f"  state                 : {report['normalized_state']}")
        print(f"  close_state           : {report.get('close_state')}")
        print(f"  fill_state            : {report.get('fill_state')}")
        print(f"  fill_count            : {report.get('fill_count')}")
        print(f"  status_known          : {report['status_known']}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_health", None):
        root_dir = _require_directory(args.hyperliquid_submit_sessions_health, "Hyperliquid submit sessions root")
        health = build_hyperliquid_submission_health(root_dir)

        print(f"\nHyperliquid submission health: {root_dir}\n")
        print(f"  total_sessions          : {health['total_sessions']}")
        print(f"  submit_response_sessions: {health['submit_response_sessions']}")
        print(f"  cancel_response_sessions: {health['cancel_response_sessions']}")
        print(f"  fill_summary_sessions  : {health['fill_summary_sessions']}")
        print(f"  supervision_sessions   : {health['supervision_sessions']}")
        print(f"  submitted_sessions      : {health['submitted_sessions']}")
        print(f"  order_status_known      : {health['order_status_known_sessions']}")
        print(f"  reconciliation_sessions : {health['reconciliation_sessions']}")
        print(f"  effective_order_known   : {health['effective_order_known_sessions']}")
        print(f"  latest_close_state      : {health.get('latest_close_state')}")
        print(f"  latest_fill_state       : {health.get('latest_fill_state')}")
        print(f"  latest_supervision_state: {health.get('latest_supervision_state')}")
        print(f"  alert_status            : {health.get('alert_status')}")
        print(f"  alert_counts            : {health.get('alert_counts')}")
        print(f"  latest_alert_id         : {health.get('latest_alert_session_id')}")
        print(f"  latest_alert_code       : {health.get('latest_alert_code')}")
        print(f"  latest_submit_id        : {health.get('latest_submit_session_id')}")
        print(f"  latest_submit_state     : {health.get('latest_submit_state')}")
        print(f"  latest_order_state      : {health.get('latest_order_state')}")
        print(f"  latest_reconcile_state  : {health.get('latest_reconciliation_state')}")
        print(f"  latest_issue_id         : {health.get('latest_issue_session_id')}")
        print(f"  latest_issue_code       : {health.get('latest_issue_code')}")
        print(f"  latest_issue_at         : {health.get('latest_issue_at')}")
        return True

    if getattr(args, "hyperliquid_submit_sessions_alerts", None):
        root_dir = _require_directory(args.hyperliquid_submit_sessions_alerts, "Hyperliquid submit sessions root")
        alerts = build_hyperliquid_submission_alerts(root_dir)
        print(json.dumps(alerts, indent=2, sort_keys=True))
        return True

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
    reconciliation, reconciliation_path = load_json_with_fallback(path, HYPERLIQUID_RECONCILIATION_FILENAME)
    cancel_response, cancel_response_path = load_json_with_fallback(path, HYPERLIQUID_CANCEL_RESPONSE_FILENAME)
    fill_summary, fill_summary_path = load_json_with_fallback(path, HYPERLIQUID_FILL_SUMMARY_FILENAME)
    supervision, supervision_path = load_json_with_fallback(path, HYPERLIQUID_SUPERVISION_FILENAME)

    envelope = signed_action.get("signature_envelope", {}) if isinstance(signed_action, dict) else {}
    effective_order_known = bool(reconciliation.get("status_known")) if reconciliation_path else bool(order_status.get("status_known"))
    effective_order_state = (
        reconciliation.get("normalized_state") if reconciliation_path else order_status.get("normalized_state")
    )

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
        "submit_response_generated_at": submit_response.get("generated_at"),
        "submit_errors": submit_response.get("errors"),
        "oid": submit_response.get("oid"),
        "cloid": submit_response.get("cloid") or _extract_session_cloid(signed_action, submit_response),
        "cancel_state": cancel_response.get("cancel_state"),
        "cancel_accepted": cancel_response.get("cancel_accepted"),
        "cancel_remote_called": cancel_response.get("remote_cancel_called"),
        "cancel_response_generated_at": cancel_response.get("generated_at"),
        "cancel_errors": cancel_response.get("errors"),
        "cancel_response_present": bool(cancel_response_path),
        "fill_summary_known": fill_summary.get("fills_known"),
        "fill_summary_state": fill_summary.get("fill_state"),
        "fill_summary_count": fill_summary.get("fill_count"),
        "fill_summary_filled_size": fill_summary.get("filled_size"),
        "fill_summary_remaining_size": fill_summary.get("remaining_size"),
        "fill_summary_average_fill_price": fill_summary.get("average_fill_price"),
        "fill_summary_total_fee": fill_summary.get("total_fee"),
        "fill_summary_total_builder_fee": fill_summary.get("total_builder_fee"),
        "fill_summary_total_closed_pnl": fill_summary.get("total_closed_pnl"),
        "fill_summary_first_fill_time": fill_summary.get("first_fill_time"),
        "fill_summary_last_fill_time": fill_summary.get("last_fill_time"),
        "fill_summary_generated_at": fill_summary.get("generated_at"),
        "fill_summary_errors": fill_summary.get("errors"),
        "fill_summary_present": bool(fill_summary_path),
        "supervision_state": supervision.get("supervision_state"),
        "supervision_attention_required": supervision.get("attention_required"),
        "supervision_poll_count": supervision.get("polls_completed"),
        "supervision_polls_requested": supervision.get("polls_requested"),
        "supervision_monitoring_mode": supervision.get("monitoring_mode"),
        "supervision_transport_preference": supervision.get("transport_preference"),
        "supervision_resolved_transport": supervision.get("resolved_transport"),
        "supervision_last_observed_at": supervision.get("last_observed_at"),
        "supervision_generated_at": supervision.get("generated_at"),
        "supervision_errors": supervision.get("errors"),
        "supervision_present": bool(supervision_path),
        "order_status_known": order_status.get("status_known"),
        "latest_order_state": order_status.get("normalized_state"),
        "order_status_generated_at": order_status.get("generated_at"),
        "order_status_errors": order_status.get("errors"),
        "reconciliation_known": reconciliation.get("status_known"),
        "latest_reconciliation_state": reconciliation.get("normalized_state"),
        "reconciliation_close_state": reconciliation.get("close_state"),
        "reconciliation_fill_state": reconciliation.get("fill_state"),
        "reconciliation_fill_count": reconciliation.get("fill_count"),
        "reconciliation_filled_size": reconciliation.get("filled_size"),
        "reconciliation_remaining_size": reconciliation.get("remaining_size"),
        "reconciliation_average_fill_price": reconciliation.get("average_fill_price"),
        "reconciliation_last_fill_time": reconciliation.get("last_fill_time"),
        "reconciliation_generated_at": reconciliation.get("generated_at"),
        "reconciliation_source": reconciliation.get("resolution_source"),
        "reconciliation_errors": reconciliation.get("errors"),
        "reconciliation_present": bool(reconciliation_path),
        "effective_order_known": effective_order_known,
        "effective_order_state": effective_order_state,
        "order_status_present": bool(order_status_path),
        "signed_action_present": bool(signed_action_path),
        "submit_response_present": bool(response_path),
        "path": str(path),
        "metadata_path": str(path / HYPERLIQUID_SUBMIT_METADATA_FILENAME) if metadata_path else None,
        "status_path": str(path / HYPERLIQUID_SUBMIT_STATUS_FILENAME) if status_path else None,
        "signed_action_path": str(path / HYPERLIQUID_SIGNED_ACTION_FILENAME) if signed_action_path else None,
        "submit_response_path": str(path / HYPERLIQUID_SUBMIT_RESPONSE_FILENAME) if response_path else None,
        "cancel_response_path": str(path / HYPERLIQUID_CANCEL_RESPONSE_FILENAME) if cancel_response_path else None,
        "fill_summary_path": str(path / HYPERLIQUID_FILL_SUMMARY_FILENAME) if fill_summary_path else None,
        "supervision_path": str(path / HYPERLIQUID_SUPERVISION_FILENAME) if supervision_path else None,
        "order_status_path": str(path / HYPERLIQUID_ORDER_STATUS_FILENAME) if order_status_path else None,
        "reconciliation_path": str(path / HYPERLIQUID_RECONCILIATION_FILENAME) if reconciliation_path else None,
        **_derive_hyperliquid_submission_alert_summary(
            {
                "session_id": metadata.get("session_id") or status.get("session_id") or path.name,
                "status": status.get("status") or metadata.get("status"),
                "submit_state": submit_response.get("submit_state"),
                "submitted": submit_response.get("submitted"),
                "submit_response_present": bool(response_path),
                "cancel_response_present": bool(cancel_response_path),
                "cancel_accepted": cancel_response.get("cancel_accepted"),
                "cancel_state": cancel_response.get("cancel_state"),
                "supervision_present": bool(supervision_path),
                "supervision_attention_required": supervision.get("attention_required"),
                "supervision_errors": supervision.get("errors"),
                "effective_order_known": effective_order_known,
                "effective_order_state": effective_order_state,
                "order_status_present": bool(order_status_path),
                "reconciliation_present": bool(reconciliation_path),
                "order_status_errors": order_status.get("errors"),
                "reconciliation_errors": reconciliation.get("errors"),
                "submit_errors": submit_response.get("errors"),
            }
        ),
    }


def _derive_hyperliquid_submission_alert_summary(session: dict[str, Any]) -> dict[str, Any]:
    alerts = _collect_hyperliquid_submission_alerts([session])
    alert_counts = Counter(alert["severity"] for alert in alerts)
    if alert_counts.get("critical", 0):
        alert_status = "critical"
    elif alerts:
        alert_status = "warning"
    else:
        alert_status = "ok"

    latest_alert = max(alerts, key=_hyperliquid_alert_sort_key) if alerts else None
    return {
        "alert_status": alert_status,
        "alert_counts": dict(alert_counts),
        "alerts_present": bool(alerts),
        "latest_alert_session_id": latest_alert.get("session_id") if latest_alert else None,
        "latest_alert_code": latest_alert.get("alert_code") if latest_alert else None,
        "latest_alert_at": latest_alert.get("activity_at") if latest_alert else None,
    }


def _is_valid_hyperliquid_submit_dir(path: Path) -> bool:
    return any(
        (path / name).exists()
        for name in (
            HYPERLIQUID_SUBMIT_METADATA_FILENAME,
            HYPERLIQUID_SUBMIT_STATUS_FILENAME,
            HYPERLIQUID_SIGNED_ACTION_FILENAME,
            HYPERLIQUID_SUBMIT_RESPONSE_FILENAME,
            HYPERLIQUID_CANCEL_RESPONSE_FILENAME,
            HYPERLIQUID_FILL_SUMMARY_FILENAME,
            HYPERLIQUID_SUPERVISION_FILENAME,
            HYPERLIQUID_ORDER_STATUS_FILENAME,
            HYPERLIQUID_RECONCILIATION_FILENAME,
        )
    )


def _require_directory(path_str: str | Path, label: str) -> Path:
    path = Path(path_str)
    if not path.is_dir():
        raise ConfigError(f"{label} does not exist or is not a directory: {path}")
    return path


def _print_sessions_table(sessions: list[dict[str, Any]]) -> None:
    fields = ["session_id", "status", "submit_state", "effective_order_state", "created_at"]
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


def _extract_resolved_transport(signed_action: dict[str, Any]) -> str | None:
    if not isinstance(signed_action, dict):
        return None
    account_readiness = signed_action.get("account_readiness")
    if isinstance(account_readiness, dict):
        execution_context = account_readiness.get("execution_context")
        if isinstance(execution_context, dict):
            value = execution_context.get("resolved_transport")
            if isinstance(value, str) and value.strip():
                return value.strip()
    public_preflight = signed_action.get("public_preflight")
    if isinstance(public_preflight, dict):
        execution_context = public_preflight.get("execution_context")
        if isinstance(execution_context, dict):
            value = execution_context.get("resolved_transport")
            if isinstance(value, str) and value.strip():
                return value.strip()
    execution_context = signed_action.get("execution_context")
    if isinstance(execution_context, dict):
        value = execution_context.get("resolved_transport")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_hyperliquid_supervision_snapshot(
    *,
    poll_index: int,
    order_report: dict[str, Any],
    reconciliation_report: dict[str, Any],
    fill_summary_report: dict[str, Any],
) -> dict[str, Any]:
    observed_at = (
        fill_summary_report.get("generated_at")
        or reconciliation_report.get("generated_at")
        or order_report.get("generated_at")
    )
    return {
        "poll_index": poll_index,
        "observed_at": observed_at,
        "order_status_known": order_report.get("status_known"),
        "order_state": order_report.get("normalized_state"),
        "reconciliation_known": reconciliation_report.get("status_known"),
        "reconciliation_state": reconciliation_report.get("normalized_state"),
        "close_state": reconciliation_report.get("close_state"),
        "fill_state": fill_summary_report.get("fill_state") or reconciliation_report.get("fill_state"),
        "fill_count": fill_summary_report.get("fill_count"),
        "filled_size": fill_summary_report.get("filled_size"),
        "remaining_size": fill_summary_report.get("remaining_size"),
        "average_fill_price": fill_summary_report.get("average_fill_price"),
        "total_fee": fill_summary_report.get("total_fee"),
        "total_closed_pnl": fill_summary_report.get("total_closed_pnl"),
        "errors": list(
            item
            for item in (
                *(order_report.get("errors") or []),
                *(reconciliation_report.get("errors") or []),
                *(fill_summary_report.get("errors") or []),
            )
        ),
    }


def _is_hyperliquid_terminal_state(state: Any) -> bool:
    return str(state or "").strip().lower() in {"filled", "canceled", "rejected"}


def _build_hyperliquid_supervision_report(
    *,
    summary: dict[str, Any],
    signed_action: dict[str, Any],
    execution_account_id: str | None,
    oid: int | None,
    cloid: str | None,
    polls_requested: int,
    interval_seconds: float,
    ended_early: bool,
    snapshots: list[dict[str, Any]],
    order_report: dict[str, Any],
    reconciliation_report: dict[str, Any],
    fill_summary_report: dict[str, Any],
) -> dict[str, Any]:
    resolved_transport = _extract_resolved_transport(signed_action)
    monitoring_mode = "websocket_aware_rest_polling" if resolved_transport == "websocket" else "rest_polling"
    all_errors: list[str] = []
    for payload in (order_report, reconciliation_report, fill_summary_report):
        all_errors.extend(str(item) for item in (payload.get("errors") or []))

    attention_required = (
        not bool(reconciliation_report.get("status_known"))
        or str(reconciliation_report.get("normalized_state") or "unknown") == "unknown"
        or bool(all_errors)
    )
    final_state = str(reconciliation_report.get("normalized_state") or order_report.get("normalized_state") or "unknown")
    if _is_hyperliquid_terminal_state(final_state):
        supervision_state = "terminal"
    elif attention_required:
        supervision_state = "attention_required"
    else:
        supervision_state = "active"

    return {
        "artifact_type": "quantlab.hyperliquid.supervision",
        "adapter_name": "hyperliquid",
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "source_session_id": summary.get("session_id"),
        "execution_account_id": execution_account_id,
        "oid": oid,
        "cloid": cloid,
        "transport_preference": "websocket" if resolved_transport == "websocket" else "rest",
        "resolved_transport": resolved_transport or "rest",
        "monitoring_mode": monitoring_mode,
        "private_websocket_implemented": False,
        "polls_requested": polls_requested,
        "polls_completed": len(snapshots),
        "interval_seconds": interval_seconds,
        "ended_early": ended_early,
        "attention_required": attention_required,
        "supervision_state": supervision_state,
        "final_order_state": order_report.get("normalized_state"),
        "final_reconciliation_state": reconciliation_report.get("normalized_state"),
        "final_close_state": reconciliation_report.get("close_state"),
        "final_fill_state": fill_summary_report.get("fill_state") or reconciliation_report.get("fill_state"),
        "final_fill_count": fill_summary_report.get("fill_count"),
        "final_filled_size": fill_summary_report.get("filled_size"),
        "final_remaining_size": fill_summary_report.get("remaining_size"),
        "final_average_fill_price": fill_summary_report.get("average_fill_price"),
        "final_total_fee": fill_summary_report.get("total_fee"),
        "final_total_closed_pnl": fill_summary_report.get("total_closed_pnl"),
        "last_observed_at": snapshots[-1].get("observed_at") if snapshots else None,
        "snapshots": snapshots,
        "errors": list(dict.fromkeys(all_errors)),
    }


def _derive_hyperliquid_submit_session_status(order_status: dict[str, Any]) -> str:
    if bool(order_status.get("status_known")):
        return str(order_status.get("normalized_state") or "submitted")
    return str(order_status.get("normalized_state") or "unknown")


def _derive_hyperliquid_cancel_session_status(summary: dict[str, Any], cancel_report: dict[str, Any]) -> str:
    if bool(cancel_report.get("cancel_accepted")):
        if summary.get("effective_order_state") == "canceled":
            return "canceled"
        return "cancel_pending"
    return str(summary.get("status") or summary.get("effective_order_state") or "submitted")


def build_hyperliquid_submission_health(root_dir: str | Path) -> dict[str, Any]:
    root = _require_directory(root_dir, "Hyperliquid submit sessions root")
    sessions = [load_hyperliquid_submit_summary(path) for path in scan_hyperliquid_submit_sessions(root)]
    alerts = _collect_hyperliquid_submission_alerts(sessions)
    latest_submit = _latest_by_activity(
        [session for session in sessions if session.get("submit_response_present")]
    )
    latest_issue = max(alerts, key=_hyperliquid_alert_sort_key) if alerts else None
    alert_counts = Counter(alert["severity"] for alert in alerts)
    if alert_counts.get("critical", 0):
        alert_status = "critical"
    elif alerts:
        alert_status = "warning"
    else:
        alert_status = "ok"

    return {
        "root_dir": str(root),
        "total_sessions": len(sessions),
        "submit_response_sessions": sum(1 for session in sessions if session.get("submit_response_present")),
        "cancel_response_sessions": sum(1 for session in sessions if session.get("cancel_response_present")),
        "fill_summary_sessions": sum(1 for session in sessions if session.get("fill_summary_present")),
        "supervision_sessions": sum(1 for session in sessions if session.get("supervision_present")),
        "supervision_attention_sessions": sum(
            1 for session in sessions if session.get("supervision_present") and session.get("supervision_attention_required")
        ),
        "submitted_sessions": sum(1 for session in sessions if session.get("submitted")),
        "order_status_known_sessions": sum(1 for session in sessions if session.get("order_status_known")),
        "reconciliation_sessions": sum(1 for session in sessions if session.get("reconciliation_present")),
        "effective_order_known_sessions": sum(1 for session in sessions if session.get("effective_order_known")),
        "status_counts": dict(Counter((session.get("status") or "unknown") for session in sessions)),
        "submit_state_counts": dict(
            Counter((session.get("submit_state") or "no_submit_response") for session in sessions)
        ),
        "cancel_state_counts": dict(
            Counter((session.get("cancel_state") or "no_cancel_response") for session in sessions)
        ),
        "close_state_counts": dict(
            Counter(
                (session.get("reconciliation_close_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "fill_state_counts": dict(
            Counter(
                (session.get("reconciliation_fill_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "order_state_counts": dict(
            Counter(
                (session.get("effective_order_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "alert_status": alert_status,
        "alert_counts": dict(alert_counts),
        "alerts_present": bool(alerts),
        "latest_alert_session_id": latest_issue.get("session_id") if latest_issue else None,
        "latest_alert_code": latest_issue.get("alert_code") if latest_issue else None,
        "latest_alert_at": latest_issue.get("activity_at") if latest_issue else None,
        "latest_submit_session_id": latest_submit.get("session_id") if latest_submit else None,
        "latest_submit_state": latest_submit.get("submit_state") if latest_submit else None,
        "latest_order_state": latest_submit.get("effective_order_state") if latest_submit else None,
        "latest_reconciliation_state": latest_submit.get("latest_reconciliation_state") if latest_submit else None,
        "latest_close_state": latest_submit.get("reconciliation_close_state") if latest_submit else None,
        "latest_fill_state": latest_submit.get("reconciliation_fill_state") if latest_submit else None,
        "latest_supervision_state": latest_submit.get("supervision_state") if latest_submit else None,
        "latest_submit_at": _activity_at(latest_submit) if latest_submit else None,
        "latest_issue_session_id": latest_issue.get("session_id") if latest_issue else None,
        "latest_issue_code": latest_issue.get("alert_code") if latest_issue else None,
        "latest_issue_at": latest_issue.get("activity_at") if latest_issue else None,
    }


def build_hyperliquid_submission_alerts(root_dir: str | Path) -> dict[str, Any]:
    root = _require_directory(root_dir, "Hyperliquid submit sessions root")
    sessions = [load_hyperliquid_submit_summary(path) for path in scan_hyperliquid_submit_sessions(root)]
    alerts = _collect_hyperliquid_submission_alerts(sessions)
    latest_alert = max(alerts, key=_hyperliquid_alert_sort_key) if alerts else None
    alert_counts = Counter(alert["severity"] for alert in alerts)

    if alert_counts.get("critical", 0):
        alert_status = "critical"
    elif alerts:
        alert_status = "warning"
    else:
        alert_status = "ok"

    return {
        "root_dir": str(root),
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "total_sessions": len(sessions),
        "submit_response_sessions": sum(1 for session in sessions if session.get("submit_response_present")),
        "cancel_response_sessions": sum(1 for session in sessions if session.get("cancel_response_present")),
        "fill_summary_sessions": sum(1 for session in sessions if session.get("fill_summary_present")),
        "supervision_sessions": sum(1 for session in sessions if session.get("supervision_present")),
        "submitted_sessions": sum(1 for session in sessions if session.get("submitted")),
        "close_state_counts": dict(
            Counter(
                (session.get("reconciliation_close_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "fill_state_counts": dict(
            Counter(
                (session.get("reconciliation_fill_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "order_state_counts": dict(
            Counter(
                (session.get("effective_order_state") or "unknown")
                for session in sessions
                if session.get("submit_response_present")
            )
        ),
        "alert_status": alert_status,
        "has_alerts": bool(alerts),
        "alert_counts": dict(alert_counts),
        "latest_alert_session_id": latest_alert.get("session_id") if latest_alert else None,
        "latest_alert_code": latest_alert.get("alert_code") if latest_alert else None,
        "latest_alert_at": latest_alert.get("activity_at") if latest_alert else None,
        "alerts": alerts,
    }


def _collect_hyperliquid_submission_alerts(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for session in sessions:
        if not session.get("submit_response_present"):
            continue

        submitted = bool(session.get("submitted"))
        submit_state = str(session.get("submit_state") or session.get("status") or "unknown")
        activity_at = _parse_activity_timestamp(session)

        if session.get("cancel_response_present") and not bool(session.get("cancel_accepted")):
            cancel_state = str(session.get("cancel_state") or "unknown")
            code_map = {
                "cancel_request_failed": "HYPERLIQUID_CANCEL_REQUEST_FAILED",
                "cancel_rejected": "HYPERLIQUID_CANCEL_REJECTED",
                "missing_signing_key": "HYPERLIQUID_CANCEL_SIGNING_KEY_MISSING",
                "signer_identity_mismatch": "HYPERLIQUID_CANCEL_SIGNER_MISMATCH",
            }
            severity = "critical" if cancel_state in {"cancel_request_failed", "cancel_rejected"} else "warning"
            alerts.append(
                _build_hyperliquid_alert(
                    code=code_map.get(cancel_state, "HYPERLIQUID_CANCEL_ATTENTION"),
                    severity=severity,
                    session=session,
                    activity_at=activity_at,
                    message=_join_reasons(session.get("cancel_errors")) or f"Hyperliquid cancel state is '{cancel_state}'.",
                )
            )

        if session.get("supervision_present") and bool(session.get("supervision_attention_required")):
            alerts.append(
                _build_hyperliquid_alert(
                    code="HYPERLIQUID_SUPERVISION_ATTENTION",
                    severity="warning" if session.get("effective_order_known") else "critical",
                    session=session,
                    activity_at=activity_at,
                    message=_join_reasons(session.get("supervision_errors"))
                    or "Hyperliquid supervision ended with attention_required = true.",
                )
            )

        if submitted:
            if not session.get("order_status_present") and not session.get("reconciliation_present"):
                alerts.append(
                    _build_hyperliquid_alert(
                        code="HYPERLIQUID_ORDER_STATUS_MISSING",
                        severity="warning",
                        session=session,
                        activity_at=activity_at,
                        message="Submitted Hyperliquid session has no persistent order-status artifact yet.",
                    )
                )
            elif not bool(session.get("effective_order_known")):
                alerts.append(
                    _build_hyperliquid_alert(
                        code="HYPERLIQUID_ORDER_STATUS_UNKNOWN",
                        severity="critical",
                        session=session,
                        activity_at=activity_at,
                        message=_join_reasons(session.get("reconciliation_errors") or session.get("order_status_errors")) or "Submitted Hyperliquid session has no known remote order state yet.",
                    )
                )
            elif session.get("effective_order_state") == "rejected":
                alerts.append(
                    _build_hyperliquid_alert(
                        code="HYPERLIQUID_ORDER_REJECTED",
                        severity="critical",
                        session=session,
                        activity_at=activity_at,
                        message="Submitted Hyperliquid session reached remote order state 'rejected'.",
                    )
                )
            elif session.get("effective_order_state") == "canceled":
                alerts.append(
                    _build_hyperliquid_alert(
                        code="HYPERLIQUID_ORDER_CANCELED",
                        severity="warning",
                        session=session,
                        activity_at=activity_at,
                        message="Submitted Hyperliquid session reached remote order state 'canceled'.",
                    )
                )
            continue

        code_map = {
            "submit_request_failed": "HYPERLIQUID_SUBMIT_REQUEST_FAILED",
            "submit_rejected": "HYPERLIQUID_SUBMIT_REJECTED",
            "signed_action_not_ready": "HYPERLIQUID_SIGNED_ACTION_NOT_READY",
            "signed_action_not_signed": "HYPERLIQUID_SIGNED_ACTION_UNSIGNED",
            "signature_missing": "HYPERLIQUID_SIGNATURE_MISSING",
            "submit_payload_unavailable": "HYPERLIQUID_SUBMIT_PAYLOAD_MISSING",
        }
        severity = "critical" if submit_state in {"submit_request_failed", "submit_rejected"} else "warning"
        alerts.append(
            _build_hyperliquid_alert(
                code=code_map.get(submit_state, "HYPERLIQUID_SUBMIT_ATTENTION"),
                severity=severity,
                session=session,
                activity_at=activity_at,
                message=_join_reasons(session.get("submit_errors")) or f"Hyperliquid submit session is in state '{submit_state}'.",
            )
        )

    return alerts


def _build_hyperliquid_alert(
    *,
    code: str,
    severity: str,
    session: dict[str, Any],
    activity_at: dt.datetime | None,
    message: str,
) -> dict[str, Any]:
    return {
        "alert_code": code,
        "severity": severity,
        "session_id": session.get("session_id"),
        "status": session.get("status"),
        "submit_state": session.get("submit_state"),
        "order_status_state": session.get("effective_order_state"),
        "activity_at": activity_at.replace(microsecond=0).isoformat() if activity_at else None,
        "path": session.get("path"),
        "message": message,
    }


def _join_reasons(values: Any) -> str | None:
    if not isinstance(values, list):
        return None
    parts = [str(value) for value in values if str(value).strip()]
    return ", ".join(parts) if parts else None


def _activity_at(session: dict[str, Any] | None) -> str | None:
    activity_at = _parse_activity_timestamp(session) if session else None
    return activity_at.replace(microsecond=0).isoformat() if activity_at else None


def _parse_activity_timestamp(session: dict[str, Any] | None) -> dt.datetime | None:
    if not session:
        return None

    for key in (
        "supervision_generated_at",
        "cancel_response_generated_at",
        "fill_summary_generated_at",
        "reconciliation_generated_at",
        "order_status_generated_at",
        "submit_response_generated_at",
        "updated_at",
        "created_at",
    ):
        value = session.get(key)
        if not value:
            continue
        try:
            return dt.datetime.fromisoformat(str(value))
        except ValueError:
            continue
    return None


def _latest_by_activity(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    dated = [(session, _parse_activity_timestamp(session)) for session in sessions]
    dated = [(session, stamp) for session, stamp in dated if stamp is not None]
    if not dated:
        return None
    dated.sort(key=lambda item: item[1])
    return dated[-1][0]


def _hyperliquid_alert_sort_key(alert: dict[str, Any]) -> tuple[dt.datetime, str]:
    activity_at = alert.get("activity_at")
    try:
        parsed = dt.datetime.fromisoformat(str(activity_at)) if activity_at else dt.datetime.min
    except ValueError:
        parsed = dt.datetime.min
    return parsed, str(alert.get("session_id") or "")
