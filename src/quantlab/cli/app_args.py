import argparse


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="QuantLab MVP: research-first trading experiment engine."
    )
    # Global / Request params
    parser.add_argument(
        "--json-request",
        help="Pass a V1 Stepbit Request JSON string directly.",
    )
    parser.add_argument(
        "--signal-file",
        help="Path to an append-only JSON Lines file for session signals.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the current QuantLab version and exit.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run lightweight runtime health checks and exit.",
    )

    parser.add_argument("--ticker", default="ETH-USD")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--fee", type=float, default=0.002)

    # Strategy (legacy flags)
    parser.add_argument("--rsi_buy_max", type=float, default=60.0)
    parser.add_argument("--rsi_sell_min", type=float, default=75.0)
    parser.add_argument("--cooldown_days", type=int, default=0)

    # Output
    parser.add_argument(
        "--outdir", default=None, help="Output directory (default: outputs)"
    )
    parser.add_argument("--save_price_plot", action="store_true")

    # Paper broker
    parser.add_argument(
        "--paper",
        action="store_true",
        help="Ejecuta paper broker + CSV de trades",
    )
    parser.add_argument(
        "--initial_cash",
        type=float,
        default=1000.0,
        help="Cash inicial para paper broker",
    )

    # Slippage
    parser.add_argument(
        "--slippage_bps",
        type=float,
        default=8.0,
        help="Slippage fijo en bps (10bps=0.10%%)",
    )
    parser.add_argument("--slippage_mode", default="fixed", choices=["fixed", "atr"])
    parser.add_argument(
        "--k_atr",
        type=float,
        default=0.05,
        help="Sensibilidad slippage ATR (si slippage_mode=atr)",
    )

    # Reporting / Sweep
    parser.add_argument(
        "--report",
        nargs="?",
        const=True,
        help="Genera report para un run (pasa el path) o para la ejecución actual",
    )
    parser.add_argument("--trades_csv", default=None)
    parser.add_argument("--sweep", help="Path a .yaml de configuración para grid search")
    parser.add_argument("--sweep_outdir", default=None)

    # Run navigation (Stage N)
    parser.add_argument(
        "--runs-list",
        metavar="ROOT_DIR",
        default=None,
        help="List all runs in a directory.",
    )
    parser.add_argument(
        "--runs-show",
        metavar="RUN_DIR",
        default=None,
        help="Show details for a single run.",
    )
    parser.add_argument(
        "--runs-best",
        metavar="ROOT_DIR",
        default=None,
        help="Find the best run by a metric.",
    )
    parser.add_argument(
        "--paper-sessions-list",
        metavar="ROOT_DIR",
        default=None,
        help="List paper sessions in a directory.",
    )
    parser.add_argument(
        "--paper-sessions-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single paper session.",
    )
    parser.add_argument(
        "--paper-sessions-health",
        metavar="ROOT_DIR",
        default=None,
        help="Summarize paper session health in a directory.",
    )
    parser.add_argument(
        "--paper-sessions-alerts",
        metavar="ROOT_DIR",
        default=None,
        help="Emit a deterministic alert snapshot for paper sessions in a directory.",
    )
    parser.add_argument(
        "--paper-stale-minutes",
        type=int,
        default=60,
        help="Minutes before a running paper session is treated as stale.",
    )
    parser.add_argument(
        "--paper-sessions-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared paper-session index artifacts in a directory.",
    )
    parser.add_argument(
        "--kraken-dry-run-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken dry-run audit artifact in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-preflight-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Hyperliquid read-only venue preflight artifact in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-account-readiness-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Hyperliquid read-only account/signer readiness artifact in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-signed-action-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Hyperliquid action and signature-envelope artifact in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-submit-signed-action",
        metavar="FILE",
        default=None,
        help="Submit a previously generated hyperliquid_signed_action.json artifact through the supervised Hyperliquid path.",
    )
    parser.add_argument(
        "--hyperliquid-submit-session",
        metavar="FILE",
        default=None,
        help="Submit a previously generated hyperliquid_signed_action.json artifact into a canonical Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-submit-reviewer",
        default=None,
        help="Reviewer name required for supervised Hyperliquid submit.",
    )
    parser.add_argument(
        "--hyperliquid-submit-note",
        default=None,
        help="Optional note attached to a supervised Hyperliquid submit artifact.",
    )
    parser.add_argument(
        "--hyperliquid-submit-confirm",
        action="store_true",
        help="Explicit confirmation required for supervised Hyperliquid submit.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-root",
        metavar="ROOT_DIR",
        default=None,
        help="Root directory for canonical Hyperliquid submit sessions.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-list",
        metavar="ROOT_DIR",
        default=None,
        help="List Hyperliquid submit sessions in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared Hyperliquid submit index artifacts in a directory.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-supervise",
        metavar="SESSION_DIR",
        default=None,
        help="Run bounded continuous supervision over a Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-status",
        metavar="SESSION_DIR",
        default=None,
        help="Refresh normalized post-submit order status for a Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-reconcile",
        metavar="SESSION_DIR",
        default=None,
        help="Reconcile a Hyperliquid submit session against direct order status and open-order surfaces.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-fills",
        metavar="SESSION_DIR",
        default=None,
        help="Refresh a richer fill summary for a Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-cancel",
        metavar="SESSION_DIR",
        default=None,
        help="Submit a supervised cancel request for a canonical Hyperliquid submit session.",
    )
    parser.add_argument(
        "--hyperliquid-cancel-reviewer",
        default=None,
        help="Reviewer name required for supervised Hyperliquid cancel.",
    )
    parser.add_argument(
        "--hyperliquid-cancel-note",
        default=None,
        help="Optional note attached to a supervised Hyperliquid cancel artifact.",
    )
    parser.add_argument(
        "--hyperliquid-cancel-confirm",
        action="store_true",
        help="Explicit confirmation required for supervised Hyperliquid cancel.",
    )
    parser.add_argument(
        "--hyperliquid-supervision-polls",
        type=int,
        default=3,
        help="Number of supervision polling snapshots to take for Hyperliquid monitoring.",
    )
    parser.add_argument(
        "--hyperliquid-supervision-interval-seconds",
        type=float,
        default=2.0,
        help="Sleep interval between Hyperliquid supervision polling snapshots.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-health",
        metavar="ROOT_DIR",
        default=None,
        help="Summarize Hyperliquid submission health across canonical submit sessions.",
    )
    parser.add_argument(
        "--hyperliquid-submit-sessions-alerts",
        metavar="ROOT_DIR",
        default=None,
        help="Emit a deterministic alert snapshot for notable Hyperliquid submit-session states.",
    )
    parser.add_argument(
        "--pretrade-handoff-validate",
        metavar="FILE",
        default=None,
        help="Validate a bounded calculadora_riego_trading QuantLab handoff artifact.",
    )
    parser.add_argument(
        "--pretrade-handoff-validation-outdir",
        metavar="DIR",
        default=None,
        help="Directory where QuantLab should write the local pre-trade handoff validation artifact.",
    )
    parser.add_argument(
        "--broker-evidence-readiness-outdir",
        metavar="DIR",
        default=None,
        help="Write a deterministic readiness artifact for the first supervised broker evidence pass.",
    )
    parser.add_argument(
        "--broker-evidence-corridor",
        choices=["auto", "kraken", "hyperliquid"],
        default="auto",
        help="Broker corridor to evaluate for the first supervised evidence pass.",
    )
    parser.add_argument(
        "--hyperliquid-private-key",
        default=None,
        help="Private key for local Hyperliquid action signing.",
    )
    parser.add_argument(
        "--hyperliquid-private-key-env",
        default="HYPERLIQUID_PRIVATE_KEY",
        help="Environment variable name used to load the Hyperliquid signing private key.",
    )
    parser.add_argument(
        "--kraken-preflight-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken read-only preflight artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-auth-preflight-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken authenticated read-only preflight artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-account-readiness-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken authenticated account snapshot and intent readiness artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-order-validate-outdir",
        metavar="DIR",
        default=None,
        help="Persist a local Kraken validate-only order probe artifact in a directory.",
    )
    parser.add_argument(
        "--kraken-order-validate-session",
        action="store_true",
        help="Persist a canonical broker order-validation session under outputs/broker_order_validations.",
    )
    parser.add_argument(
        "--kraken-preflight-timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for Kraken public preflight probes.",
    )
    parser.add_argument(
        "--hyperliquid-preflight-timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for Hyperliquid public preflight probes.",
    )
    parser.add_argument("--kraken-api-key", default=None)
    parser.add_argument("--kraken-api-secret", default=None)
    parser.add_argument("--kraken-api-key-env", default="KRAKEN_API_KEY")
    parser.add_argument("--kraken-api-secret-env", default="KRAKEN_API_SECRET")
    parser.add_argument("--execution-account-id", default=None)
    parser.add_argument("--execution-signer-id", default=None)
    parser.add_argument(
        "--execution-signer-type",
        choices=["direct", "api_wallet", "agent_wallet"],
        default=None,
    )
    parser.add_argument(
        "--execution-routing-target",
        choices=["account", "subaccount", "vault"],
        default=None,
    )
    parser.add_argument(
        "--execution-transport-preference",
        choices=["rest", "websocket", "either"],
        default=None,
    )
    parser.add_argument("--execution-expires-after", type=int, default=None)
    parser.add_argument("--execution-nonce", type=int, default=None)
    parser.add_argument(
        "--kraken-dry-run-session",
        action="store_true",
        help="Persist a canonical Kraken dry-run session under outputs/broker_dry_runs.",
    )
    parser.add_argument(
        "--broker-dry-runs-root",
        metavar="ROOT_DIR",
        default=None,
        help="Root directory for canonical broker dry-run sessions.",
    )
    parser.add_argument(
        "--broker-dry-runs-list",
        metavar="ROOT_DIR",
        default=None,
        help="List broker dry-run sessions in a directory.",
    )
    parser.add_argument(
        "--broker-dry-runs-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single broker dry-run session.",
    )
    parser.add_argument(
        "--broker-dry-runs-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared broker dry-run index artifacts in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-root",
        metavar="ROOT_DIR",
        default=None,
        help="Root directory for canonical broker order-validation sessions.",
    )
    parser.add_argument(
        "--broker-order-validations-list",
        metavar="ROOT_DIR",
        default=None,
        help="List broker order-validation sessions in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-show",
        metavar="SESSION_DIR",
        default=None,
        help="Show details for a single broker order-validation session.",
    )
    parser.add_argument(
        "--broker-order-validations-health",
        metavar="ROOT_DIR",
        default=None,
        help="Summarize broker submission health in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-alerts",
        metavar="ROOT_DIR",
        default=None,
        help="Emit a deterministic alert snapshot for broker submission sessions in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-index",
        metavar="ROOT_DIR",
        default=None,
        help="Refresh the shared broker order-validation index artifacts in a directory.",
    )
    parser.add_argument(
        "--broker-order-validations-approve",
        metavar="SESSION_DIR",
        default=None,
        help="Approve a broker order-validation session locally.",
    )
    parser.add_argument(
        "--broker-order-validations-bundle",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a pre-submit bundle from an approved broker order-validation session.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-gate",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a supervised submit gate artifact from a pre-submit bundle.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-stub",
        metavar="SESSION_DIR",
        default=None,
        help="Generate a supervised submit stub artifact from a submit gate.",
    )
    parser.add_argument(
        "--broker-order-validations-submit-real",
        metavar="SESSION_DIR",
        default=None,
        help="Submit a real Kraken order from a supervised submit gate and persist the response artifact.",
    )
    parser.add_argument(
        "--broker-order-validations-reconcile",
        metavar="SESSION_DIR",
        default=None,
        help="Reconcile an existing broker submit response against Kraken order state.",
    )
    parser.add_argument(
        "--broker-order-validations-status",
        metavar="SESSION_DIR",
        default=None,
        help="Refresh normalized post-submit order status for a broker order-validation session.",
    )
    parser.add_argument(
        "--broker-approval-reviewer",
        default=None,
        help="Reviewer name/id for local broker approval actions.",
    )
    parser.add_argument(
        "--broker-approval-note",
        default=None,
        help="Optional note for local broker approval actions.",
    )
    parser.add_argument(
        "--broker-submit-reviewer",
        default=None,
        help="Reviewer name/id for supervised submit gate actions.",
    )
    parser.add_argument(
        "--broker-submit-note",
        default=None,
        help="Optional note for supervised submit gate actions.",
    )
    parser.add_argument(
        "--broker-submit-confirm",
        action="store_true",
        help="Explicit confirmation flag required for supervised submit gate and real submit actions.",
    )
    parser.add_argument(
        "--broker-submit-live",
        action="store_true",
        help="Explicit live-submit flag required before sending a real broker order.",
    )
    parser.add_argument("--broker-symbol", default=None)
    parser.add_argument("--broker-side", default=None)
    parser.add_argument("--broker-quantity", type=float, default=None)
    parser.add_argument("--broker-notional", type=float, default=None)
    parser.add_argument("--broker-account-id", default=None)
    parser.add_argument("--broker-strategy-id", default=None)
    parser.add_argument("--broker-max-notional", type=float, default=None)
    parser.add_argument("--broker-allowed-symbols", default=None)
    parser.add_argument("--broker-kill-switch", action="store_true")
    parser.add_argument("--broker-allow-missing-account-id", action="store_true")
    parser.add_argument(
        "--metric",
        default="sharpe_simple",
        help="Metric to rank by (used with --runs-best, --best-from).",
    )

    # Stage J/K/L/M Flags (legacy — use --runs-* equivalents)
    parser.add_argument(
        "--list-runs",
        metavar="ROOT_DIR",
        default=None,
        help="[Deprecated] Use --runs-list.",
    )
    parser.add_argument(
        "--best-from",
        metavar="ROOT_DIR",
        default=None,
        help="[Deprecated] Use --runs-best.",
    )
    parser.add_argument("--compare", nargs="+", metavar="RUN_DIR")
    parser.add_argument("--advanced-report", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-eval", metavar="RUN_DIR", default=None)
    parser.add_argument("--forward-start", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-end", metavar="YYYY-MM-DD", default=None)
    parser.add_argument("--forward-outdir", metavar="DIR", default=None)
    parser.add_argument("--forward-metric", default="sharpe_simple")
    parser.add_argument("--resume-forward", metavar="SESSION_DIR", default=None)
    parser.add_argument("--portfolio-report", metavar="ROOT_DIR", default=None)
    parser.add_argument(
        "--portfolio-mode",
        default="raw_capital",
        choices=["raw_capital", "equal_weight", "custom_weight"],
    )
    parser.add_argument("--portfolio-weights", metavar="JSON_FILE", default=None)
    parser.add_argument("--portfolio-top-n", type=int, default=None)
    parser.add_argument("--portfolio-rank-metric", default="total_return")
    parser.add_argument("--portfolio-min-return", type=float, default=None)
    parser.add_argument("--portfolio-max-drawdown", type=float, default=None)
    parser.add_argument("--portfolio-include-tickers", default=None)
    parser.add_argument("--portfolio-exclude-tickers", default=None)
    parser.add_argument("--portfolio-include-strategies", default=None)
    parser.add_argument("--portfolio-exclude-strategies", default=None)
    parser.add_argument("--portfolio-latest-per-source-run", action="store_true")
    parser.add_argument("--portfolio-compare", metavar="ROOT_DIR", default=None)
    return parser
