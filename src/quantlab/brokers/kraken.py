"""
Stage D.1 Kraken dry-run adapter.

This module validates that the broker boundary can support a first concrete
backend without sending real broker requests.
"""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import datetime as dt
import hashlib
import hmac
import json
import os
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .boundary import (
    BrokerAdapter,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)

KRAKEN_PUBLIC_API_BASE = "https://api.kraken.com/0/public"
_SYMBOL_ALIASES = {"BTC": "XBT"}


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


@dataclass(frozen=True)
class KrakenPreflightReport:
    adapter_name: str
    generated_at: str
    symbol_input: str
    normalized_symbol: str
    public_api_reachable: bool
    pair_supported: bool
    server_time_unix: int | None
    server_time_rfc1123: str | None
    matched_pair_key: str | None
    matched_pair_wsname: str | None
    matched_pair_altname: str | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.kraken.preflight",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "symbol_input": self.symbol_input,
            "normalized_symbol": self.normalized_symbol,
            "public_api_reachable": self.public_api_reachable,
            "pair_supported": self.pair_supported,
            "server_time_unix": self.server_time_unix,
            "server_time_rfc1123": self.server_time_rfc1123,
            "matched_pair_key": self.matched_pair_key,
            "matched_pair_wsname": self.matched_pair_wsname,
            "matched_pair_altname": self.matched_pair_altname,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class KrakenAuthPreflightReport:
    adapter_name: str
    generated_at: str
    credentials_present: bool
    authenticated: bool
    api_key_env: str
    api_secret_env: str
    key_name: str | None
    permissions: dict[str, object] | None
    restrictions: dict[str, object] | None
    created_at: str | None
    updated_at: str | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.kraken.auth_preflight",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "credentials_present": self.credentials_present,
            "authenticated": self.authenticated,
            "api_key_env": self.api_key_env,
            "api_secret_env": self.api_secret_env,
            "key_name": self.key_name,
            "permissions": self.permissions,
            "restrictions": self.restrictions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class KrakenBalanceEntry:
    asset: str
    balance: float | None
    credit: float | None
    credit_used: float | None
    hold_trade: float | None
    available: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "asset": self.asset,
            "balance": self.balance,
            "credit": self.credit,
            "credit_used": self.credit_used,
            "hold_trade": self.hold_trade,
            "available": self.available,
        }


@dataclass(frozen=True)
class KrakenIntentReadiness:
    allowed: bool
    reasons: tuple[str, ...]
    funding_asset: str | None
    funding_basis: str | None
    required_amount: float | None
    available_amount: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "funding_asset": self.funding_asset,
            "funding_basis": self.funding_basis,
            "required_amount": self.required_amount,
            "available_amount": self.available_amount,
        }


@dataclass(frozen=True)
class KrakenAccountSnapshotReport:
    adapter_name: str
    generated_at: str
    symbol_input: str
    normalized_symbol: str
    public_api_reachable: bool
    pair_supported: bool
    matched_pair_key: str | None
    matched_pair_wsname: str | None
    matched_pair_altname: str | None
    base_asset: str | None
    quote_asset: str | None
    pair_status: str | None
    ordermin: float | None
    costmin: float | None
    tick_size: float | None
    account_snapshot_available: bool
    balances: tuple[KrakenBalanceEntry, ...]
    authenticated_preflight: KrakenAuthPreflightReport
    intent: ExecutionIntent
    policy: ExecutionPolicy
    local_preflight: ExecutionPreflight
    intent_readiness: KrakenIntentReadiness
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "quantlab.kraken.account_snapshot",
            "adapter_name": self.adapter_name,
            "generated_at": self.generated_at,
            "symbol_input": self.symbol_input,
            "normalized_symbol": self.normalized_symbol,
            "public_api_reachable": self.public_api_reachable,
            "pair_supported": self.pair_supported,
            "matched_pair_key": self.matched_pair_key,
            "matched_pair_wsname": self.matched_pair_wsname,
            "matched_pair_altname": self.matched_pair_altname,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "pair_status": self.pair_status,
            "ordermin": self.ordermin,
            "costmin": self.costmin,
            "tick_size": self.tick_size,
            "account_snapshot_available": self.account_snapshot_available,
            "balances": [entry.to_dict() for entry in self.balances],
            "authenticated_preflight": self.authenticated_preflight.to_dict(),
            "intent": asdict(self.intent),
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
            "intent_readiness": self.intent_readiness.to_dict(),
            "errors": list(self.errors),
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

    def build_public_preflight_report(
        self,
        symbol: str,
        *,
        timeout_seconds: float = 10.0,
        fetch_json=None,
    ) -> KrakenPreflightReport:
        normalized_symbol = _normalize_kraken_pair(symbol)
        errors: list[str] = []
        public_api_reachable = False
        server_time_unix = None
        server_time_rfc1123 = None
        matched_pair_key = None
        matched_pair_wsname = None
        matched_pair_altname = None
        pair_supported = False

        try:
            time_payload = fetch_kraken_server_time(
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
            )
            server_time = time_payload.get("result", {})
            server_time_unix = server_time.get("unixtime")
            server_time_rfc1123 = server_time.get("rfc1123")
            public_api_reachable = True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"server_time_probe_failed:{exc.__class__.__name__}")

        try:
            asset_pairs_payload = fetch_kraken_asset_pairs(
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
            )
            pair_match = _find_matching_asset_pair(
                normalized_symbol,
                asset_pairs_payload.get("result", {}),
            )
            if pair_match is not None:
                public_api_reachable = True
                pair_supported = True
                matched_pair_key = pair_match["pair_key"]
                matched_pair_wsname = pair_match["wsname"]
                matched_pair_altname = pair_match["altname"]
            else:
                errors.append("pair_not_supported")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"asset_pairs_probe_failed:{exc.__class__.__name__}")

        return KrakenPreflightReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            symbol_input=symbol,
            normalized_symbol=normalized_symbol,
            public_api_reachable=public_api_reachable,
            pair_supported=pair_supported,
            server_time_unix=server_time_unix,
            server_time_rfc1123=server_time_rfc1123,
            matched_pair_key=matched_pair_key,
            matched_pair_wsname=matched_pair_wsname,
            matched_pair_altname=matched_pair_altname,
            errors=tuple(errors),
        )

    def build_authenticated_preflight_report(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        api_key_env: str = "KRAKEN_API_KEY",
        api_secret_env: str = "KRAKEN_API_SECRET",
        timeout_seconds: float = 10.0,
        fetch_private_json=None,
    ) -> KrakenAuthPreflightReport:
        resolved_key = api_key or os.getenv(api_key_env)
        resolved_secret = api_secret or os.getenv(api_secret_env)
        errors: list[str] = []

        if not resolved_key:
            errors.append("missing_api_key")
        if not resolved_secret:
            errors.append("missing_api_secret")

        if errors:
            return KrakenAuthPreflightReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                credentials_present=False,
                authenticated=False,
                api_key_env=api_key_env,
                api_secret_env=api_secret_env,
                key_name=None,
                permissions=None,
                restrictions=None,
                created_at=None,
                updated_at=None,
                errors=tuple(errors),
            )

        try:
            response = fetch_kraken_api_key_info(
                api_key=resolved_key,
                api_secret=resolved_secret,
                timeout_seconds=timeout_seconds,
                fetch_private_json=fetch_private_json,
            )
            response_errors = response.get("error", []) if isinstance(response, dict) else []
            if response_errors:
                return KrakenAuthPreflightReport(
                    adapter_name=self.adapter_name,
                    generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                    credentials_present=True,
                    authenticated=False,
                    api_key_env=api_key_env,
                    api_secret_env=api_secret_env,
                    key_name=None,
                    permissions=None,
                    restrictions=None,
                    created_at=None,
                    updated_at=None,
                    errors=tuple(str(err) for err in response_errors),
                )
            result = response.get("result", {}) if isinstance(response, dict) else {}
            return KrakenAuthPreflightReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                credentials_present=True,
                authenticated=True,
                api_key_env=api_key_env,
                api_secret_env=api_secret_env,
                key_name=result.get("name"),
                permissions=result.get("permissions"),
                restrictions=result.get("restrictions"),
                created_at=result.get("created"),
                updated_at=result.get("updated"),
                errors=(),
            )
        except Exception as exc:  # noqa: BLE001
            return KrakenAuthPreflightReport(
                adapter_name=self.adapter_name,
                generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                credentials_present=True,
                authenticated=False,
                api_key_env=api_key_env,
                api_secret_env=api_secret_env,
                key_name=None,
                permissions=None,
                restrictions=None,
                created_at=None,
                updated_at=None,
                errors=(f"auth_probe_failed:{exc.__class__.__name__}",),
            )

    def build_account_snapshot_report(
        self,
        intent: ExecutionIntent,
        policy: ExecutionPolicy,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        api_key_env: str = "KRAKEN_API_KEY",
        api_secret_env: str = "KRAKEN_API_SECRET",
        timeout_seconds: float = 10.0,
        fetch_json=None,
        fetch_private_json=None,
    ) -> KrakenAccountSnapshotReport:
        public_report = self.build_public_preflight_report(
            intent.symbol,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        auth_report = self.build_authenticated_preflight_report(
            api_key=api_key,
            api_secret=api_secret,
            api_key_env=api_key_env,
            api_secret_env=api_secret_env,
            timeout_seconds=timeout_seconds,
            fetch_private_json=fetch_private_json,
        )
        local_preflight = self.preflight(intent, policy)
        errors: list[str] = list(public_report.errors) + list(auth_report.errors)

        pair_details = None
        if public_report.pair_supported:
            try:
                asset_pairs_payload = fetch_kraken_asset_pairs(
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                )
                pair_details = _find_matching_asset_pair(
                    public_report.normalized_symbol,
                    asset_pairs_payload.get("result", {}),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"pair_details_probe_failed:{exc.__class__.__name__}")

        balances: tuple[KrakenBalanceEntry, ...] = ()
        account_snapshot_available = False
        if auth_report.authenticated:
            try:
                balance_payload = fetch_kraken_extended_balance(
                    api_key=api_key or os.getenv(api_key_env, ""),
                    api_secret=api_secret or os.getenv(api_secret_env, ""),
                    timeout_seconds=timeout_seconds,
                    fetch_private_json=fetch_private_json,
                )
                balance_errors = balance_payload.get("error", []) if isinstance(balance_payload, dict) else []
                if balance_errors:
                    errors.extend(str(err) for err in balance_errors)
                else:
                    balances = tuple(_build_balance_entries(balance_payload.get("result", {})))
                    account_snapshot_available = True
            except Exception as exc:  # noqa: BLE001
                errors.append(f"balance_probe_failed:{exc.__class__.__name__}")

        readiness = _build_intent_readiness(
            intent=intent,
            pair_supported=public_report.pair_supported,
            pair_details=pair_details,
            authenticated=auth_report.authenticated,
            account_snapshot_available=account_snapshot_available,
            balances=balances,
            local_preflight=local_preflight,
        )

        return KrakenAccountSnapshotReport(
            adapter_name=self.adapter_name,
            generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
            symbol_input=intent.symbol,
            normalized_symbol=public_report.normalized_symbol,
            public_api_reachable=public_report.public_api_reachable,
            pair_supported=public_report.pair_supported,
            matched_pair_key=public_report.matched_pair_key,
            matched_pair_wsname=public_report.matched_pair_wsname,
            matched_pair_altname=public_report.matched_pair_altname,
            base_asset=_pair_value(pair_details, "base"),
            quote_asset=_pair_value(pair_details, "quote"),
            pair_status=_pair_value(pair_details, "status"),
            ordermin=_pair_float(pair_details, "ordermin"),
            costmin=_pair_float(pair_details, "costmin"),
            tick_size=_pair_float(pair_details, "tick_size"),
            account_snapshot_available=account_snapshot_available,
            balances=balances,
            authenticated_preflight=auth_report,
            intent=intent,
            policy=policy,
            local_preflight=local_preflight,
            intent_readiness=readiness,
            errors=tuple(errors),
        )


def _normalize_kraken_pair(symbol: str) -> str:
    raw = symbol.strip().upper().replace("-", "/")
    parts = [part.strip() for part in raw.split("/") if part.strip()]
    aliased = [_SYMBOL_ALIASES.get(part, part) for part in parts]
    return "/".join(aliased) if aliased else raw


def _format_quantity(quantity: float) -> str:
    return f"{quantity:.8f}".rstrip("0").rstrip(".")


def fetch_kraken_server_time(*, timeout_seconds: float = 10.0, fetch_json=None) -> dict[str, object]:
    fetcher = fetch_json or _fetch_public_json
    return fetcher("/Time", timeout_seconds=timeout_seconds)


def fetch_kraken_asset_pairs(*, timeout_seconds: float = 10.0, fetch_json=None) -> dict[str, object]:
    fetcher = fetch_json or _fetch_public_json
    return fetcher("/AssetPairs", timeout_seconds=timeout_seconds)


def fetch_kraken_api_key_info(
    *,
    api_key: str,
    api_secret: str,
    timeout_seconds: float = 10.0,
    fetch_private_json=None,
) -> dict[str, object]:
    fetcher = fetch_private_json or _fetch_private_json
    return fetcher(
        "/0/private/GetAPIKeyInfo",
        api_key=api_key,
        api_secret=api_secret,
        timeout_seconds=timeout_seconds,
    )


def fetch_kraken_extended_balance(
    *,
    api_key: str,
    api_secret: str,
    timeout_seconds: float = 10.0,
    fetch_private_json=None,
) -> dict[str, object]:
    fetcher = fetch_private_json or _fetch_private_json
    return fetcher(
        "/0/private/BalanceEx",
        api_key=api_key,
        api_secret=api_secret,
        timeout_seconds=timeout_seconds,
    )


def _fetch_public_json(
    path: str,
    *,
    timeout_seconds: float = 10.0,
    params: dict[str, object] | None = None,
) -> dict[str, object]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{KRAKEN_PUBLIC_API_BASE}{path}{query}"
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError:
        raise


def _fetch_private_json(
    url_path: str,
    *,
    api_key: str,
    api_secret: str,
    payload: dict[str, object] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    request_payload = dict(payload or {})
    request_payload.setdefault("nonce", str(time.time_ns()))
    encoded_payload = urlencode(request_payload)
    signature = _build_kraken_api_sign(url_path, request_payload, api_secret)
    request = Request(
        f"https://api.kraken.com{url_path}",
        data=encoded_payload.encode("utf-8"),
        headers={
            "API-Key": api_key,
            "API-Sign": signature,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _build_kraken_api_sign(url_path: str, data: dict[str, object], api_secret: str) -> str:
    encoded = urlencode(data)
    nonce = str(data["nonce"])
    message = url_path.encode("utf-8") + hashlib.sha256((nonce + encoded).encode("utf-8")).digest()
    mac = hmac.new(base64.b64decode(api_secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode("utf-8")


def _find_matching_asset_pair(
    normalized_symbol: str,
    asset_pairs: dict[str, object],
) -> dict[str, str] | None:
    target_compact = _compact_symbol(normalized_symbol)
    for pair_key, payload in asset_pairs.items():
        if not isinstance(payload, dict):
            continue
        wsname = payload.get("wsname")
        altname = payload.get("altname")
        candidates = [
            _compact_symbol(normalized_symbol),
            _compact_symbol(str(wsname or "")),
            _compact_symbol(str(altname or "")),
            _compact_symbol(str(pair_key)),
        ]
        if target_compact in candidates[1:]:
            return {
                "pair_key": str(pair_key),
                "wsname": str(wsname) if wsname is not None else "",
                "altname": str(altname) if altname is not None else "",
                "base": str(payload.get("base")) if payload.get("base") is not None else "",
                "quote": str(payload.get("quote")) if payload.get("quote") is not None else "",
                "ordermin": str(payload.get("ordermin")) if payload.get("ordermin") is not None else "",
                "costmin": str(payload.get("costmin")) if payload.get("costmin") is not None else "",
                "tick_size": str(payload.get("tick_size")) if payload.get("tick_size") is not None else "",
                "status": str(payload.get("status")) if payload.get("status") is not None else "",
            }
    return None


def _compact_symbol(symbol: str) -> str:
    return "".join(ch for ch in _normalize_kraken_pair(symbol) if ch.isalnum())


def _pair_value(pair_details: dict[str, str] | None, key: str) -> str | None:
    if not pair_details:
        return None
    value = pair_details.get(key)
    return value or None


def _pair_float(pair_details: dict[str, str] | None, key: str) -> float | None:
    if not pair_details:
        return None
    return _coerce_float(pair_details.get(key))


def _coerce_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_balance_entries(result_payload: dict[str, object]) -> list[KrakenBalanceEntry]:
    entries: list[KrakenBalanceEntry] = []
    for asset, payload in sorted(result_payload.items()):
        if isinstance(payload, dict):
            balance = _coerce_float(payload.get("balance"))
            credit = _coerce_float(payload.get("credit"))
            credit_used = _coerce_float(payload.get("credit_used"))
            hold_trade = _coerce_float(payload.get("hold_trade"))
            available = _coerce_float(payload.get("available"))
            if available is None:
                available = (balance or 0.0) + (credit or 0.0) - (credit_used or 0.0) - (hold_trade or 0.0)
        else:
            balance = _coerce_float(payload)
            credit = 0.0
            credit_used = 0.0
            hold_trade = 0.0
            available = balance

        entries.append(
            KrakenBalanceEntry(
                asset=str(asset),
                balance=balance,
                credit=credit,
                credit_used=credit_used,
                hold_trade=hold_trade,
                available=available,
            )
        )
    return entries


def _build_intent_readiness(
    *,
    intent: ExecutionIntent,
    pair_supported: bool,
    pair_details: dict[str, str] | None,
    authenticated: bool,
    account_snapshot_available: bool,
    balances: tuple[KrakenBalanceEntry, ...],
    local_preflight: ExecutionPreflight,
) -> KrakenIntentReadiness:
    reasons: list[str] = list(local_preflight.reasons)
    funding_asset = None
    funding_basis = None
    required_amount = None
    available_amount = None

    if not authenticated:
        reasons.append("private_auth_not_ready")

    if not pair_supported or not pair_details:
        reasons.append("pair_not_supported")
        return KrakenIntentReadiness(
            allowed=False,
            reasons=tuple(_unique_reasons(reasons)),
            funding_asset=None,
            funding_basis=None,
            required_amount=None,
            available_amount=None,
        )

    if _pair_value(pair_details, "status") not in (None, "online"):
        reasons.append("pair_not_online")

    base_asset = _pair_value(pair_details, "base")
    quote_asset = _pair_value(pair_details, "quote")
    ordermin = _pair_float(pair_details, "ordermin")
    costmin = _pair_float(pair_details, "costmin")

    if intent.side == "buy":
        funding_asset = quote_asset
        funding_basis = "notional"
        required_amount = intent.notional
        if costmin is not None and intent.notional < costmin:
            reasons.append("below_pair_costmin")
    elif intent.side == "sell":
        funding_asset = base_asset
        funding_basis = "quantity"
        required_amount = intent.quantity
        if ordermin is not None and intent.quantity < ordermin:
            reasons.append("below_pair_ordermin")

    if not account_snapshot_available:
        reasons.append("account_snapshot_unavailable")
    elif funding_asset:
        available_amount = _available_for_asset(balances, funding_asset)
        if available_amount is None:
            reasons.append("funding_asset_missing")
        elif required_amount is not None and available_amount < required_amount:
            reasons.append("insufficient_available_balance")

    return KrakenIntentReadiness(
        allowed=not reasons,
        reasons=tuple(_unique_reasons(reasons)),
        funding_asset=funding_asset,
        funding_basis=funding_basis,
        required_amount=required_amount,
        available_amount=available_amount,
    )


def _available_for_asset(
    balances: tuple[KrakenBalanceEntry, ...],
    target_asset: str,
) -> float | None:
    matching = [
        entry.available
        for entry in balances
        if entry.available is not None and _asset_code_candidates(entry.asset) & _asset_code_candidates(target_asset)
    ]
    if not matching:
        return None
    return float(sum(matching))


def _asset_code_candidates(asset: str) -> set[str]:
    base_asset = asset.strip().upper().split(".", 1)[0]
    candidates = {base_asset}

    if base_asset.startswith(("X", "Z")) and len(base_asset) > 3:
        candidates.add(base_asset[1:])

    if base_asset in {"BTC", "XBT", "XXBT"}:
        candidates.update({"BTC", "XBT", "XXBT"})

    return {candidate for candidate in candidates if candidate}


def _unique_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason and reason not in seen:
            ordered.append(reason)
            seen.add(reason)
    return ordered
