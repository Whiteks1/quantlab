"""
Stage D.1.b Hyperliquid read-only venue preflight.

This module keeps the first Hyperliquid slice intentionally read-only. It
resolves execution-context semantics and checks venue metadata without placing
or validating live orders.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from urllib.request import Request, urlopen

from .boundary import (
    BrokerAdapter,
    ExecutionContext,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)

HYPERLIQUID_INFO_API_URL = "https://api.hyperliquid.xyz/info"
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
        if context.signer_type in {"api_wallet", "agent_wallet"} and not signer_id:
            reasons.append("missing_signer_id")
        if query_user and not _is_hex_address(query_user):
            reasons.append("invalid_execution_account_id")
        if signer_id and not _is_hex_address(signer_id):
            reasons.append("invalid_signer_id")
        if context.expires_after is not None and context.expires_after <= 0:
            reasons.append("non_positive_expires_after")

        if fetch_json is not None and query_user and _is_hex_address(query_user):
            try:
                execution_account_role = fetch_hyperliquid_user_role(
                    query_user,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"execution_account_role_probe_failed:{exc.__class__.__name__}")

        if fetch_json is not None and signer_id and _is_hex_address(signer_id) and signer_id != query_user:
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
