# Spec — Run Analysis Agent

- **Status**: Draft
- **Depends on**: ADR `NNNN-agent-layer-scope.md` (scope, non-goals), `docs/run-artifact-contract.md` (source of truth for run artifact structure)
- **Agent id**: `run-analysis-agent`
- **Variant**: Analyst (read-only over run artifacts; writes only to its own output area)

## 1. Functional spec

The Run Analysis Agent consumes a single completed run directory produced by
QuantLab and emits a single markdown report describing, in read-only terms,
what that run contains and what is observable about it.

The agent **describes and summarizes**. It does not judge strategies, does not
recommend execution changes, does not compare runs (that is a separate agent),
and does not modify any artifact of the run.

In one sentence: given `outputs/runs/<run_id>/`, produce
`outputs/agent_reports/<run_id>_analysis.md` that faithfully reports what the
run produced, flags anomalies observable from the artifacts themselves, and
lists anything the run-artifact contract expected but is missing.

## 2. Input contract

### 2.1 Location

- **Base path**: `outputs/runs/<run_id>/`
- **run_id**: an identifier matching the pattern defined by
  `docs/run-artifact-contract.md`. Until that pattern is quoted verbatim into
  this spec, the agent treats `<run_id>` as an opaque directory name and
  validates it against a configurable regex (`^[A-Za-z0-9._-]+$` as a
  conservative default).

### 2.2 Expected contents

- Defined by `docs/run-artifact-contract.md`. This spec does not duplicate that
  list. The agent resolves the expected file set at run time by reading the
  run-artifact contract (read-only).
- Any change to the run-artifact contract is a change to this agent's input
  contract by reference. The agent must refuse to run if the run-artifact
  contract version it reads is newer than the version it was validated
  against.

### 2.3 Preconditions

- The base path exists and is a directory.
- The directory is readable.
- At least the **required** files declared by `run-artifact-contract.md` are
  present.
- `run_id` matches the configured regex.
- No symlink in the base path escapes the `outputs/runs/<run_id>/` subtree.

### 2.4 Non-preconditions (explicitly tolerated)

- Optional files per `run-artifact-contract.md` may be missing; their absence
  is reported, not fatal.
- Order of file creation inside the run dir is irrelevant.
- File sizes are not bounded by this contract (the agent may apply its own
  read limits and report truncation).

### 2.5 What the agent reads outside the input path

Read-only, on a closed allow-list:

- `docs/run-artifact-contract.md` — to resolve expected contents.
- `NNNN-agent-layer-scope.md` — to assert boundary invariants at startup.
- Its own spec and version file.

Nothing else. In particular, the agent **does not** read from:

- `src/quantlab/execution/`
- `src/quantlab/brokers/`
- `src/quantlab/pretrade/`
- `src/quantlab/portfolio/`
- any other `outputs/` subtree (e.g. `paper_sessions/`, `broker_*/`)

## 3. Output contract

### 3.1 Location and naming

- **File**: `outputs/agent_reports/<run_id>_analysis.md`
- **Naming rule**: exactly `<run_id>_analysis.md`. No suffixes, no timestamps
  in the filename.
- **Sibling log (required)**: `outputs/agent_reports/<run_id>_analysis.log.json`
  — machine-readable provenance of the run (see §3.4).

### 3.2 Overwrite policy

- If the target markdown already exists, the agent **must not** overwrite it
  silently. Behavior is one of:
  1. Refuse and exit with `E_OUTPUT_EXISTS` (default).
  2. Write to `<run_id>_analysis.md.new` and emit a warning in the log
     (only under an explicit `--replace-pending` flag; outside this spec's
     default path).
- Never delete an existing report.

### 3.3 Report structure (required sections, in order)

1. **Header**
   - `run_id`
   - `report_version` (semantic)
   - `agent_version` (semantic)
   - `generated_at_utc` (ISO-8601)
   - `run_artifact_contract_version` (value read from the contract doc)
   - `input_hash` (hash of the sorted list of input file paths + sizes +
     mtimes; algorithm declared)
2. **Input summary**
   - Files found, by category per the run-artifact contract.
   - Files expected-required that are missing (explicit list; empty list is
     fine and must be shown as such).
   - Files expected-optional that are missing.
   - Files present that are **not** declared by the contract
     (unexpected extras).
3. **Observable facts**
   - Facts extracted from the artifacts themselves, each with a file:line or
     file:field reference. No inference beyond what the artifact states.
4. **Anomalies observable from artifacts**
   - Empty files, truncated files, schema drift against the declared
     contract, timestamps out of order, duplicated entries, encoding issues.
   - Each anomaly has a severity (`info`, `warn`, `error`) and a pointer.
5. **Open questions**
   - Things the agent cannot determine from the artifacts alone and that a
     human or a different agent would need to answer.
6. **Provenance**
   - Agent id and version.
   - Hashes of inputs.
   - Non-determinism disclosure (see §6).
7. **Non-goals acknowledgment** (one-line literal)
   - A fixed sentence stating the agent did not touch execution, brokers,
     pretrade, portfolio. This sentence must be grep-able across all reports.

### 3.4 Sibling log schema (minimum)

- `run_id`
- `agent_version`
- `started_at_utc`, `finished_at_utc`
- `input_path`, `output_path`
- `input_hash`, `output_hash`
- `exit_code`, `error_code` (nullable), `error_message` (nullable)
- `model_id` and `prompt_version` if an LLM was used (null otherwise)
- `files_read` (list of absolute paths; must all fall under the allow-list)
- `files_written` (list; must be exactly the report and this log)

## 4. Naming

- Agent id: `run-analysis-agent` (kebab-case).
- Output file: `<run_id>_analysis.md`.
- Output log: `<run_id>_analysis.log.json`.
- Output area: `outputs/agent_reports/` (created if missing; never created
  anywhere else).
- Configuration file (if any): out of scope for this spec.

## 5. Errors

Every error terminates the agent without writing a partial report, except
where noted.

| Code                          | Meaning                                                                                   | Report written? | Log written? |
|-------------------------------|-------------------------------------------------------------------------------------------|-----------------|--------------|
| `E_INPUT_NOT_FOUND`           | `outputs/runs/<run_id>/` does not exist.                                                  | No              | Yes          |
| `E_INPUT_NOT_DIR`             | Path exists but is not a directory.                                                       | No              | Yes          |
| `E_INPUT_UNREADABLE`          | Permission denied on input.                                                               | No              | Yes          |
| `E_RUN_ID_INVALID`            | `run_id` fails the configured regex.                                                      | No              | Yes          |
| `E_CONTRACT_UNAVAILABLE`      | `docs/run-artifact-contract.md` cannot be read.                                           | No              | Yes          |
| `E_CONTRACT_VERSION_UNKNOWN`  | The run-artifact contract version is newer than the agent was validated against.          | No              | Yes          |
| `E_REQUIRED_FILES_MISSING`    | One or more required files per the run-artifact contract are absent.                      | No              | Yes          |
| `E_SYMLINK_ESCAPE`            | A symlink in the input points outside the run subtree.                                    | No              | Yes          |
| `E_OUTPUT_EXISTS`             | Target report already exists and `--replace-pending` was not set.                         | No              | Yes          |
| `E_OUTPUT_AREA_FORBIDDEN`     | The computed output path falls outside `outputs/agent_reports/`.                          | No              | Yes          |
| `E_BOUNDARY_VIOLATION`        | The agent attempted to read or write outside its allow-list. Hard abort, state logged.    | No              | Yes          |
| `E_INTERNAL`                  | Uncategorized internal error.                                                             | No              | Yes          |
| `W_OPTIONAL_FILES_MISSING`    | Optional files missing. Not fatal; surfaced in the report.                                | Yes             | Yes          |
| `W_UNEXPECTED_EXTRAS`         | Files in input not declared by the contract. Not fatal; surfaced in the report.           | Yes             | Yes          |
| `W_NON_DETERMINISM`           | LLM or other non-deterministic component used. Surfaced in Provenance.                    | Yes             | Yes          |

On any `E_*`, `exit_code != 0`. On pure `W_*`, `exit_code == 0`.

## 6. Invariants

The following must hold for every run of the agent. A violation of any of
these is a defect, not a configuration option.

- **I1 — Read allow-list**: the set of paths actually read is a subset of the
  declared allow-list in §2.5. Reads of `execution/`, `brokers/`, `pretrade/`,
  `portfolio/` or any other `outputs/` subtree are forbidden.
- **I2 — Write allow-list**: the set of paths actually written is exactly
  `{output report, output log}` under `outputs/agent_reports/`. No other
  writes anywhere in the repo.
- **I3 — Idempotency**: given the same input (`input_hash` unchanged) and the
  same agent/model/prompt versions, re-running the agent produces the same
  report content, modulo fields explicitly flagged as non-deterministic in
  §6.a.
- **I4 — Non-deletion**: the agent never deletes any file.
- **I5 — Non-mutation of inputs**: no file inside `outputs/runs/<run_id>/` is
  modified, touched (mtime), or renamed.
- **I6 — Bounded output**: the output report is a single markdown file; the
  output log is a single JSON file. No additional artifacts.
- **I7 — Non-goals statement present**: every report contains the literal
  non-goals acknowledgment sentence from §3.3 #7, grep-able via
  `trading|risk|execution|pretrade|portfolio|brokers`.
- **I8 — Version honesty**: `agent_version` and `run_artifact_contract_version`
  reflect what was actually loaded, not constants.
- **I9 — Failure before partial**: on any `E_*`, no partial report is left
  behind. The log is the only artifact on failure.
- **I10 — No outbound network**: the agent does not perform network I/O. If a
  future variant needs it, that is a different agent with its own spec.

### 6.a Non-determinism

If the agent uses an LLM or any non-deterministic component:

- The report's *Provenance* section must declare `model_id`, `prompt_version`,
  and a `non_determinism: true` flag.
- Idempotency (I3) is weakened to: same input + same model + same prompt +
  same sampling params → same structural layout; free-text prose may vary
  within the declared sections.
- If the agent is purely extractive (no LLM), the report must declare
  `non_determinism: false`, and I3 holds as byte-equivalence on normalized
  output.

## 7. Out of scope for this spec

- Trigger mechanism (manual, CLI, scheduler): separate contract.
- Authentication/authorization of the operator invoking the agent.
- Multi-run comparison (that is a different agent).
- Any write to `outputs/runs/`, `outputs/paper_sessions/`,
  `outputs/broker_*/`.
- Any modification of code under `src/quantlab/execution/`,
  `src/quantlab/brokers/`, `src/quantlab/pretrade/`,
  `src/quantlab/portfolio/`.

## 8. Open questions

- Exact `run_id` regex per `docs/run-artifact-contract.md` (needs verbatim
  quote).
- Exact list of required vs. optional files inside
  `outputs/runs/<run_id>/` (lives in the run-artifact contract, not here).
- Whether the agent is purely extractive or LLM-backed in its first
  implementation (affects §6.a).
- Hash algorithm for `input_hash` / `output_hash` (sha256 proposed,
  not fixed here).
- Retention policy for `outputs/agent_reports/` (who prunes, when).
- CI check that enforces I7 (grep for non-goals sentence) across all
  committed reports, if reports are ever committed.
