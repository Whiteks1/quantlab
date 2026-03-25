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
            }
    return None


def _compact_symbol(symbol: str) -> str:
    return "".join(ch for ch in _normalize_kraken_pair(symbol) if ch.isalnum())
