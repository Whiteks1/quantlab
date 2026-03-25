from __future__ import annotations

import json
import subprocess
import sys


def run_main(args):
    proc = subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        print(f"\n--- STDOUT ---\n{proc.stdout}")
    if proc.stderr:
        print(f"\n--- STDERR ---\n{proc.stderr}")
    return proc


def test_writes_kraken_dry_run_artifact(tmp_path):
    outdir = tmp_path / "kraken_dry_run_ok"

    result = run_main(
        [
            "--kraken-dry-run-outdir",
            str(outdir),
            "--broker-symbol",
            "ETH-USD",
            "--broker-side",
            "buy",
            "--broker-quantity",
            "0.25",
            "--broker-notional",
            "500",
            "--broker-account-id",
            "acct_demo",
            "--broker-max-notional",
            "1000",
            "--broker-allowed-symbols",
            "ETH/USD,BTC/USD",
        ]
    )

    assert result.returncode == 0
    artifact_path = outdir / "broker_dry_run.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.kraken.dry_run_audit"
    assert payload["adapter_name"] == "kraken"
    assert payload["preflight"]["allowed"] is True
    assert payload["payload"]["pair"] == "ETH/USD"
    assert payload["policy"]["max_notional_per_order"] == 1000.0


def test_persists_rejected_kraken_dry_run_artifact(tmp_path):
    outdir = tmp_path / "kraken_dry_run_rejected"

    result = run_main(
        [
            "--kraken-dry-run-outdir",
            str(outdir),
            "--broker-symbol",
            "SOL-USD",
            "--broker-side",
            "buy",
            "--broker-quantity",
            "0.25",
            "--broker-notional",
            "1500",
            "--broker-account-id",
            "acct_demo",
            "--broker-max-notional",
            "1000",
            "--broker-allowed-symbols",
            "ETH/USD,BTC/USD",
        ]
    )

    assert result.returncode == 0
    artifact_path = outdir / "broker_dry_run.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["preflight"]["allowed"] is False
    assert "max_notional_exceeded" in payload["preflight"]["reasons"]
    assert "symbol_not_allowed" in payload["preflight"]["reasons"]
    assert payload["payload"] is None


def test_missing_required_broker_inputs_fails_cleanly(tmp_path):
    outdir = tmp_path / "kraken_dry_run_invalid"

    result = run_main(
        [
            "--kraken-dry-run-outdir",
            str(outdir),
            "--broker-symbol",
            "ETH-USD",
            "--broker-side",
            "buy",
        ]
    )

    assert result.returncode == 2
    assert "broker_quantity is required" in result.stderr or "broker_quantity is required" in result.stdout
