"""
CLI handler for read-only broker preflight probes.
"""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.brokers import KrakenBrokerAdapter
from quantlab.errors import ConfigError


def handle_broker_preflight_commands(args) -> dict[str, object] | bool:
    """
    Handle broker preflight CLI commands.

    Commands:
    - ``--kraken-preflight-outdir <DIR>`` : run read-only Kraken readiness probes and persist artifact
    """
    if not getattr(args, "kraken_preflight_outdir", None):
        return False

    symbol = getattr(args, "broker_symbol", None) or getattr(args, "ticker", None)
    if not isinstance(symbol, str) or not symbol.strip():
        raise ConfigError("broker_symbol or ticker must be provided for Kraken preflight.")

    outdir = Path(args.kraken_preflight_outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    adapter = KrakenBrokerAdapter()
    report = adapter.build_public_preflight_report(
        symbol,
        timeout_seconds=float(getattr(args, "kraken_preflight_timeout", 10.0)),
    ).to_dict()

    artifact_path = outdir / "broker_preflight.json"
    with open(artifact_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("\nKraken preflight generated:\n")
    print(f"  artifact_path        : {artifact_path}")
    print(f"  public_api_reachable : {report['public_api_reachable']}")
    print(f"  pair_supported       : {report['pair_supported']}")

    return {
        "status": "success",
        "mode": "broker_preflight",
        "adapter_name": report["adapter_name"],
        "artifact_path": str(artifact_path),
        "pair_supported": report["pair_supported"],
        "public_api_reachable": report["public_api_reachable"],
    }
