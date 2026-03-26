"""
Stage D.0 broker safety boundary.

This module defines the broker-agnostic contract that future dry-run and live
execution work must pass through before any exchange-specific adapter is used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class ExecutionIntent:
    """
    Normalized broker-bound execution intent produced by QuantLab.
    """

    broker_target: str
    symbol: str
    side: str
    quantity: float
    notional: float
    account_id: str | None
    strategy_id: str | None = None
    request_id: str | None = None
    dry_run: bool = True


@dataclass(frozen=True)
class ExecutionPolicy:
    """
    Local safety policy that must approve execution before adapter use.
    """

    kill_switch_active: bool = False
    max_notional_per_order: float | None = None
    allowed_symbols: frozenset[str] = field(default_factory=frozenset)
    require_account_id: bool = True


@dataclass(frozen=True)
class ExecutionContext:
    """
    Optional execution-venue context that sits beside the core execution intent.

    This is intentionally small. It exists so future venue integrations can
    model signer and routing concerns without overloading the strategy-facing
    ``ExecutionIntent`` object.
    """

    execution_account_id: str | None = None
    signer_id: str | None = None
    signer_type: Literal["direct", "api_wallet", "agent_wallet"] = "direct"
    routing_target: Literal["account", "subaccount", "vault"] = "account"
    transport_preference: Literal["rest", "websocket", "either"] = "either"
    expires_after: int | None = None
    nonce_hint: int | None = None


@dataclass(frozen=True)
class ExecutionPreflight:
    """
    Deterministic result of validating an execution intent against local policy.
    """

    allowed: bool
    reasons: tuple[str, ...] = ()


class BrokerAdapter(Protocol):
    """
    Broker-agnostic contract for future exchange-specific adapters.
    """

    adapter_name: str

    def preflight(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
        context: ExecutionContext | None = None,
    ) -> ExecutionPreflight:
        """
        Validate a broker-bound intent before any broker-specific action occurs.
        """

    def build_order_payload(
        self,
        intent: ExecutionIntent,
        context: ExecutionContext | None = None,
    ) -> dict[str, object]:
        """
        Translate a validated execution intent into an exchange-specific payload.
        """


def validate_execution_intent(
    intent: ExecutionIntent,
    policy: ExecutionPolicy,
) -> ExecutionPreflight:
    """
    Validate a broker execution intent against the Stage D.0 local safety policy.
    """
    reasons: list[str] = []

    if policy.kill_switch_active:
        reasons.append("kill_switch_active")

    if not intent.account_id and policy.require_account_id:
        reasons.append("missing_account_id")

    if intent.quantity <= 0:
        reasons.append("non_positive_quantity")

    if intent.notional <= 0:
        reasons.append("non_positive_notional")

    if policy.max_notional_per_order is not None and intent.notional > policy.max_notional_per_order:
        reasons.append("max_notional_exceeded")

    if policy.allowed_symbols and intent.symbol not in policy.allowed_symbols:
        reasons.append("symbol_not_allowed")

    if intent.side not in {"buy", "sell"}:
        reasons.append("unsupported_side")

    return ExecutionPreflight(allowed=not reasons, reasons=tuple(reasons))
