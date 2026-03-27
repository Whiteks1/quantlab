"""
Stage D.1.b Hyperliquid read-only venue preflight.

This module keeps the first Hyperliquid slice intentionally read-only. It
resolves execution-context semantics and checks venue metadata without placing
or validating live orders.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import time
from urllib.request import Request, urlopen

try:
    import msgpack
    from eth_account import Account
    from eth_account.messages import encode_typed_data
    from eth_utils import keccak, to_hex
except ImportError:  # pragma: no cover - exercised via fallback behavior.
    msgpack = None
    Account = None
    encode_typed_data = None
    keccak = None
    to_hex = None

from .boundary import (
    BrokerAdapter,
    ExecutionContext,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)

HYPERLIQUID_INFO_API_URL = "https://api.hyperliquid.xyz/info"
HYPERLIQUID_EXCHANGE_API_URL = "https://api.hyperliquid.xyz/exchange"
HYPERLIQUID_MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
_SPOT_SYMBOL_ALIASES = {
    "BTC/USDC": "UBTC/USDC",
}


@dataclass(frozen=True)
class HyperliquidResolvedExecutionContext:
    execution_account_id: str | None
    query_user: str | None
    signer_id: str | None
    signer_type: str
    routing_target: str
    transport_preference: str
    resolved_transport: str
    expires_after: int | None
    nonce_scope: str | None
    query_address_matches_signer: bool | None
    execution_account_role: str | None
    signer_role: str | None
    context_ready: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "execution_account_id": self.execution_account_id,
            "query_user": self.query_user,
            "signer_id": self.signer_id,
            "signer_type": self.signer_type,
            "routing_target": self.routing_target,
            "transport_preference": self.transport_preference,
            "resolved_transport": self.resolved_transport,
            "expires_after": self.expires_after,
            "nonce_scope": self.nonce_scope,
            "query_address_matches_signer": self.query_address_matches_signer,
            "execution_account_role": self.execution_account_role,
            "signer_role": self.signer_role,
            "context_ready": self.context_ready,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class HyperliquidPreflightReport:
    adapter_name: str
    generated_at: str
    symbol_input: str
    normalized_symbol: str
    market_type: str
    metadata_type: str
    public_api_reachable: bool
    market_supported: bool
    matched_name: str | None
    resolved_coin: str | None
    resolved_asset: int | None
    mid_price: str | None
    rest_info_url: str
    websocket_url: str
    execution_context: HyperliquidResolvedExecutionContext
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.preflight",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "symbol_input": self.symbol_input,
            "normalized_symbol": self.normalized_symbol,
            "market_type": self.market_type,
            "metadata_type": self.metadata_type,
            "public_api_reachable": self.public_api_reachable,
            "market_supported": self.market_supported,
            "matched_name": self.matched_name,
            "resolved_coin": self.resolved_coin,
            "resolved_asset": self.resolved_asset,
            "mid_price": self.mid_price,
            "rest_info_url": self.rest_info_url,
            "websocket_url": self.websocket_url,
            "execution_context": self.execution_context.to_dict(),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidAccountReadinessReport:
    adapter_name: str
    generated_at: str
    execution_context: HyperliquidResolvedExecutionContext
    account_visibility_available: bool
    open_orders_count: int | None
    frontend_open_orders_count: int | None
    open_orders_sample: tuple[dict[str, object], ...]
    frontend_open_orders_sample: tuple[dict[str, object], ...]
    readiness_allowed: bool
    readiness_reasons: tuple[str, ...]
    rest_info_url: str
    websocket_url: str
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.account_readiness",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "execution_context": self.execution_context.to_dict(),
            "account_visibility_available": self.account_visibility_available,
            "open_orders_count": self.open_orders_count,
            "frontend_open_orders_count": self.frontend_open_orders_count,
            "open_orders_sample": list(self.open_orders_sample),
            "frontend_open_orders_sample": list(self.frontend_open_orders_sample),
            "readiness_allowed": self.readiness_allowed,
            "readiness_reasons": list(self.readiness_reasons),
            "rest_info_url": self.rest_info_url,
            "websocket_url": self.websocket_url,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidSignedActionReport:
    adapter_name: str
    generated_at: str
    intent: ExecutionIntent
    policy: ExecutionPolicy
    local_preflight: ExecutionPreflight
    public_preflight: HyperliquidPreflightReport
    account_readiness: HyperliquidAccountReadinessReport
    nonce: int
    nonce_source: str
    expires_after: int | None
    expires_after_mode: str | None
    signature_envelope: dict[str, object]
    action_payload: dict[str, object] | None
    readiness_allowed: bool
    readiness_reasons: tuple[str, ...]
    signer_backend: str | None = None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.signed_action",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "intent": {
                "broker_target": self.intent.broker_target,
                "symbol": self.intent.symbol,
                "side": self.intent.side,
                "quantity": self.intent.quantity,
                "notional": self.intent.notional,
                "account_id": self.intent.account_id,
                "strategy_id": self.intent.strategy_id,
                "request_id": self.intent.request_id,
                "dry_run": self.intent.dry_run,
            },
            "policy": {
                "kill_switch_active": self.policy.kill_switch_active,
                "max_notional_per_order": self.policy.max_notional_per_order,
                "allowed_symbols": sorted(self.policy.allowed_symbols),
                "require_account_id": self.policy.require_account_id,
            },
            "local_preflight": {
                "allowed": self.local_preflight.allowed,
                "reasons": list(self.local_preflight.reasons),
            },
            "public_preflight": self.public_preflight.to_dict(),
            "account_readiness": self.account_readiness.to_dict(),
            "nonce": self.nonce,
            "nonce_source": self.nonce_source,
            "expires_after": self.expires_after,
            "expires_after_mode": self.expires_after_mode,
            "signature_envelope": self.signature_envelope,
            "action_payload": self.action_payload,
            "readiness_allowed": self.readiness_allowed,
            "readiness_reasons": list(self.readiness_reasons),
            "signer_backend": self.signer_backend,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidSubmitReport:
    adapter_name: str
    generated_at: str
    source_artifact_path: str
    source_action_hash: str | None
    source_signer_id: str | None
    source_signing_payload_sha256: str | None
    submit_payload: dict[str, object] | None
    submit_state: str
    remote_submit_called: bool
    submitted: bool
    response_type: str | None
    oid: int | None
    cloid: str | None
    exchange_response: dict[str, object] | None
    reviewer: str
    note: str | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.submit_response",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "source_artifact_path": self.source_artifact_path,
            "source_action_hash": self.source_action_hash,
            "source_signer_id": self.source_signer_id,
            "source_signing_payload_sha256": self.source_signing_payload_sha256,
            "submit_payload": self.submit_payload,
            "submit_state": self.submit_state,
            "remote_submit_called": self.remote_submit_called,
            "submitted": self.submitted,
            "response_type": self.response_type,
            "oid": self.oid,
            "cloid": self.cloid,
            "exchange_response": self.exchange_response,
            "reviewer": self.reviewer,
            "note": self.note,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidCancelReport:
    adapter_name: str
    generated_at: str
    source_session_id: str
    source_action_hash: str | None
    source_signer_id: str | None
    source_signing_payload_sha256: str | None
    source_submit_state: str | None
    cancel_payload: dict[str, object] | None
    cancel_state: str
    remote_cancel_called: bool
    cancel_accepted: bool
    response_type: str | None
    asset: int | None
    oid: int | None
    cloid: str | None
    exchange_response: dict[str, object] | None
    reviewer: str
    note: str | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.cancel_response",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "source_session_id": self.source_session_id,
            "source_action_hash": self.source_action_hash,
            "source_signer_id": self.source_signer_id,
            "source_signing_payload_sha256": self.source_signing_payload_sha256,
            "source_submit_state": self.source_submit_state,
            "cancel_payload": self.cancel_payload,
            "cancel_state": self.cancel_state,
            "remote_cancel_called": self.remote_cancel_called,
            "cancel_accepted": self.cancel_accepted,
            "response_type": self.response_type,
            "asset": self.asset,
            "oid": self.oid,
            "cloid": self.cloid,
            "exchange_response": self.exchange_response,
            "reviewer": self.reviewer,
            "note": self.note,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidOrderStatusReport:
    adapter_name: str
    generated_at: str
    source_session_id: str
    execution_account_id: str | None
    query_mode: str | None
    query_identifier: str | None
    query_attempted: bool
    status_known: bool
    normalized_state: str | None
    raw_status: str | None
    oid: int | None
    cloid: str | None
    order_status: dict[str, object] | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.order_status",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "source_session_id": self.source_session_id,
            "execution_account_id": self.execution_account_id,
            "query_mode": self.query_mode,
            "query_identifier": self.query_identifier,
            "query_attempted": self.query_attempted,
            "status_known": self.status_known,
            "normalized_state": self.normalized_state,
            "raw_status": self.raw_status,
            "oid": self.oid,
            "cloid": self.cloid,
            "order_status": self.order_status,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidReconciliationReport:
    adapter_name: str
    generated_at: str
    source_session_id: str
    execution_account_id: str | None
    status_known: bool
    normalized_state: str | None
    close_state: str | None
    fill_state: str | None
    resolution_source: str | None
    oid: int | None
    cloid: str | None
    original_size: str | None
    filled_size: str | None
    remaining_size: str | None
    fill_count: int
    average_fill_price: str | None
    last_fill_time: int | None
    order_status_report: dict[str, object] | None
    matched_open_order: dict[str, object] | None
    matched_frontend_open_order: dict[str, object] | None
    matched_historical_order: dict[str, object] | None
    matched_fill_sample: tuple[dict[str, object], ...]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.reconciliation",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "source_session_id": self.source_session_id,
            "execution_account_id": self.execution_account_id,
            "status_known": self.status_known,
            "normalized_state": self.normalized_state,
            "close_state": self.close_state,
            "fill_state": self.fill_state,
            "resolution_source": self.resolution_source,
            "oid": self.oid,
            "cloid": self.cloid,
            "original_size": self.original_size,
            "filled_size": self.filled_size,
            "remaining_size": self.remaining_size,
            "fill_count": self.fill_count,
            "average_fill_price": self.average_fill_price,
            "last_fill_time": self.last_fill_time,
            "order_status_report": self.order_status_report,
            "matched_open_order": self.matched_open_order,
            "matched_frontend_open_order": self.matched_frontend_open_order,
            "matched_historical_order": self.matched_historical_order,
            "matched_fill_sample": list(self.matched_fill_sample),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class HyperliquidFillSummaryReport:
    adapter_name: str
    generated_at: str
    source_session_id: str
    execution_account_id: str | None
    fills_known: bool
    query_attempted: bool
    oid: int | None
    cloid: str | None
    fill_state: str | None
    original_size: str | None
    filled_size: str | None
    remaining_size: str | None
    fill_count: int
    average_fill_price: str | None
    total_fee: str | None
    total_builder_fee: str | None
    total_closed_pnl: str | None
    first_fill_time: int | None
    last_fill_time: int | None
    matched_fill_sample: tuple[dict[str, object], ...]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.hyperliquid.fill_summary",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "source_session_id": self.source_session_id,
            "execution_account_id": self.execution_account_id,
            "fills_known": self.fills_known,
            "query_attempted": self.query_attempted,
            "oid": self.oid,
            "cloid": self.cloid,
            "fill_state": self.fill_state,
            "original_size": self.original_size,
            "filled_size": self.filled_size,
            "remaining_size": self.remaining_size,
            "fill_count": self.fill_count,
            "average_fill_price": self.average_fill_price,
            "total_fee": self.total_fee,
            "total_builder_fee": self.total_builder_fee,
            "total_closed_pnl": self.total_closed_pnl,
            "first_fill_time": self.first_fill_time,
            "last_fill_time": self.last_fill_time,
            "matched_fill_sample": list(self.matched_fill_sample),
            "errors": list(self.errors),
        }


class HyperliquidBrokerAdapter(BrokerAdapter):
    """
    Read-only Hyperliquid venue adapter for preflight and context resolution.
    """

    adapter_name = "hyperliquid"

    def preflight(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
        context: ExecutionContext | None = None,
    ) -> ExecutionPreflight:
        base = validate_execution_intent(intent, policy)
        context_result = self.resolve_execution_context(
            intent_account_id=intent.account_id,
            context=context,
        )
        reasons = list(base.reasons)
        if not context_result.context_ready:
            reasons.extend(context_result.reasons)
        return ExecutionPreflight(allowed=not reasons, reasons=tuple(_unique_reasons(reasons)))

    def build_order_payload(
        self,
        intent: ExecutionIntent,
        context: ExecutionContext | None = None,
    ) -> dict[str, object]:
        resolved_context = self.resolve_execution_context(
            intent_account_id=intent.account_id,
            context=context,
        )
        return {
            "asset": _normalize_hyperliquid_symbol(intent.symbol),
            "side": intent.side.upper(),
            "quantity": intent.quantity,
            "notional": intent.notional,
            "execution_context": resolved_context.to_dict(),
        }

    def resolve_execution_context(
        self,
        *,
        intent_account_id: str | None = None,
        context: ExecutionContext | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidResolvedExecutionContext:
        context = context or ExecutionContext()
        execution_account_id = context.execution_account_id or intent_account_id
        query_user = execution_account_id
        signer_id = context.signer_id or execution_account_id
        resolved_transport = (
            "websocket" if context.transport_preference in {"either", "websocket"} else "rest"
        )

        reasons: list[str] = []
        execution_account_role = None
        signer_role = None

        if context.routing_target in {"subaccount", "vault"} and not execution_account_id:
            reasons.append("missing_execution_account_id")
        if context.signer_type in {"api_wallet", "agent_wallet"} and not execution_account_id:
            reasons.append("missing_execution_account_id")
        if context.signer_type in {"api_wallet", "agent_wallet"} and not signer_id:
            reasons.append("missing_signer_id")
        if query_user and not _is_hex_address(query_user):
            reasons.append("invalid_execution_account_id")
        if signer_id and not _is_hex_address(signer_id):
            reasons.append("invalid_signer_id")
        if context.expires_after is not None and context.expires_after <= 0:
            reasons.append("non_positive_expires_after")
        if context.nonce_hint is not None and context.nonce_hint <= 0:
            reasons.append("non_positive_nonce_hint")

        if query_user and _is_hex_address(query_user):
            try:
                execution_account_role = fetch_hyperliquid_user_role(
                    query_user,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"execution_account_role_probe_failed:{exc.__class__.__name__}")

        if signer_id and _is_hex_address(signer_id) and signer_id != query_user:
            try:
                signer_role = fetch_hyperliquid_user_role(
                    signer_id,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"signer_role_probe_failed:{exc.__class__.__name__}")
        elif signer_id == query_user:
            signer_role = execution_account_role

        return HyperliquidResolvedExecutionContext(
            execution_account_id=execution_account_id,
            query_user=query_user,
            signer_id=signer_id,
            signer_type=context.signer_type,
            routing_target=context.routing_target,
            transport_preference=context.transport_preference,
            resolved_transport=resolved_transport,
            expires_after=context.expires_after,
            nonce_scope=signer_id,
            query_address_matches_signer=(query_user == signer_id) if query_user and signer_id else None,
            execution_account_role=execution_account_role,
            signer_role=signer_role,
            context_ready=not reasons,
            reasons=tuple(_unique_reasons(reasons)),
        )

    def build_public_preflight_report(
        self,
        symbol: str,
        *,
        intent_account_id: str | None = None,
        context: ExecutionContext | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidPreflightReport:
        normalized_symbol = _normalize_hyperliquid_symbol(symbol)
        market_type = "spot" if "/" in normalized_symbol else "perp"
        metadata_type = "spotMeta" if market_type == "spot" else "meta"
        errors: list[str] = []
        public_api_reachable = False
        market_supported = False
        matched_name = None
        resolved_coin = None
        resolved_asset = None
        mid_price = None

        resolved_context = self.resolve_execution_context(
            intent_account_id=intent_account_id,
            context=context,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        errors.extend(resolved_context.reasons)

        try:
            all_mids = fetch_hyperliquid_all_mids(
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
            )
            public_api_reachable = True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"all_mids_probe_failed:{exc.__class__.__name__}")
            all_mids = {}

        try:
            if market_type == "spot":
                market = fetch_hyperliquid_spot_market(
                    normalized_symbol,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
            else:
                market = fetch_hyperliquid_perp_market(
                    normalized_symbol,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
            public_api_reachable = True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"market_meta_probe_failed:{exc.__class__.__name__}")
            market = None

        if market is not None:
            market_supported = True
            matched_name = market["matched_name"]
            resolved_coin = market["resolved_coin"]
            resolved_asset = market["resolved_asset"]
            if resolved_coin and isinstance(all_mids, dict):
                mid_price = all_mids.get(resolved_coin)
        else:
            errors.append("market_not_supported")

        return HyperliquidPreflightReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            symbol_input=symbol,
            normalized_symbol=normalized_symbol,
            market_type=market_type,
            metadata_type=metadata_type,
            public_api_reachable=public_api_reachable,
            market_supported=market_supported,
            matched_name=matched_name,
            resolved_coin=resolved_coin,
            resolved_asset=resolved_asset,
            mid_price=mid_price,
            rest_info_url=HYPERLIQUID_INFO_API_URL,
            websocket_url=HYPERLIQUID_MAINNET_WS_URL,
            execution_context=resolved_context,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_signed_action_report(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
        *,
        context: ExecutionContext | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
        now_ms: int | None = None,
        signing_private_key: str | None = None,
        signing_private_key_env: str = "HYPERLIQUID_PRIVATE_KEY",
    ) -> HyperliquidSignedActionReport:
        local_preflight = self.preflight(intent, policy, context=context)
        public_preflight = self.build_public_preflight_report(
            intent.symbol,
            intent_account_id=intent.account_id,
            context=context,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        account_readiness = self.build_account_readiness_report(
            intent_account_id=intent.account_id,
            context=context,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )

        resolved_context = account_readiness.execution_context
        nonce, nonce_source = _resolve_hyperliquid_nonce(context=context, now_ms=now_ms)
        expires_after, expires_after_mode = _resolve_expires_after(context=context, nonce=nonce)

        readiness_reasons: list[str] = list(local_preflight.reasons)
        if not public_preflight.market_supported:
            readiness_reasons.append("market_not_supported")
        readiness_reasons.extend(account_readiness.readiness_reasons)
        if not resolved_context.signer_id:
            readiness_reasons.append("missing_signer_id")
        if not resolved_context.nonce_scope:
            readiness_reasons.append("missing_nonce_scope")

        action_payload = None
        if not readiness_reasons:
            action_payload = self.build_order_action_payload(
                intent,
                public_preflight=public_preflight,
            )

        signer_backend = None
        signature_envelope = self.build_signature_envelope(
            action_payload=action_payload,
            resolved_context=resolved_context,
            nonce=nonce,
            expires_after=expires_after,
        )
        errors = list(account_readiness.errors)
        if action_payload is None:
            errors.append("action_payload_not_ready")
        else:
            signer_backend = "local_private_key"
            signer_result = self.apply_signing_backend(
                signature_envelope=signature_envelope,
                resolved_context=resolved_context,
                signing_private_key=signing_private_key,
                signing_private_key_env=signing_private_key_env,
            )
            signature_envelope = signer_result["signature_envelope"]
            if signer_result["signer_backend"]:
                signer_backend = signer_result["signer_backend"]
            errors.extend(signer_result["errors"])
            readiness_reasons.extend(signer_result["readiness_reasons"])

        return HyperliquidSignedActionReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            intent=intent,
            policy=policy,
            local_preflight=local_preflight,
            public_preflight=public_preflight,
            account_readiness=account_readiness,
            nonce=nonce,
            nonce_source=nonce_source,
            expires_after=expires_after,
            expires_after_mode=expires_after_mode,
            signature_envelope=signature_envelope,
            action_payload=action_payload,
            readiness_allowed=not readiness_reasons,
            readiness_reasons=tuple(_unique_reasons(readiness_reasons)),
            signer_backend=signer_backend,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_order_action_payload(
        self,
        intent: ExecutionIntent,
        *,
        public_preflight: HyperliquidPreflightReport,
    ) -> dict[str, object]:
        if public_preflight.resolved_asset is None:
            raise ValueError("resolved_asset is required for Hyperliquid order action payload")

        order = {
            "a": public_preflight.resolved_asset,
            "b": intent.side.lower() == "buy",
            "p": str(public_preflight.mid_price or "0"),
            "s": _format_hyperliquid_size(intent.quantity),
            "r": False,
            "t": {"limit": {"tif": "Ioc"}},
        }
        if intent.request_id:
            order["c"] = _build_hyperliquid_cloid(intent.request_id)

        return {
            "type": "order",
            "orders": [order],
            "grouping": "na",
        }

    def build_signature_envelope(
        self,
        *,
        action_payload: dict[str, object] | None,
        resolved_context: HyperliquidResolvedExecutionContext,
        nonce: int,
        expires_after: int | None,
    ) -> dict[str, object]:
        signing_payload = {
            "action": action_payload,
            "nonce": nonce,
            "vaultAddress": (
                resolved_context.execution_account_id
                if resolved_context.routing_target in {"subaccount", "vault"}
                and resolved_context.execution_account_id
                and resolved_context.execution_account_id != resolved_context.signer_id
                else None
            ),
            "expiresAfter": expires_after,
        }
        canonical = json.dumps(signing_payload, sort_keys=True, separators=(",", ":"))
        return {
            "signer_id": resolved_context.signer_id,
            "nonce_scope": resolved_context.nonce_scope,
            "signing_scheme": "hyperliquid_l1_action",
            "signature_state": "pending_signer_backend",
            "signature_present": False,
            "signature_reason": "signature_backend_not_implemented",
            "signing_payload": signing_payload,
            "signing_payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "action_hash": None,
            "phantom_agent": None,
            "signature": None,
            "derived_signer_address": None,
        }

    def apply_signing_backend(
        self,
        *,
        signature_envelope: dict[str, object],
        resolved_context: HyperliquidResolvedExecutionContext,
        signing_private_key: str | None = None,
        signing_private_key_env: str = "HYPERLIQUID_PRIVATE_KEY",
        is_mainnet: bool = True,
    ) -> dict[str, object]:
        envelope = dict(signature_envelope)
        readiness_reasons: list[str] = []
        errors: list[str] = []
        signer_backend = None

        private_key, private_key_source = _load_hyperliquid_private_key(
            explicit_value=signing_private_key,
            env_name=signing_private_key_env,
        )
        if not private_key:
            envelope["signature_state"] = "pending_signer_backend"
            envelope["signature_reason"] = "missing_signing_key"
            return {
                "signature_envelope": envelope,
                "readiness_reasons": readiness_reasons,
                "errors": errors,
                "signer_backend": signer_backend,
            }

        signer_backend = "hyperliquid_local_private_key"
        envelope["private_key_source"] = private_key_source

        if not _hyperliquid_signing_dependencies_available():
            envelope["signature_state"] = "signer_backend_unavailable"
            envelope["signature_reason"] = "signing_dependencies_missing"
            readiness_reasons.append("signing_dependencies_missing")
            errors.append("signing_dependencies_missing")
            return {
                "signature_envelope": envelope,
                "readiness_reasons": readiness_reasons,
                "errors": errors,
                "signer_backend": signer_backend,
            }

        try:
            signed = sign_hyperliquid_l1_action(
                private_key=private_key,
                action_payload=envelope.get("signing_payload", {}).get("action"),
                vault_address=envelope.get("signing_payload", {}).get("vaultAddress"),
                nonce=int(envelope.get("signing_payload", {}).get("nonce")),
                expires_after=envelope.get("signing_payload", {}).get("expiresAfter"),
                is_mainnet=is_mainnet,
            )
        except Exception as exc:  # noqa: BLE001
            envelope["signature_state"] = "signer_backend_error"
            envelope["signature_reason"] = f"{exc.__class__.__name__}"
            errors.append(f"signing_backend_failed:{exc.__class__.__name__}")
            readiness_reasons.append("signing_backend_failed")
            return {
                "signature_envelope": envelope,
                "readiness_reasons": readiness_reasons,
                "errors": errors,
                "signer_backend": signer_backend,
            }

        expected_signer = resolved_context.signer_id.lower() if resolved_context.signer_id else None
        derived_signer = signed["signer_address"].lower()
        if expected_signer and expected_signer != derived_signer:
            envelope["signature_state"] = "signer_identity_mismatch"
            envelope["signature_reason"] = "derived_signer_address_mismatch"
            envelope["derived_signer_address"] = signed["signer_address"]
            envelope["action_hash"] = signed["action_hash"]
            envelope["phantom_agent"] = signed["phantom_agent"]
            readiness_reasons.append("signer_identity_mismatch")
            errors.append("signer_identity_mismatch")
            return {
                "signature_envelope": envelope,
                "readiness_reasons": readiness_reasons,
                "errors": errors,
                "signer_backend": signer_backend,
            }

        envelope["signature_state"] = "signed"
        envelope["signature_present"] = True
        envelope["signature_reason"] = None
        envelope["derived_signer_address"] = signed["signer_address"]
        envelope["action_hash"] = signed["action_hash"]
        envelope["phantom_agent"] = signed["phantom_agent"]
        envelope["signature"] = signed["signature"]
        envelope["eip712_payload"] = signed["eip712_payload"]
        return {
            "signature_envelope": envelope,
            "readiness_reasons": readiness_reasons,
            "errors": errors,
            "signer_backend": signer_backend,
        }

    def build_account_readiness_report(
        self,
        *,
        intent_account_id: str | None = None,
        context: ExecutionContext | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidAccountReadinessReport:
        resolved_context = self.resolve_execution_context(
            intent_account_id=intent_account_id,
            context=context,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        readiness_reasons: list[str] = list(resolved_context.reasons)
        errors: list[str] = list(resolved_context.reasons)
        account_visibility_available = False
        open_orders_count = None
        frontend_open_orders_count = None
        open_orders_sample: tuple[dict[str, object], ...] = ()
        frontend_open_orders_sample: tuple[dict[str, object], ...] = ()

        if not resolved_context.query_user:
            readiness_reasons.append("missing_execution_account_id")
        elif not _is_hex_address(resolved_context.query_user):
            readiness_reasons.append("invalid_execution_account_id")
        else:
            try:
                open_orders = fetch_hyperliquid_open_orders(
                    resolved_context.query_user,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
                frontend_open_orders = fetch_hyperliquid_frontend_open_orders(
                    resolved_context.query_user,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
                account_visibility_available = True
                open_orders_count = len(open_orders)
                frontend_open_orders_count = len(frontend_open_orders)
                open_orders_sample = tuple(open_orders[:5])
                frontend_open_orders_sample = tuple(frontend_open_orders[:5])
            except Exception as exc:  # noqa: BLE001
                failure_reason = f"account_visibility_probe_failed:{exc.__class__.__name__}"
                readiness_reasons.append("account_visibility_unavailable")
                errors.append(failure_reason)

        if resolved_context.execution_account_role == "missing":
            readiness_reasons.append("execution_account_missing")

        if resolved_context.signer_type in {"api_wallet", "agent_wallet"}:
            if resolved_context.signer_role is None:
                readiness_reasons.append("signer_role_unknown")
            elif resolved_context.signer_role != "agent":
                readiness_reasons.append("signer_role_mismatch")

        if resolved_context.routing_target == "subaccount" and resolved_context.execution_account_role not in {
            None,
            "subAccount",
        }:
            readiness_reasons.append("execution_account_not_subaccount")

        if resolved_context.routing_target == "vault" and resolved_context.execution_account_role not in {
            None,
            "vault",
        }:
            readiness_reasons.append("execution_account_not_vault")

        return HyperliquidAccountReadinessReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            execution_context=resolved_context,
            account_visibility_available=account_visibility_available,
            open_orders_count=open_orders_count,
            frontend_open_orders_count=frontend_open_orders_count,
            open_orders_sample=open_orders_sample,
            frontend_open_orders_sample=frontend_open_orders_sample,
            readiness_allowed=not readiness_reasons,
            readiness_reasons=tuple(_unique_reasons(readiness_reasons)),
            rest_info_url=HYPERLIQUID_INFO_API_URL,
            websocket_url=HYPERLIQUID_MAINNET_WS_URL,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_submit_report(
        self,
        *,
        source_artifact_path: str,
        signed_action_artifact: dict[str, object],
        reviewer: str,
        note: str | None = None,
        timeout_seconds: float = 10.0,
        post_json=None,
        remote_submit: bool = True,
    ) -> HyperliquidSubmitReport:
        errors: list[str] = []
        submit_payload = None
        exchange_response: dict[str, object] | None = None
        response_type = None
        remote_submit_called = False
        submitted = False
        submit_state = "submit_not_ready"

        if not isinstance(signed_action_artifact, dict):
            errors.append("invalid_signed_action_artifact")
            return HyperliquidSubmitReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_artifact_path=source_artifact_path,
                source_action_hash=None,
                source_signer_id=None,
                source_signing_payload_sha256=None,
                submit_payload=None,
                submit_state="invalid_signed_action_artifact",
                remote_submit_called=False,
                submitted=False,
                response_type=None,
                oid=None,
                cloid=None,
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=tuple(_unique_reasons(errors)),
            )

        submit_payload = _build_hyperliquid_submit_payload(signed_action_artifact)
        source_envelope = signed_action_artifact.get("signature_envelope", {})

        if signed_action_artifact.get("artifact_type") != "quantlab.hyperliquid.signed_action":
            errors.append("unexpected_signed_action_artifact_type")
        if not bool(signed_action_artifact.get("readiness_allowed")):
            errors.append("signed_action_not_ready")
        if not isinstance(source_envelope, dict):
            errors.append("missing_signature_envelope")
        else:
            if source_envelope.get("signature_state") != "signed":
                errors.append("signed_action_not_signed")
            if not bool(source_envelope.get("signature_present")):
                errors.append("signature_missing")
        if not isinstance(submit_payload, dict):
            errors.append("submit_payload_unavailable")

        if errors:
            submit_state = errors[0]
            return HyperliquidSubmitReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_artifact_path=source_artifact_path,
                source_action_hash=_safe_string(source_envelope.get("action_hash")),
                source_signer_id=_safe_string(source_envelope.get("signer_id")),
                source_signing_payload_sha256=_safe_string(source_envelope.get("signing_payload_sha256")),
                submit_payload=submit_payload,
                submit_state=submit_state,
                remote_submit_called=False,
                submitted=False,
                response_type=None,
                oid=None,
                cloid=_extract_hyperliquid_submit_cloid(signed_action_artifact),
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=tuple(_unique_reasons(errors)),
            )

        if not remote_submit:
            return HyperliquidSubmitReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_artifact_path=source_artifact_path,
                source_action_hash=_safe_string(source_envelope.get("action_hash")),
                source_signer_id=_safe_string(source_envelope.get("signer_id")),
                source_signing_payload_sha256=_safe_string(source_envelope.get("signing_payload_sha256")),
                submit_payload=submit_payload,
                submit_state="pending_remote_submit",
                remote_submit_called=False,
                submitted=False,
                response_type=None,
                oid=None,
                cloid=_extract_hyperliquid_submit_cloid(signed_action_artifact),
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=(),
            )

        try:
            exchange_response = fetch_hyperliquid_exchange(
                submit_payload,
                timeout_seconds=timeout_seconds,
                post_json=post_json,
            )
            remote_submit_called = True
            response_type = _extract_hyperliquid_response_type(exchange_response)
            submitted, response_errors = _classify_hyperliquid_submit_response(exchange_response)
            errors.extend(response_errors)
            submit_state = "submitted_remote" if submitted else "submit_rejected"
        except Exception as exc:  # noqa: BLE001
            remote_submit_called = True
            submit_state = "submit_request_failed"
            errors.append(f"submit_request_failed:{exc.__class__.__name__}")

        return HyperliquidSubmitReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            source_artifact_path=source_artifact_path,
            source_action_hash=_safe_string(source_envelope.get("action_hash")),
            source_signer_id=_safe_string(source_envelope.get("signer_id")),
            source_signing_payload_sha256=_safe_string(source_envelope.get("signing_payload_sha256")),
            submit_payload=submit_payload,
            submit_state=submit_state,
            remote_submit_called=remote_submit_called,
            submitted=submitted,
            response_type=response_type,
            oid=_extract_hyperliquid_submit_oid(exchange_response),
            cloid=_extract_hyperliquid_submit_cloid(signed_action_artifact),
            exchange_response=exchange_response,
            reviewer=reviewer,
            note=note,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_order_status_report(
        self,
        *,
        source_session_id: str,
        execution_account_id: str | None,
        oid: int | None = None,
        cloid: str | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidOrderStatusReport:
        errors: list[str] = []
        query_attempted = False
        raw_status = None
        normalized_state = None
        order_status = None
        status_known = False

        resolved_execution_account = _safe_string(execution_account_id)
        resolved_cloid = _safe_string(cloid)
        resolved_oid = oid if isinstance(oid, int) and oid >= 0 else None

        if not resolved_execution_account:
            errors.append("missing_execution_account_id")
        elif not _is_hex_address(resolved_execution_account):
            errors.append("invalid_execution_account_id")

        query_mode = None
        query_identifier = None
        query_value: int | str | None = None
        if resolved_oid is not None:
            query_mode = "oid"
            query_identifier = str(resolved_oid)
            query_value = resolved_oid
        elif resolved_cloid:
            query_mode = "cloid"
            query_identifier = resolved_cloid
            query_value = resolved_cloid
        else:
            errors.append("missing_order_identifier")

        if errors:
            return HyperliquidOrderStatusReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_session_id=source_session_id,
                execution_account_id=resolved_execution_account,
                query_mode=query_mode,
                query_identifier=query_identifier,
                query_attempted=False,
                status_known=False,
                normalized_state=None,
                raw_status=None,
                oid=resolved_oid,
                cloid=resolved_cloid,
                order_status=None,
                errors=tuple(_unique_reasons(errors)),
            )

        try:
            order_status = fetch_hyperliquid_order_status(
                resolved_execution_account,
                query_value,
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
            )
            query_attempted = True
            raw_status = _extract_hyperliquid_order_status(order_status)
            if raw_status == "missing_order":
                normalized_state = "unknown"
                status_known = False
                errors.append("missing_order")
            elif raw_status is not None:
                normalized_state = _normalize_hyperliquid_order_state(raw_status)
                status_known = True
            else:
                normalized_state = "unknown"
                status_known = False
                errors.append("unknown_order_status_shape")
        except Exception as exc:  # noqa: BLE001
            query_attempted = True
            normalized_state = "unknown"
            errors.append(f"order_status_probe_failed:{exc.__class__.__name__}")

        return HyperliquidOrderStatusReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            source_session_id=source_session_id,
            execution_account_id=resolved_execution_account,
            query_mode=query_mode,
            query_identifier=query_identifier,
            query_attempted=query_attempted,
            status_known=status_known,
            normalized_state=normalized_state,
            raw_status=raw_status,
            oid=resolved_oid,
            cloid=resolved_cloid,
            order_status=order_status,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_cancel_report(
        self,
        *,
        source_session_id: str,
        signed_action_artifact: dict[str, object],
        submit_response_artifact: dict[str, object],
        reviewer: str,
        note: str | None = None,
        timeout_seconds: float = 10.0,
        post_json=None,
        remote_cancel: bool = True,
        signing_private_key: str | None = None,
        signing_private_key_env: str = "HYPERLIQUID_PRIVATE_KEY",
        is_mainnet: bool = True,
    ) -> HyperliquidCancelReport:
        errors: list[str] = []
        cancel_payload = None
        exchange_response: dict[str, object] | None = None
        response_type = None
        remote_cancel_called = False
        cancel_accepted = False
        cancel_state = "cancel_not_ready"

        source_envelope = (
            signed_action_artifact.get("signature_envelope", {}) if isinstance(signed_action_artifact, dict) else {}
        )
        source_action_hash = _safe_string(source_envelope.get("action_hash")) if isinstance(source_envelope, dict) else None
        source_signer_id = _safe_string(source_envelope.get("signer_id")) if isinstance(source_envelope, dict) else None
        source_signing_payload_sha256 = (
            _safe_string(source_envelope.get("signing_payload_sha256")) if isinstance(source_envelope, dict) else None
        )
        source_submit_state = (
            _safe_string(submit_response_artifact.get("submit_state")) if isinstance(submit_response_artifact, dict) else None
        )

        if not isinstance(signed_action_artifact, dict):
            errors.append("invalid_signed_action_artifact")
        if not isinstance(submit_response_artifact, dict):
            errors.append("invalid_submit_response_artifact")

        if isinstance(signed_action_artifact, dict):
            if signed_action_artifact.get("artifact_type") != "quantlab.hyperliquid.signed_action":
                errors.append("unexpected_signed_action_artifact_type")
            if not bool(signed_action_artifact.get("readiness_allowed")):
                errors.append("signed_action_not_ready")
        if isinstance(submit_response_artifact, dict):
            if submit_response_artifact.get("artifact_type") != "quantlab.hyperliquid.submit_response":
                errors.append("unexpected_submit_response_artifact_type")
            if not bool(submit_response_artifact.get("remote_submit_called")):
                errors.append("submit_not_attempted")
            if not bool(submit_response_artifact.get("submitted")):
                errors.append("submit_not_confirmed")

        asset = _extract_hyperliquid_submit_asset(signed_action_artifact) if isinstance(signed_action_artifact, dict) else None
        oid = _extract_hyperliquid_submit_oid(submit_response_artifact) if isinstance(submit_response_artifact, dict) else None
        cloid = (
            _extract_hyperliquid_submit_cloid(signed_action_artifact) if isinstance(signed_action_artifact, dict) else None
        )
        if asset is None:
            errors.append("missing_source_asset")
        if oid is None and not cloid:
            errors.append("missing_order_identifier")

        if not isinstance(source_envelope, dict):
            errors.append("missing_signature_envelope")
        else:
            if source_envelope.get("signature_state") != "signed":
                errors.append("signed_action_not_signed")
            if not bool(source_envelope.get("signature_present")):
                errors.append("signature_missing")

        private_key, private_key_source = _load_hyperliquid_private_key(
            explicit_value=signing_private_key,
            env_name=signing_private_key_env,
        )
        if not private_key:
            errors.append("missing_signing_key")
        elif not _hyperliquid_signing_dependencies_available():
            errors.append("signing_dependencies_missing")

        nonce = int(time.time_ns() // 1_000_000)
        vault_address = None
        if isinstance(source_envelope, dict):
            signing_payload = source_envelope.get("signing_payload")
            if isinstance(signing_payload, dict):
                vault_address = _safe_string(signing_payload.get("vaultAddress"))

        cancel_action = _build_hyperliquid_cancel_action_payload(asset=asset, oid=oid, cloid=cloid)
        if cancel_action is None:
            errors.append("cancel_action_unavailable")

        if errors:
            cancel_state = errors[0]
            return HyperliquidCancelReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_session_id=source_session_id,
                source_action_hash=source_action_hash,
                source_signer_id=source_signer_id,
                source_signing_payload_sha256=source_signing_payload_sha256,
                source_submit_state=source_submit_state,
                cancel_payload=None,
                cancel_state=cancel_state,
                remote_cancel_called=False,
                cancel_accepted=False,
                response_type=None,
                asset=asset,
                oid=oid,
                cloid=cloid,
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=tuple(_unique_reasons(errors)),
            )

        try:
            signed = sign_hyperliquid_l1_action(
                private_key=private_key,
                action_payload=cancel_action,
                vault_address=vault_address,
                nonce=nonce,
                expires_after=None,
                is_mainnet=is_mainnet,
            )
        except Exception as exc:  # noqa: BLE001
            cancel_state = "cancel_signing_failed"
            errors.append(f"cancel_signing_failed:{exc.__class__.__name__}")
            return HyperliquidCancelReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_session_id=source_session_id,
                source_action_hash=source_action_hash,
                source_signer_id=source_signer_id,
                source_signing_payload_sha256=source_signing_payload_sha256,
                source_submit_state=source_submit_state,
                cancel_payload=None,
                cancel_state=cancel_state,
                remote_cancel_called=False,
                cancel_accepted=False,
                response_type=None,
                asset=asset,
                oid=oid,
                cloid=cloid,
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=tuple(_unique_reasons(errors)),
            )

        derived_signer = _safe_string(signed.get("signer_address"))
        if source_signer_id and derived_signer and source_signer_id.lower() != derived_signer.lower():
            errors.append("signer_identity_mismatch")
            cancel_state = "signer_identity_mismatch"
            return HyperliquidCancelReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_session_id=source_session_id,
                source_action_hash=source_action_hash,
                source_signer_id=source_signer_id,
                source_signing_payload_sha256=source_signing_payload_sha256,
                source_submit_state=source_submit_state,
                cancel_payload=None,
                cancel_state=cancel_state,
                remote_cancel_called=False,
                cancel_accepted=False,
                response_type=None,
                asset=asset,
                oid=oid,
                cloid=cloid,
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=tuple(_unique_reasons(errors)),
            )

        cancel_payload = {
            "action": cancel_action,
            "nonce": nonce,
            "signature": signed.get("signature"),
        }
        if vault_address:
            cancel_payload["vaultAddress"] = vault_address

        if not remote_cancel:
            return HyperliquidCancelReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                source_session_id=source_session_id,
                source_action_hash=source_action_hash,
                source_signer_id=source_signer_id,
                source_signing_payload_sha256=source_signing_payload_sha256,
                source_submit_state=source_submit_state,
                cancel_payload=cancel_payload,
                cancel_state="pending_remote_cancel",
                remote_cancel_called=False,
                cancel_accepted=False,
                response_type=None,
                asset=asset,
                oid=oid,
                cloid=cloid,
                exchange_response=None,
                reviewer=reviewer,
                note=note,
                errors=(),
            )

        try:
            exchange_response = fetch_hyperliquid_exchange(
                cancel_payload,
                timeout_seconds=timeout_seconds,
                post_json=post_json,
            )
            remote_cancel_called = True
            response_type = _extract_hyperliquid_response_type(exchange_response)
            cancel_errors = _extract_hyperliquid_exchange_errors(exchange_response)
            errors.extend(cancel_errors)
            cancel_accepted = not cancel_errors
            cancel_state = "canceled_remote" if cancel_accepted else "cancel_rejected"
        except Exception as exc:  # noqa: BLE001
            remote_cancel_called = True
            cancel_state = "cancel_request_failed"
            errors.append(f"cancel_request_failed:{exc.__class__.__name__}")

        return HyperliquidCancelReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            source_session_id=source_session_id,
            source_action_hash=source_action_hash,
            source_signer_id=source_signer_id,
            source_signing_payload_sha256=source_signing_payload_sha256,
            source_submit_state=source_submit_state,
            cancel_payload=cancel_payload,
            cancel_state=cancel_state,
            remote_cancel_called=remote_cancel_called,
            cancel_accepted=cancel_accepted,
            response_type=response_type,
            asset=asset,
            oid=oid,
            cloid=cloid,
            exchange_response=exchange_response,
            reviewer=reviewer,
            note=note,
            errors=tuple(_unique_reasons(errors)),
        )

    def build_reconciliation_report(
        self,
        *,
        source_session_id: str,
        execution_account_id: str | None,
        oid: int | None = None,
        cloid: str | None = None,
        signed_action_artifact: dict[str, object] | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidReconciliationReport:
        errors: list[str] = []
        status_report = self.build_order_status_report(
            source_session_id=source_session_id,
            execution_account_id=execution_account_id,
            oid=oid,
            cloid=cloid,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        ).to_dict()

        normalized_state = status_report.get("normalized_state")
        status_known = bool(status_report.get("status_known"))
        resolution_source = "order_status" if status_report.get("query_attempted") else None
        matched_open_order = None
        matched_frontend_open_order = None
        matched_historical_order = None
        matched_fills: list[dict[str, object]] = []

        resolved_execution_account = _safe_string(execution_account_id)
        resolved_cloid = _safe_string(cloid)
        resolved_oid = oid if isinstance(oid, int) and oid >= 0 else None
        original_size_hint = _extract_hyperliquid_signed_action_size(signed_action_artifact)

        if not resolved_execution_account:
            errors.append("missing_execution_account_id")
        elif not _is_hex_address(resolved_execution_account):
            errors.append("invalid_execution_account_id")

        if resolved_oid is None and not resolved_cloid:
            errors.append("missing_order_identifier")

        if not errors:
            if not status_known:
                try:
                    open_orders = fetch_hyperliquid_open_orders(
                        resolved_execution_account,
                        timeout_seconds=timeout_seconds,
                        fetch_json=fetch_json,
                    )
                    matched_open_order = _find_matching_hyperliquid_order(
                        open_orders,
                        oid=resolved_oid,
                        cloid=resolved_cloid,
                    )
                    if matched_open_order is not None:
                        status_known = True
                        normalized_state = "open"
                        resolution_source = "open_orders"
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"open_orders_reconciliation_failed:{exc.__class__.__name__}")

            if not status_known:
                try:
                    frontend_open_orders = fetch_hyperliquid_frontend_open_orders(
                        resolved_execution_account,
                        timeout_seconds=timeout_seconds,
                        fetch_json=fetch_json,
                    )
                    matched_frontend_open_order = _find_matching_hyperliquid_order(
                        frontend_open_orders,
                        oid=resolved_oid,
                        cloid=resolved_cloid,
                    )
                    if matched_frontend_open_order is not None:
                        status_known = True
                        normalized_state = "open"
                        resolution_source = "frontend_open_orders"
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"frontend_open_orders_reconciliation_failed:{exc.__class__.__name__}")

            if not status_known:
                try:
                    historical_orders = fetch_hyperliquid_historical_orders(
                        resolved_execution_account,
                        timeout_seconds=timeout_seconds,
                        fetch_json=fetch_json,
                    )
                    matched_historical_order = _find_matching_hyperliquid_order(
                        historical_orders,
                        oid=resolved_oid,
                        cloid=resolved_cloid,
                    )
                    if matched_historical_order is not None:
                        historical_status = _safe_string(matched_historical_order.get("status"))
                        normalized_state = _normalize_hyperliquid_order_state(historical_status)
                        status_known = normalized_state not in {None, "unknown"}
                        resolution_source = "historical_orders"
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"historical_orders_reconciliation_failed:{exc.__class__.__name__}")

            try:
                user_fills = fetch_hyperliquid_user_fills(
                    resolved_execution_account,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
                matched_fills = _find_matching_hyperliquid_fills(
                    user_fills,
                    oid=resolved_oid,
                    cloid=resolved_cloid,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"user_fills_reconciliation_failed:{exc.__class__.__name__}")

        matched_fills = _sort_hyperliquid_fills(matched_fills)
        size_source = (
            _extract_hyperliquid_status_order_snapshot(status_report)
            or matched_open_order
            or matched_frontend_open_order
            or matched_historical_order
        )
        original_size = _extract_hyperliquid_order_original_size(size_source)
        if original_size is None:
            original_size = original_size_hint
        remaining_size = _extract_hyperliquid_order_remaining_size(size_source)
        fill_metrics = _summarize_hyperliquid_fills(matched_fills)
        close_state = _derive_hyperliquid_close_state(normalized_state)
        fill_state = _derive_hyperliquid_fill_state(
            normalized_state=normalized_state,
            close_state=close_state,
            original_size=original_size,
            remaining_size=remaining_size,
            filled_size=fill_metrics["filled_size"],
            fill_count=fill_metrics["fill_count"],
        )

        if (
            not status_known
            and close_state != "open"
            and original_size is not None
            and fill_metrics["filled_size"] is not None
            and _decimal_at_least(fill_metrics["filled_size"], original_size)
        ):
            status_known = True
            normalized_state = "filled"
            close_state = "closed"
            fill_state = "filled"
            resolution_source = "user_fills"

        if not status_known and not errors:
            normalized_state = "unknown"
            resolution_source = "unresolved"
            errors.append("reconciliation_not_found")

        return HyperliquidReconciliationReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            source_session_id=source_session_id,
            execution_account_id=resolved_execution_account,
            status_known=status_known,
            normalized_state=normalized_state,
            close_state=close_state,
            fill_state=fill_state,
            resolution_source=resolution_source,
            oid=resolved_oid,
            cloid=resolved_cloid,
            original_size=_format_decimal_string(original_size),
            filled_size=_format_decimal_string(fill_metrics["filled_size"]),
            remaining_size=_format_decimal_string(remaining_size),
            fill_count=fill_metrics["fill_count"],
            average_fill_price=_format_decimal_string(fill_metrics["average_fill_price"]),
            last_fill_time=fill_metrics["last_fill_time"],
            order_status_report=status_report,
            matched_open_order=matched_open_order,
            matched_frontend_open_order=matched_frontend_open_order,
            matched_historical_order=matched_historical_order,
            matched_fill_sample=tuple(matched_fills[:5]),
            errors=tuple(_unique_reasons(errors)),
        )

    def build_fill_summary_report(
        self,
        *,
        source_session_id: str,
        execution_account_id: str | None,
        oid: int | None = None,
        cloid: str | None = None,
        signed_action_artifact: dict[str, object] | None = None,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> HyperliquidFillSummaryReport:
        errors: list[str] = []
        query_attempted = False
        matched_fills: list[dict[str, object]] = []

        resolved_execution_account = _safe_string(execution_account_id)
        resolved_cloid = _safe_string(cloid)
        resolved_oid = oid if isinstance(oid, int) and oid >= 0 else None
        original_size = _extract_hyperliquid_signed_action_size(signed_action_artifact)

        if not resolved_execution_account:
            errors.append("missing_execution_account_id")
        elif not _is_hex_address(resolved_execution_account):
            errors.append("invalid_execution_account_id")

        if resolved_oid is None and not resolved_cloid:
            errors.append("missing_order_identifier")

        if not errors:
            try:
                all_fills = fetch_hyperliquid_user_fills(
                    resolved_execution_account,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
                query_attempted = True
                matched_fills = _sort_hyperliquid_fills(
                    _find_matching_hyperliquid_fills(
                        all_fills,
                        oid=resolved_oid,
                        cloid=resolved_cloid,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"user_fills_summary_failed:{exc.__class__.__name__}")

        fill_metrics = _summarize_hyperliquid_fills(matched_fills)
        filled_size = fill_metrics["filled_size"]
        remaining_size = _subtract_decimals(original_size, filled_size)
        fill_state = _derive_hyperliquid_fill_summary_state(
            original_size=original_size,
            filled_size=filled_size,
            fill_count=fill_metrics["fill_count"],
        )
        fills_known = query_attempted and not errors

        return HyperliquidFillSummaryReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            source_session_id=source_session_id,
            execution_account_id=resolved_execution_account,
            fills_known=fills_known,
            query_attempted=query_attempted,
            oid=resolved_oid,
            cloid=resolved_cloid,
            fill_state=fill_state,
            original_size=_format_decimal_string(original_size),
            filled_size=_format_decimal_string(filled_size),
            remaining_size=_format_decimal_string(remaining_size),
            fill_count=fill_metrics["fill_count"],
            average_fill_price=_format_decimal_string(fill_metrics["average_fill_price"]),
            total_fee=_format_decimal_string(fill_metrics["total_fee"]),
            total_builder_fee=_format_decimal_string(fill_metrics["total_builder_fee"]),
            total_closed_pnl=_format_decimal_string(fill_metrics["total_closed_pnl"]),
            first_fill_time=fill_metrics["first_fill_time"],
            last_fill_time=fill_metrics["last_fill_time"],
            matched_fill_sample=tuple(matched_fills[:10]),
            errors=tuple(_unique_reasons(errors)),
        )


def fetch_hyperliquid_all_mids(
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> dict[str, str]:
    payload = fetch_hyperliquid_info({"type": "allMids"}, timeout_seconds=timeout_seconds, fetch_json=fetch_json)
    if isinstance(payload, dict):
        return {str(key): str(value) for key, value in payload.items()}
    return {}


def fetch_hyperliquid_user_role(
    user: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> str | None:
    payload = fetch_hyperliquid_info(
        {"type": "userRole", "user": user},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    if isinstance(payload, dict):
        role = payload.get("role")
        return str(role) if role is not None else None
    return None


def fetch_hyperliquid_open_orders(
    user: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> list[dict[str, object]]:
    payload = fetch_hyperliquid_info(
        {"type": "openOrders", "user": user},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def fetch_hyperliquid_frontend_open_orders(
    user: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> list[dict[str, object]]:
    payload = fetch_hyperliquid_info(
        {"type": "frontendOpenOrders", "user": user},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def fetch_hyperliquid_historical_orders(
    user: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> list[dict[str, object]]:
    payload = fetch_hyperliquid_info(
        {"type": "historicalOrders", "user": user},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def fetch_hyperliquid_user_fills(
    user: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> list[dict[str, object]]:
    payload = fetch_hyperliquid_info(
        {"type": "userFills", "user": user},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def fetch_hyperliquid_order_status(
    user: str,
    oid: int | str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> dict[str, object]:
    payload = fetch_hyperliquid_info(
        {"type": "orderStatus", "user": user, "oid": oid},
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    return payload if isinstance(payload, dict) else {"raw_response": payload}


def fetch_hyperliquid_perp_market(
    symbol: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> dict[str, object] | None:
    payload = fetch_hyperliquid_info({"type": "meta"}, timeout_seconds=timeout_seconds, fetch_json=fetch_json)
    universe = payload.get("universe", []) if isinstance(payload, dict) else []
    for index, item in enumerate(universe):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().upper()
        if name != symbol:
            continue
        return {
            "matched_name": name,
            "resolved_coin": name,
            "resolved_asset": index,
        }
    return None


def fetch_hyperliquid_spot_market(
    symbol: str,
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> dict[str, object] | None:
    payload = fetch_hyperliquid_info({"type": "spotMeta"}, timeout_seconds=timeout_seconds, fetch_json=fetch_json)
    universe = payload.get("universe", []) if isinstance(payload, dict) else []
    target = _SPOT_SYMBOL_ALIASES.get(symbol, symbol)
    for item in universe:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().upper()
        if name != target:
            continue
        pair_index = int(item.get("index"))
        resolved_coin = name if name == "PURR/USDC" else f"@{pair_index}"
        return {
            "matched_name": name,
            "resolved_coin": resolved_coin,
            "resolved_asset": 10000 + pair_index,
        }
    return None


def fetch_hyperliquid_info(
    payload: dict[str, object],
    *,
    timeout_seconds: float = 10.0,
    fetch_json=None,
) -> object:
    fetcher = fetch_json or _post_info_json
    return fetcher(payload, timeout_seconds=timeout_seconds)


def fetch_hyperliquid_exchange(
    payload: dict[str, object],
    *,
    timeout_seconds: float = 10.0,
    post_json=None,
) -> dict[str, object]:
    poster = post_json or _post_exchange_json
    response = poster(payload, timeout_seconds=timeout_seconds)
    return response if isinstance(response, dict) else {"raw_response": response}


def _post_info_json(
    payload: dict[str, object],
    *,
    timeout_seconds: float = 10.0,
) -> object:
    request = Request(
        HYPERLIQUID_INFO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_exchange_json(
    payload: dict[str, object],
    *,
    timeout_seconds: float = 10.0,
) -> object:
    request = Request(
        HYPERLIQUID_EXCHANGE_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_hyperliquid_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace("-", "/")


def _is_hex_address(value: str) -> bool:
    candidate = value.strip()
    if len(candidate) != 42 or not candidate.startswith("0x"):
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in candidate[2:])


def _unique_reasons(reasons: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason and reason not in seen:
            ordered.append(reason)
            seen.add(reason)
    return ordered


def _resolve_hyperliquid_nonce(
    *,
    context: ExecutionContext | None,
    now_ms: int | None = None,
) -> tuple[int, str]:
    if context and context.nonce_hint is not None:
        return int(context.nonce_hint), "context_nonce_hint"
    return int(now_ms if now_ms is not None else time.time_ns() // 1_000_000), "generated_ms_timestamp"


def _resolve_expires_after(
    *,
    context: ExecutionContext | None,
    nonce: int,
) -> tuple[int | None, str | None]:
    if not context or context.expires_after is None:
        return None, None
    if context.expires_after >= 10_000_000_000:
        return int(context.expires_after), "absolute_ms"
    return nonce + int(context.expires_after), "relative_ms"


def _format_hyperliquid_size(quantity: float) -> str:
    return f"{quantity:.8f}".rstrip("0").rstrip(".")


def _build_hyperliquid_cloid(request_id: str) -> str:
    digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
    return digest[:32]


def _build_hyperliquid_submit_payload(
    signed_action_artifact: dict[str, object],
) -> dict[str, object] | None:
    action_payload = signed_action_artifact.get("action_payload")
    signature_envelope = signed_action_artifact.get("signature_envelope")
    nonce = signed_action_artifact.get("nonce")
    expires_after = signed_action_artifact.get("expires_after")

    if not isinstance(action_payload, dict):
        return None
    if not isinstance(signature_envelope, dict):
        return None
    if not isinstance(signature_envelope.get("signature"), dict):
        return None
    if nonce is None:
        return None

    signing_payload = signature_envelope.get("signing_payload", {})
    payload = {
        "action": action_payload,
        "nonce": nonce,
        "signature": signature_envelope.get("signature"),
    }

    vault_address = None
    if isinstance(signing_payload, dict):
        vault_address = signing_payload.get("vaultAddress")
    if isinstance(vault_address, str) and vault_address.strip():
        payload["vaultAddress"] = vault_address
    if expires_after is not None:
        payload["expiresAfter"] = expires_after
    return payload


def _extract_hyperliquid_submit_oid(exchange_response: dict[str, object] | None) -> int | None:
    if not isinstance(exchange_response, dict):
        return None
    direct_oid = exchange_response.get("oid")
    if isinstance(direct_oid, int):
        return direct_oid
    response = exchange_response.get("response")
    if not isinstance(response, dict):
        return None
    data = response.get("data")
    if not isinstance(data, dict):
        return None
    statuses = data.get("statuses")
    if not isinstance(statuses, list):
        return None
    for item in statuses:
        if not isinstance(item, dict):
            continue
        for value in item.values():
            if isinstance(value, dict) and isinstance(value.get("oid"), int):
                return value.get("oid")
    return None


def _extract_hyperliquid_submit_asset(signed_action_artifact: dict[str, object]) -> int | None:
    action_payload = signed_action_artifact.get("action_payload")
    if not isinstance(action_payload, dict):
        return None
    orders = action_payload.get("orders")
    if not isinstance(orders, list) or not orders:
        return None
    first_order = orders[0]
    if not isinstance(first_order, dict):
        return None
    asset = first_order.get("a")
    return asset if isinstance(asset, int) and asset >= 0 else None


def _extract_hyperliquid_submit_cloid(signed_action_artifact: dict[str, object]) -> str | None:
    action_payload = signed_action_artifact.get("action_payload")
    if not isinstance(action_payload, dict):
        return None
    orders = action_payload.get("orders")
    if not isinstance(orders, list) or not orders:
        return None
    first_order = orders[0]
    if not isinstance(first_order, dict):
        return None
    return _safe_string(first_order.get("c"))


def _extract_hyperliquid_response_type(exchange_response: dict[str, object] | None) -> str | None:
    if not isinstance(exchange_response, dict):
        return None
    response = exchange_response.get("response")
    if isinstance(response, dict):
        response_type = response.get("type")
        if response_type is not None:
            return str(response_type)
    status = exchange_response.get("status")
    return str(status) if status is not None else None


def _extract_hyperliquid_exchange_errors(
    exchange_response: dict[str, object] | None,
) -> list[str]:
    if not isinstance(exchange_response, dict):
        return ["invalid_exchange_response"]

    errors: list[str] = []
    status = str(exchange_response.get("status") or "").strip().lower()
    if status and status != "ok":
        errors.append(f"exchange_status:{status}")

    response = exchange_response.get("response")
    if isinstance(response, dict):
        response_type = str(response.get("type") or "").strip().lower()
        if response_type == "error":
            errors.append("exchange_response_error")
        data = response.get("data")
        if isinstance(data, dict):
            statuses = data.get("statuses")
            if isinstance(statuses, list):
                for item in statuses:
                    if isinstance(item, dict) and "error" in item:
                        errors.append(f"status_error:{item.get('error')}")

    return _unique_reasons(str(item) for item in errors)


def _classify_hyperliquid_submit_response(
    exchange_response: dict[str, object] | None,
) -> tuple[bool, list[str]]:
    errors = _extract_hyperliquid_exchange_errors(exchange_response)
    status = str(exchange_response.get("status") or "").strip().lower() if isinstance(exchange_response, dict) else ""
    submitted = not errors and status == "ok"
    return submitted, errors


def _build_hyperliquid_cancel_action_payload(
    *,
    asset: int | None,
    oid: int | None,
    cloid: str | None,
) -> dict[str, object] | None:
    if asset is None:
        return None
    if oid is not None:
        return {
            "type": "cancel",
            "cancels": [{"a": asset, "o": oid}],
        }
    if cloid:
        return {
            "type": "cancelByCloid",
            "cancels": [{"asset": asset, "cloid": cloid}],
        }
    return None


_HYPERLIQUID_CANCELED_STATES = {
    "canceled",
    "margincanceled",
    "vaultwithdrawalcanceled",
    "openinterestcapcanceled",
    "selftradecanceled",
    "reduceonlycanceled",
    "siblingfilledcanceled",
    "delistedcanceled",
    "liquidatedcanceled",
    "scheduledcancel",
}

_HYPERLIQUID_REJECTED_STATES = {
    "rejected",
    "tickrejected",
    "mintradentlrejected",
    "perpmarginrejected",
    "reduceonlyrejected",
    "badalopxrejected",
    "ioccancelrejected",
    "badtriggerpxrejected",
    "marketordernoliquidityrejected",
    "positionincreaseatopeninterestcaprejected",
    "positionflipatopeninterestcaprejected",
    "tooaggressiveatopeninterestcaprejected",
    "openinterestincreaserejected",
    "insufficientspotbalancerejected",
    "oraclerejected",
    "perpmaxpositionrejected",
}


def _extract_hyperliquid_order_status(order_status: dict[str, object] | None) -> str | None:
    if not isinstance(order_status, dict):
        return None
    status = order_status.get("status")
    if isinstance(status, str):
        normalized = status.strip()
        if normalized:
            lower = normalized.lower()
            if lower == "order":
                order = order_status.get("order")
                if isinstance(order, dict):
                    nested_status = order.get("status")
                    if isinstance(nested_status, str) and nested_status.strip():
                        return nested_status.strip()
            if lower in {"missing", "missingorder", "missing_order"}:
                return "missing_order"
            return normalized
    order = order_status.get("order")
    if isinstance(order, dict):
        nested_status = order.get("status")
        if isinstance(nested_status, str) and nested_status.strip():
            return nested_status.strip()
    return None


def _find_matching_hyperliquid_order(
    orders: list[dict[str, object]] | None,
    *,
    oid: int | None,
    cloid: str | None,
) -> dict[str, object] | None:
    if not isinstance(orders, list):
        return None
    for item in orders:
        if not isinstance(item, dict):
            continue
        item_oid = _extract_hyperliquid_order_oid(item)
        item_cloid = _extract_hyperliquid_order_cloid(item)
        if oid is not None and item_oid == oid:
            return item
        if cloid and item_cloid and item_cloid == cloid:
            return item
    return None


def _find_matching_hyperliquid_fills(
    fills: list[dict[str, object]] | None,
    *,
    oid: int | None,
    cloid: str | None,
) -> list[dict[str, object]]:
    if not isinstance(fills, list):
        return []
    matches: list[dict[str, object]] = []
    for item in fills:
        if not isinstance(item, dict):
            continue
        item_oid = _extract_hyperliquid_order_oid(item)
        item_cloid = _extract_hyperliquid_order_cloid(item)
        if oid is not None and item_oid == oid:
            matches.append(item)
            continue
        if cloid and item_cloid and item_cloid == cloid:
            matches.append(item)
    return matches


def _extract_hyperliquid_order_oid(order_item: dict[str, object]) -> int | None:
    direct_oid = order_item.get("oid")
    if isinstance(direct_oid, int):
        return direct_oid
    nested_order = order_item.get("order")
    if isinstance(nested_order, dict):
        nested_oid = nested_order.get("oid")
        if isinstance(nested_oid, int):
            return nested_oid
    return None


def _extract_hyperliquid_order_cloid(order_item: dict[str, object]) -> str | None:
    for key in ("cloid", "c", "clientOrderId"):
        value = _safe_string(order_item.get(key))
        if value:
            return value
    nested_order = order_item.get("order")
    if isinstance(nested_order, dict):
        for key in ("cloid", "c", "clientOrderId"):
            value = _safe_string(nested_order.get(key))
            if value:
                return value
    return None


def _extract_hyperliquid_status_order_snapshot(status_report: dict[str, object] | None) -> dict[str, object] | None:
    if not isinstance(status_report, dict):
        return None
    order_status = status_report.get("order_status")
    if not isinstance(order_status, dict):
        return None
    status_block = order_status.get("order")
    if isinstance(status_block, dict):
        nested_order = status_block.get("order")
        if isinstance(nested_order, dict):
            return nested_order
    return None


def _extract_hyperliquid_order_original_size(order_item: dict[str, object] | None) -> Decimal | None:
    return _extract_hyperliquid_decimal_field(order_item, "origSz")


def _extract_hyperliquid_order_remaining_size(order_item: dict[str, object] | None) -> Decimal | None:
    return _extract_hyperliquid_decimal_field(order_item, "sz")


def _extract_hyperliquid_signed_action_size(signed_action_artifact: dict[str, object] | None) -> Decimal | None:
    if not isinstance(signed_action_artifact, dict):
        return None
    action_payload = signed_action_artifact.get("action_payload")
    if not isinstance(action_payload, dict):
        return None
    orders = action_payload.get("orders")
    if not isinstance(orders, list) or not orders:
        return None
    first_order = orders[0]
    if not isinstance(first_order, dict):
        return None
    return _parse_decimal(first_order.get("s"))


def _extract_hyperliquid_decimal_field(order_item: dict[str, object] | None, key: str) -> Decimal | None:
    if not isinstance(order_item, dict):
        return None
    value = order_item.get(key)
    parsed = _parse_decimal(value)
    if parsed is not None:
        return parsed
    nested_order = order_item.get("order")
    if isinstance(nested_order, dict):
        return _parse_decimal(nested_order.get(key))
    return None


def _sort_hyperliquid_fills(fills: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        fills,
        key=lambda item: (
            _extract_hyperliquid_fill_time(item) or -1,
            _extract_hyperliquid_fill_tid(item) or -1,
        ),
        reverse=True,
    )


def _summarize_hyperliquid_fills(fills: list[dict[str, object]]) -> dict[str, object]:
    total_size = Decimal("0")
    weighted_notional = Decimal("0")
    total_fee = Decimal("0")
    total_builder_fee = Decimal("0")
    total_closed_pnl = Decimal("0")
    first_fill_time: int | None = None
    last_fill_time: int | None = None

    for item in fills:
        size = _parse_decimal(item.get("sz"))
        price = _parse_decimal(item.get("px"))
        fee = _parse_decimal(item.get("fee"))
        builder_fee = _parse_decimal(item.get("builderFee"))
        closed_pnl = _parse_decimal(item.get("closedPnl"))
        fill_time = _extract_hyperliquid_fill_time(item)
        if fill_time is not None and (first_fill_time is None or fill_time < first_fill_time):
            first_fill_time = fill_time
        if fill_time is not None and (last_fill_time is None or fill_time > last_fill_time):
            last_fill_time = fill_time
        if size is None:
            size = Decimal("0")
        total_size += size
        if price is not None and size > 0:
            weighted_notional += size * price
        if fee is not None:
            total_fee += fee
        if builder_fee is not None:
            total_builder_fee += builder_fee
        if closed_pnl is not None:
            total_closed_pnl += closed_pnl

    average_fill_price = None
    if total_size > 0 and weighted_notional > 0:
        average_fill_price = weighted_notional / total_size

    return {
        "fill_count": len(fills),
        "filled_size": total_size if total_size > 0 else None,
        "average_fill_price": average_fill_price,
        "total_fee": total_fee if total_fee != 0 else None,
        "total_builder_fee": total_builder_fee if total_builder_fee != 0 else None,
        "total_closed_pnl": total_closed_pnl if total_closed_pnl != 0 else None,
        "first_fill_time": first_fill_time,
        "last_fill_time": last_fill_time,
    }


def _extract_hyperliquid_fill_time(fill: dict[str, object]) -> int | None:
    value = fill.get("time")
    return value if isinstance(value, int) and value >= 0 else None


def _extract_hyperliquid_fill_tid(fill: dict[str, object]) -> int | None:
    value = fill.get("tid")
    return value if isinstance(value, int) and value >= 0 else None


def _normalize_hyperliquid_order_state(raw_status: str | None) -> str | None:
    if raw_status is None:
        return None
    lowered = raw_status.strip().lower()
    if lowered in {"open", "triggered"}:
        return "open"
    if lowered == "filled":
        return "filled"
    if lowered in _HYPERLIQUID_CANCELED_STATES:
        return "canceled"
    if lowered in _HYPERLIQUID_REJECTED_STATES:
        return "rejected"
    if lowered == "missing_order":
        return "unknown"
    return "unknown"


def _derive_hyperliquid_close_state(normalized_state: str | None) -> str | None:
    if normalized_state == "open":
        return "open"
    if normalized_state in {"filled", "canceled", "rejected"}:
        return "closed"
    if normalized_state == "unknown":
        return "unknown"
    return None


def _derive_hyperliquid_fill_state(
    *,
    normalized_state: str | None,
    close_state: str | None,
    original_size: Decimal | None,
    remaining_size: Decimal | None,
    filled_size: Decimal | None,
    fill_count: int,
) -> str | None:
    if normalized_state == "filled":
        return "filled"
    if fill_count > 0:
        if normalized_state in {"canceled", "rejected"}:
            return "partial"
        if close_state == "open":
            return "partial"
        if original_size is not None and filled_size is not None and _decimal_at_least(filled_size, original_size):
            return "filled"
        return "partial"
    if original_size is not None and remaining_size is not None:
        if remaining_size < original_size:
            return "partial"
        if remaining_size >= original_size:
            return "none"
    if close_state in {"open", "closed"}:
        return "none"
    if normalized_state == "unknown":
        return "unknown"
    return None


def _derive_hyperliquid_fill_summary_state(
    *,
    original_size: Decimal | None,
    filled_size: Decimal | None,
    fill_count: int,
) -> str | None:
    if fill_count <= 0:
        return "none"
    if original_size is not None and filled_size is not None and _decimal_at_least(filled_size, original_size):
        return "filled"
    return "partial"


def _decimal_at_least(left: Decimal, right: Decimal, tolerance: str = "0.000000000001") -> bool:
    return left + Decimal(tolerance) >= right


def _subtract_decimals(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    if left is None:
        return None
    if right is None:
        return left
    result = left - right
    if result < 0:
        return Decimal("0")
    return result


def _parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        text = str(value).strip()
        if not text:
            return None
        return Decimal(text)
    except (ArithmeticError, InvalidOperation, ValueError):
        return None


def _format_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _safe_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _hyperliquid_signing_dependencies_available() -> bool:
    return all(module is not None for module in (msgpack, Account, encode_typed_data, keccak, to_hex))


def _load_hyperliquid_private_key(
    *,
    explicit_value: str | None,
    env_name: str,
) -> tuple[str | None, str | None]:
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip(), "explicit_arg"
    if env_name:
        env_value = os.getenv(env_name)
        if isinstance(env_value, str) and env_value.strip():
            return env_value.strip(), f"env:{env_name}"
    return None, None


def sign_hyperliquid_l1_action(
    *,
    private_key: str,
    action_payload: dict[str, object] | None,
    vault_address: str | None,
    nonce: int,
    expires_after: int | None,
    is_mainnet: bool = True,
) -> dict[str, object]:
    if not action_payload:
        raise ValueError("missing_action_payload")
    if not _hyperliquid_signing_dependencies_available():
        raise RuntimeError("missing_signing_dependencies")

    wallet = Account.from_key(private_key)
    action_hash = _hyperliquid_action_hash(action_payload, vault_address, nonce, expires_after)
    phantom_agent = {
        "source": "a" if is_mainnet else "b",
        "connectionId": action_hash,
    }
    eip712_payload = {
        "domain": {
            "chainId": 1337,
            "name": "Exchange",
            "verifyingContract": "0x0000000000000000000000000000000000000000",
            "version": "1",
        },
        "types": {
            "Agent": [
                {"name": "source", "type": "string"},
                {"name": "connectionId", "type": "bytes32"},
            ],
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
        },
        "primaryType": "Agent",
        "message": phantom_agent,
    }
    structured_data = encode_typed_data(full_message=eip712_payload)
    signed = wallet.sign_message(structured_data)
    signature = {
        "r": to_hex(signed.r),
        "s": to_hex(signed.s),
        "v": signed.v,
    }
    return {
        "signer_address": wallet.address,
        "action_hash": action_hash.hex(),
        "phantom_agent": {
            "source": phantom_agent["source"],
            "connectionId": action_hash.hex(),
        },
        "eip712_payload": eip712_payload,
        "signature": signature,
    }


def recover_hyperliquid_l1_action_signer(
    *,
    action_payload: dict[str, object] | None,
    signature: dict[str, object],
    vault_address: str | None,
    nonce: int,
    expires_after: int | None,
    is_mainnet: bool = True,
) -> str:
    if not _hyperliquid_signing_dependencies_available():
        raise RuntimeError("missing_signing_dependencies")
    action_hash = _hyperliquid_action_hash(action_payload, vault_address, nonce, expires_after)
    phantom_agent = {
        "source": "a" if is_mainnet else "b",
        "connectionId": action_hash,
    }
    eip712_payload = {
        "domain": {
            "chainId": 1337,
            "name": "Exchange",
            "verifyingContract": "0x0000000000000000000000000000000000000000",
            "version": "1",
        },
        "types": {
            "Agent": [
                {"name": "source", "type": "string"},
                {"name": "connectionId", "type": "bytes32"},
            ],
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
        },
        "primaryType": "Agent",
        "message": phantom_agent,
    }
    structured_data = encode_typed_data(full_message=eip712_payload)
    recovered = Account.recover_message(
        structured_data,
        vrs=[signature["v"], signature["r"], signature["s"]],
    )
    return str(recovered)


def _hyperliquid_action_hash(
    action_payload: dict[str, object] | None,
    vault_address: str | None,
    nonce: int,
    expires_after: int | None,
) -> bytes:
    if not action_payload:
        raise ValueError("missing_action_payload")
    if msgpack is None or keccak is None:
        raise RuntimeError("missing_signing_dependencies")
    data = msgpack.packb(action_payload)
    data += int(nonce).to_bytes(8, "big")
    if vault_address is None:
        data += b"\x00"
    else:
        data += b"\x01"
        data += bytes.fromhex(vault_address[2:] if str(vault_address).startswith("0x") else str(vault_address))
    if expires_after is not None:
        data += b"\x00"
        data += int(expires_after).to_bytes(8, "big")
    return keccak(data)
