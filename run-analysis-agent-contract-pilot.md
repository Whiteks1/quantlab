# Spec — Run Analysis Agent (Pilot)

- **Status**: Draft (pilot-scoped)
- **Scope**: Pilot only. Extractive, read-only, single-run.
- **Depends on**: ADR `NNNN-agent-layer-scope.md` (scope, non-goals).
- **Does not depend at runtime on**: any other document, including
  `docs/run-artifact-contract.md`. The pilot's input allow-list is frozen in
  this spec (see §2.2).
- **Agent id**: `run-analysis-agent`
- **Variant**: Analyst — extractive (no LLM, no stochastic components).
- **Supersedes**: prior draft `run-analysis-agent-contract.md`.

## 1. Functional spec

The Run Analysis Agent (pilot) consumes a single completed run directory
produced by QuantLab and emits a single markdown report describing, in
read-only, extractive terms, what that run contains.

Extractive means: every statement in the report is a direct read-off of a
field or a file in the input, or a mechanical derivation from such reads
(count, presence/absence, hash, timestamp diff). The pilot does **not**
invoke an LLM, does not call external services, and contains no stochastic
component.

The agent **describes**. It does not judge strategies, does not recommend
execution changes, does not compare runs, and does not modify any artifact
of the run.

In one sentence: given `outputs/runs/<run_id>/`, produce
`outputs/agent_reports/<run_id>_analysis.md` that faithfully enumerates the
allow-listed files found, reports required files that are missing, and
flags observable anomalies — without interpretation.

## 2. Input contract

### 2.1 Location

- **Base path**: `outputs/runs/<run_id>/`
- **run_id**: opaque directory name validated against a conservative regex
  (`^[A-Za-z0-9._-]+$`). A stricter pattern can be introduced in a later
  revision without breaking this contract.

### 2.2 Allow-list of supported inputs (frozen for the pilot)

The pilot reads **only** files that match one of the roles below. Files
outside the allow-list are reported as *unexpected extras* (warning, not
fatal — see §5). The pilot does not recurse into subdirectories beyond the
base path unless a role below explicitly declares a subdirectory.

| Role                    | Filename (pilot)             | Required | Format   | Notes                                                |
|-------------------------|------------------------------|----------|----------|------------------------------------------------------|
| Run manifest / metadata | `<MANIFEST_FILENAME>`        | required | JSON     | Holds run identifier, timestamps, params.            |
| Performance summary     | `<METRICS_FILENAME>`         | required | JSON     | Aggregated metrics of the run.                       |
| Run log                 | `<RUNLOG_FILENAME>`          | optional | text/json| Execution log emitted by the runner.                 |
| Config snapshot         | `<CONFIG_FILENAME>`          | optional | JSON/YAML| Config as used by the run.                           |
| Equity / PnL series     | `<EQUITY_FILENAME>`          | optional | CSV      | Time series of equity or pnl.                        |
| Trade / order record    | `<TRADES_FILENAME>`          | optional | CSV      | Per-trade or per-order rows.                         |
| Attachments subdir      | `attachments/` (subdirectory)| optional | —        | Auxiliary artifacts; files enumerated, not parsed.   |

**Placeholder resolution.** The six `<*_FILENAME>` slots are placeholders.
They must be replaced by verbatim filenames before the pilot moves from
*Draft* to *Ready*. The source of those filenames is a one-time manual
listing of an existing run directory (or a paste of the relevant portion of
`docs/run-artifact-contract.md`). Until the placeholders are resolved, the
pilot implementation must refuse to run with `E_ALLOWLIST_UNRESOLVED`.

**Required files.** Exactly two: `<MANIFEST_FILENAME>` and
`<METRICS_FILENAME>`. Any other file is optional for this pilot.

### 2.3 Preconditions

- The base path exists, is a directory, and is readable.
- `run_id` matches the configured regex.
- No symlink in the base path escapes the `outputs/runs/<run_id>/` subtree.
- Both required files (§2.2) are present and non-empty.
- The allow-list placeholders have been resolved.

### 2.4 Non-preconditions (explicitly tolerated)

- Any or all optional files may be missing; their absence is reported, not
  fatal.
- `attachments/` may be absent, empty, or contain arbitrary filenames; the
  pilot enumerates them but does not parse their contents.
- File sizes are not bounded by this contract. The pilot may apply its own
  read limits per file and must report truncation in the anomalies section.

### 2.5 What the agent reads outside the input path

Read-only, on a closed allow-list:

- `NNNN-agent-layer-scope.md` — to assert boundary invariants at startup.
- Its own embedded version/spec identifier.

Nothing else. In particular, the pilot **does not** read from:

- `src/quantlab/execution/`
- `src/quantlab/brokers/`
- `src/quantlab/pretrade/`
- `src/quantlab/portfolio/`
- `docs/run-artifact-contract.md` (no runtime dependency; the allow-list is
  frozen in §2.2)
- any other `outputs/` subtree (e.g. `paper_sessions/`, `broker_*/`)
- the network

## 3. Output contract

### 3.1 Location and naming

- **File**: `outputs/agent_reports/<run_id>_analysis.md`
- **Naming rule**: exactly `<run_id>_analysis.md`. No suffixes, no
  timestamps in the filename.
- **Sibling log (required)**:
  `outputs/agent_reports/<run_id>_analysis.log.json` — machine-readable
  provenance (see §3.4).

### 3.2 Overwrite policy

- If the target markdown already exists, the agent **must not** overwrite it
  silently. Behavior is one of:
  1. Refuse and exit with `E_OUTPUT_EXISTS` (default).
  2. Write to `<run_id>_analysis.md.new` and emit a warning in the log
     (only under an explicit `--replace-pending` flag; outside this
     spec's default path).
- Never delete an existing report.

### 3.3 Report structure (required sections, in order)

1. **Header**
   - `run_id`
   - `report_version` (semantic)
   - `agent_version` (semantic)
   - `spec_version` (semantic; identifies this spec)
   - `generated_at_utc` (ISO-8601)
   - `input_hash` (hash of the sorted list of input file paths + sizes +
     mtimes; algorithm declared)
2. **Input summary**
   - Allow-listed files found (by role).
   - Required files missing (explicit list; empty list is fine and must be
     shown as such — this branch is only reachable under
     `W_REQUIRED_MISSING_FORCE`, which is not defined by default; see §5).
   - Optional files missing.
   - Files present that are **not** declared by the allow-list
     (unexpected extras).
3. **Observable facts**
   - Facts extracted directly from allow-listed files, each with a
     `file:line` or `file:field` reference. No inference beyond what the
     artifact states.
4. **Anomalies observable from artifacts**
   - Empty files, truncated files, timestamps out of order, duplicated
     entries within a file, encoding issues, zero-byte files in
     `attachments/`.
   - Each anomaly has a severity (`info`, `warn`, `error`) and a pointer.
5. **Open questions**
   - Things the pilot cannot determine from the allow-list alone and that a
     human or a different agent would need to answer.
6. **Provenance**
   - Agent id and version.
   - Spec version.
   - Input hash and output hash.
   - `non_determinism: false` (pilot is extractive by contract).
7. **Non-goals acknowledgment** (one-line literal)
   - A fixed sentence stating the agent did not touch execution, brokers,
     pretrade, portfolio. This sentence must be grep-able across all
     reports (see I7).

### 3.4 Sibling log schema (minimum)

- `run_id`
- `agent_version`
- `spec_version`
- `started_at_utc`, `finished_at_utc`
- `input_path`, `output_path`
- `input_hash`, `output_hash`
- `exit_code`, `error_code` (nullable), `error_message` (nullable)
- `files_read` (list of absolute paths; must all fall under the allow-list
  of §2.5 and the role allow-list of §2.2)
- `files_written` (list; must be exactly the report and this log)

Fields intentionally excluded from the pilot log (would only apply to a
non-extractive variant): `model_id`, `prompt_version`, sampling parameters.

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
| `E_ALLOWLIST_UNRESOLVED`      | Placeholder filenames in §2.2 have not been replaced.                                     | No              | Yes          |
| `E_REQUIRED_FILES_MISSING`    | `<MANIFEST_FILENAME>` or `<METRICS_FILENAME>` is absent or empty.                         | No              | Yes          |
| `E_SYMLINK_ESCAPE`            | A symlink in the input points outside the run subtree.                                    | No              | Yes          |
| `E_OUTPUT_EXISTS`             | Target report already exists and `--replace-pending` was not set.                         | No              | Yes          |
| `E_OUTPUT_AREA_FORBIDDEN`     | The computed output path falls outside `outputs/agent_reports/`.                          | No              | Yes          |
| `E_BOUNDARY_VIOLATION`        | The agent attempted to read or write outside its allow-list. Hard abort, state logged.   | No              | Yes          |
| `E_INTERNAL`                  | Uncategorized internal error.                                                             | No              | Yes          |
| `W_OPTIONAL_FILES_MISSING`    | Optional files missing. Not fatal; surfaced in the report.                                | Yes             | Yes          |
| `W_UNEXPECTED_EXTRAS`         | Files in input not declared by the allow-list. Not fatal; surfaced in the report.         | Yes             | Yes          |
| `W_TRUNCATED_READ`            | A file was read up to an internal limit; truncation surfaced in the report.               | Yes             | Yes          |

On any `E_*`, `exit_code != 0`. On pure `W_*`, `exit_code == 0`.

Removed from the prior draft (not applicable to the pilot):
`E_CONTRACT_UNAVAILABLE`, `E_CONTRACT_VERSION_UNKNOWN`, `W_NON_DETERMINISM`.

## 6. Invariants

The following must hold for every run of the pilot. A violation of any of
these is a defect, not a configuration option.

- **I1 — Read allow-list**: the set of paths actually read is a subset of
  the union of §2.2 (roles under the input base path) and §2.5 (external
  reads). Reads of `execution/`, `brokers/`, `pretrade/`, `portfolio/` or
  any other `outputs/` subtree are forbidden.
- **I2 — Write allow-list**: the set of paths actually written is exactly
  `{output report, output log}` under `outputs/agent_reports/`. No other
  writes anywhere in the repo.
- **I3 — Deterministic output**: given the same input (`input_hash`
  unchanged) and the same `agent_version` and `spec_version`, re-running
  the pilot produces byte-equivalent output under a declared normalization
  (line endings, trailing whitespace, timestamp field replaced by a stable
  marker during test).
- **I4 — Non-deletion**: the agent never deletes any file.
- **I5 — Non-mutation of inputs**: no file inside `outputs/runs/<run_id>/`
  is modified, touched (mtime), or renamed.
- **I6 — Bounded output**: the output report is a single markdown file; the
  output log is a single JSON file. No additional artifacts.
- **I7 — Non-goals statement present**: every report contains the literal
  non-goals acknowledgment sentence from §3.3 #7, grep-able via
  `trading|risk|execution|pretrade|portfolio|brokers`.
- **I8 — Version honesty**: `agent_version` and `spec_version` reflect what
  was actually loaded, not constants.
- **I9 — Failure before partial**: on any `E_*`, no partial report is left
  behind. The log is the only artifact on failure.
- **I10 — No outbound network**: the agent does not perform network I/O.
- **I11 — Extractive only**: the pilot uses no LLM and no stochastic
  component. Any future variant that relaxes I11 requires a superseding
  spec.
- **I12 — No runtime contract discovery**: the pilot does not read any
  contract document at runtime to determine its allow-list. The allow-list
  of §2.2 is frozen in this spec.

## 7. Out of scope for this spec

- Trigger mechanism (manual, CLI, scheduler): separate contract.
- Authentication/authorization of the operator invoking the agent.
- Multi-run comparison (different agent, different spec).
- Any write to `outputs/runs/`, `outputs/paper_sessions/`,
  `outputs/broker_*/`.
- Any modification of code under `src/quantlab/execution/`,
  `src/quantlab/brokers/`, `src/quantlab/pretrade/`,
  `src/quantlab/portfolio/`.
- Any non-extractive analysis (LLM, statistical inference beyond counts
  and presence/absence).
- Runtime reading of `docs/run-artifact-contract.md` or any other contract
  document.

## 8. Open questions

- Verbatim filenames for the six `<*_FILENAME>` placeholders in §2.2
  (bloqueante antes de implementación).
- Exact `run_id` regex if the pilot regex needs tightening.
- Hash algorithm for `input_hash` / `output_hash` (sha256 proposed,
  not fixed here).
- Retention policy for `outputs/agent_reports/` (who prunes, when).
- Whether `outputs/agent_reports/` should be gitignored or versioned; if
  versioned, CI check enforcing I7 across all committed reports.
- Normalization rules for I3 byte-equivalence testing (line endings,
  whitespace, timestamp masking).
