"""
Stage D.1 Kraken dry-run adapter.

This module validates that the broker boundary can support a first concrete
backend without sending real broker requests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import datetime as dt

from .boundary import (
    BrokerAdapter,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)


@dataclass(frozen=True)
class KrakenDryRunAudit:
    adapter_name: str
    generated_at: str
    preflight: ExecutionPreflight
    intent: ExecutionIntent
    policy: ExecutionPolicy
    payload: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.kraken.dry_run_audit",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "preflight": {
                "allowed": self.preflight.allowed,
                "reasons": list(self.preflight.reasons),
            },
            "intent": asdict(self.intent),
            "policy": {
                "kill_switch_active": self.policy.kill_switch_active,
                "max_notional_per_order": self.policy.max_notional_per_order,
                "allowed_symbols": sorted(self.policy.allowed_symbols),
                "require_account_id": self.policy.require_account_id,
            },
            "payload": self.payload,
        }


class KrakenBrokerAdapter(BrokerAdapter):
    """
    First dry-run broker adapter target for QuantLab.
    """

    adapter_name = "kraken"

    def preflight(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
    ) -> ExecutionPreflight:
        return validate_execution_intent(intent, policy)

    def build_order_payload(self, intent: ExecutionIntent) -> dict[str, object]:
        side = intent.side.lower()
        ordertype = "market"

        return {
            "pair": _normalize_kraken_pair(intent.symbol),
            "type": side,
            "ordertype": ordertype,
            "volume": _format_quantity(intent.quantity),
            "oflags": "post" if ordertype == "limit" else None,
            "dry_run": intent.dry_run,
            "request_id": intent.request_id,
            "strategy_id": intent.strategy_id,
            "account_id": intent.account_id,
            "notional": intent.notional,
        }

    def build_dry_run_audit(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
    ) -> KrakenDryRunAudit:
        preflight = self.preflight(intent, policy)
        payload = self.build_order_payload(intent) if preflight.allowed else None
        return KrakenDryRunAudit(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            preflight=preflight,
            intent=intent,
            policy=policy,
            payload=payload,
        )


def _normalize_kraken_pair(symbol: str) -> str:
    normalized = symbol.strip().upper().replace("-", "/")
    return normalized


def _format_quantity(quantity: float) -> str:
    return f"{quantity:.8f}".rstrip("0").rstrip(".")
