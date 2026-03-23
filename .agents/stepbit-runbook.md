# QuantLab Runbook for Stepbit

This runbook is the operational source of truth for Stepbit agents and human operators interacting with QuantLab through the current integration-ready CLI.

It is intentionally concise and action-oriented. For deeper technical details, refer to:
- `.agents/stepbit-io-v1.md`
- `.agents/artifact-contracts.md`

---

## 1. Operation: Prepare (Runtime Health)

Before invoking QuantLab, verify that the runtime environment is valid and that the correct interpreter is being used.

### Runtime Requirements
- **Python**: Version >= 3.10
- **Interpreter**: Prefer an explicit interpreter path rather than relying on ambient shell state
- **Dependencies**: The environment must include QuantLab dependencies

### Recommended Invocation Contract
Use an explicit Python interpreter when invoking QuantLab.

Examples:
- **Windows**: `.venv\Scripts\python.exe`
- **POSIX**: `.venv/bin/python`

### Health Verification
QuantLab provides lightweight health/version checks through the CLI.

#### Version Check
```bash
python main.py --version
```


Expected result:

- prints the current QuantLab version as a stable string
- exits with code 0

#### Health Check
```bash
python main.py --check
```

Expected result:

- prints a stable JSON environment summary including:
  - status
  - project_root
  - main_path
  - src_root
  - interpreter
  - venv_active
  - quantlab_import
  - python_version
  - version
- exits with code 0 on success
- exits with code 2 on runtime/config failure
Runtime Resolution Notes

The current CLI includes minimal runtime hardening:

main.py resolves PROJECT_ROOT
src/ is anchored into sys.path
default outdir is anchored to PROJECT_ROOT / "outputs" when --outdir is not explicitly provided

This reduces current-working-directory fragility for local automated execution.

### Smoke Validation

For a reproducible machine-facing smoke validation, use the existing `--json-request` sweep path and verify the generated `report.json.machine_contract`.

Recommended focused test command:

```bash
pytest test/test_cli_health.py test/test_machine_sweep_smoke.py -q
```

2. Operation: Invoke (Headless Execution)

QuantLab should be invoked through the JSON request path for deterministic, machine-driven execution.

Standard Command Pattern
python main.py --json-request '<JSON_PAYLOAD>'
Required JSON Fields
schema_version: must be "1.0"
command: one of:
run
sweep
forward
portfolio
request_id: optional traceability field
params: command-specific arguments mapped into CLI arguments
Example: Basic Backtest (run)
{
  "schema_version": "1.0",
  "request_id": "req_demo_001",
  "command": "run",
  "params": {
    "ticker": "ETH-USD",
    "start": "2023-01-01",
    "end": "2023-12-31",
    "paper": true
  }
}
Example: Sweep
{
  "schema_version": "1.0",
  "request_id": "req_demo_002",
  "command": "sweep",
  "params": {
    "config_path": "configs/example_sweep.yaml"
  }
}
Example: Forward
{
  "schema_version": "1.0",
  "request_id": "req_demo_003",
  "command": "forward",
  "params": {
    "run_dir": "outputs/runs/<run_id>"
  }
}
Notes
The JSON request path is the preferred Stepbit-facing contract.
Unknown commands or invalid schema versions should fail with exit code 2.
3. Operation: Interpret (Results & Artifacts)

Stepbit should interpret both:

the process exit code
the generated machine-readable artifact(s)
Exit Codes

QuantLab uses the following exit code policy:

Exit Code	Classification	Meaning
0	SUCCESS	Task completed normally
1	GENERAL_ERROR	Unexpected crash or unhandled exception
2	INVALID_CONFIG	Invalid JSON payload or CLI/configuration error
3	DATA_ERROR	Missing/invalid market data or invalid data state
4	STRATEGY_ERROR	Strategy-specific failure or parameter/logic error
Canonical Machine-Readable Artifact

The canonical artifact for integration is:

report.json

For session-oriented flows, Stepbit should read the report.json produced in the run/session output directory.

Typical pattern:

outputs/runs/<run_id>/report.json

Depending on mode, the artifact is expected in the actual directory produced by that flow. The important invariant is:

canonical machine-readable artifact name: report.json
Recommended Data Source

When interpreting quantitative results, Stepbit should prioritize the top-level:

"summary": {
  "total_return": ...,
  "sharpe_simple": ...,
  "max_drawdown": ...,
  "trades": ...,
  "win_rate": ...
}

This is the normalized KPI surface intended for machine use.

Legacy Compatibility

Some legacy artifacts may still exist alongside the canonical report.json, for backward compatibility. Stepbit should prefer report.json whenever available.

4. Operation: Recover (Troubleshooting)

Use exit code first, then stderr, then artifacts.

Scenario	Manifestation	Recommended Response
Invalid JSON payload	Exit 2 + ERROR: Invalid --json-request payload...	Fix JSON syntax and retry
Missing command	Exit 2 + ERROR: Missing 'command' in JSON request.	Add top-level command field
Invalid schema version	Exit 2 + ERROR: Unsupported or missing schema_version...	Set schema_version to "1.0"
Unknown command	Exit 2 + ERROR: Unknown command ...	Use one of: run, sweep, forward, portfolio
Missing OHLC / invalid data	Exit 3 + clean stderr message	Verify ticker, date range, and available data
Strategy/data-shape issue	Exit 3 or 4 depending on source	Verify required columns, strategy params, and preconditions
Unexpected crash	Exit 1 + traceback	Treat as unhandled failure and inspect logs/traceback
Recovery Priority
Validate the request payload
Validate runtime health with --check
Re-run with explicit interpreter path
Inspect stderr
Inspect report.json only for successful or partially produced flows where applicable
5. Operational Notes
Reproducibility

For automated execution:

use an explicit interpreter path
use the JSON request path
prefer canonical report.json
rely on exit codes rather than parsing informal stdout
Current Integration Slice

The currently validated integration slice includes:

JSON request ingestion
explicit command dispatch
machine-readable reporting via report.json
structured exit codes
runtime health/version checks
end-to-end smoke validation of the first usable Stepbit ↔ QuantLab flow
Deferred / Not Assumed Here

This runbook does not assume the presence of:

response envelopes on stdout
fingerprint-based response metadata
automatic remote venv provisioning
distributed execution features
future orchestration behaviors not yet implemented
Related Documentation
.agents/stepbit-io-v1.md
.agents/artifact-contracts.md
.agents/session-log.md

## Bloque correcto para `.agents/session-log.md`

```md
## 2026-03-21 — QuantLab Runbook for Stepbit (Issue #26)
- **Session Focus**: Create operational documentation for Stepbit integration and synchronize the internal I/O contract with current repository reality.
- **Tasks Completed**:
  - Created `.agents/stepbit-runbook.md` organized around Prepare, Invoke, Interpret, and Recover.
  - Synchronized `.agents/stepbit-io-v1.md` and `docs/stepbit-io-v1.md` with current implemented behavior.
  - Updated I/O status labels for `schema_version` validation, `request_id` propagation, and exit codes `3` / `4` as implemented.
  - Documented the current runtime preparation and invocation expectations for Stepbit-driven execution.
- **Key Decisions**: The runbook documents current implemented behavior only and does not present future integration features as operational.
- **Next Steps**: Hand over for review; continue with further integration documentati
