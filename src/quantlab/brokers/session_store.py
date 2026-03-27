from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.runs.serializers import save_json


BROKER_DRY_RUN_AUDIT_FILENAME = "broker_dry_run.json"
BROKER_DRY_RUN_METADATA_FILENAME = "session_metadata.json"
BROKER_DRY_RUN_STATUS_FILENAME = "session_status.json"
BROKER_ORDER_VALIDATE_FILENAME = "broker_order_validate.json"
BROKER_ORDER_VALIDATE_METADATA_FILENAME = "session_metadata.json"
BROKER_ORDER_VALIDATE_STATUS_FILENAME = "session_status.json"
BROKER_ORDER_APPROVAL_FILENAME = "approval.json"
BROKER_PRE_SUBMIT_BUNDLE_FILENAME = "broker_pre_submit_bundle.json"
BROKER_SUBMIT_GATE_FILENAME = "broker_submit_gate.json"
BROKER_SUBMIT_ATTEMPT_FILENAME = "broker_submit_attempt.json"
BROKER_SUBMIT_RESPONSE_FILENAME = "broker_submit_response.json"
BROKER_ORDER_STATUS_FILENAME = "broker_order_status.json"
HYPERLIQUID_SIGNED_ACTION_FILENAME = "hyperliquid_signed_action.json"
HYPERLIQUID_SUBMIT_RESPONSE_FILENAME = "hyperliquid_submit_response.json"
HYPERLIQUID_SUBMIT_METADATA_FILENAME = "session_metadata.json"
HYPERLIQUID_SUBMIT_STATUS_FILENAME = "session_status.json"
HYPERLIQUID_ORDER_STATUS_FILENAME = "hyperliquid_order_status.json"
HYPERLIQUID_RECONCILIATION_FILENAME = "hyperliquid_reconciliation.json"
HYPERLIQUID_CANCEL_RESPONSE_FILENAME = "hyperliquid_cancel_response.json"


class BrokerDryRunStore:
    """
    Manage the directory structure and core artifacts for a broker dry-run session.
    """

    def __init__(self, session_id: str, base_dir: str = "outputs/broker_dry_runs"):
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_path = self.base_dir / session_id

    def initialize(self) -> Path:
        self.session_path.mkdir(parents=True, exist_ok=True)
        return self.session_path

    def _ensure_initialized(self) -> None:
        self.session_path.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(metadata)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / BROKER_DRY_RUN_METADATA_FILENAME)

    def write_status(self, status: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(status)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / BROKER_DRY_RUN_STATUS_FILENAME)

    def write_audit(self, audit: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(audit, self.session_path / BROKER_DRY_RUN_AUDIT_FILENAME)

    def get_session_path(self) -> Path:
        return self.session_path.resolve()


class BrokerOrderValidationStore:
    """
    Manage the directory structure and core artifacts for a broker order-validation session.
    """

    def __init__(self, session_id: str, base_dir: str = "outputs/broker_order_validations"):
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_path = self.base_dir / session_id

    def initialize(self) -> Path:
        self.session_path.mkdir(parents=True, exist_ok=True)
        return self.session_path

    def _ensure_initialized(self) -> None:
        self.session_path.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(metadata)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / BROKER_ORDER_VALIDATE_METADATA_FILENAME)

    def write_status(self, status: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(status)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / BROKER_ORDER_VALIDATE_STATUS_FILENAME)

    def write_report(self, report: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(report, self.session_path / BROKER_ORDER_VALIDATE_FILENAME)

    def write_approval(self, approval: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(approval, self.session_path / BROKER_ORDER_APPROVAL_FILENAME)

    def write_pre_submit_bundle(self, bundle: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(bundle, self.session_path / BROKER_PRE_SUBMIT_BUNDLE_FILENAME)

    def write_submit_gate(self, gate: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(gate, self.session_path / BROKER_SUBMIT_GATE_FILENAME)

    def write_submit_attempt(self, attempt: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(attempt, self.session_path / BROKER_SUBMIT_ATTEMPT_FILENAME)

    def write_submit_response(self, response: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(response, self.session_path / BROKER_SUBMIT_RESPONSE_FILENAME)

    def write_order_status(self, order_status: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(order_status, self.session_path / BROKER_ORDER_STATUS_FILENAME)

    def get_session_path(self) -> Path:
        return self.session_path.resolve()


class HyperliquidSubmitStore:
    """
    Manage the directory structure and core artifacts for a Hyperliquid submit session.
    """

    def __init__(self, session_id: str, base_dir: str = "outputs/hyperliquid_submits"):
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_path = self.base_dir / session_id

    def initialize(self) -> Path:
        self.session_path.mkdir(parents=True, exist_ok=True)
        return self.session_path

    def _ensure_initialized(self) -> None:
        self.session_path.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(metadata)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / HYPERLIQUID_SUBMIT_METADATA_FILENAME)

    def write_status(self, status: dict[str, Any]) -> None:
        self._ensure_initialized()
        data = dict(status)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / HYPERLIQUID_SUBMIT_STATUS_FILENAME)

    def write_signed_action(self, signed_action: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(signed_action, self.session_path / HYPERLIQUID_SIGNED_ACTION_FILENAME)

    def write_submit_response(self, response: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(response, self.session_path / HYPERLIQUID_SUBMIT_RESPONSE_FILENAME)

    def write_order_status(self, order_status: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(order_status, self.session_path / HYPERLIQUID_ORDER_STATUS_FILENAME)

    def write_reconciliation(self, reconciliation: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(reconciliation, self.session_path / HYPERLIQUID_RECONCILIATION_FILENAME)

    def write_cancel_response(self, cancel_response: dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(cancel_response, self.session_path / HYPERLIQUID_CANCEL_RESPONSE_FILENAME)

    def get_session_path(self) -> Path:
        return self.session_path.resolve()
