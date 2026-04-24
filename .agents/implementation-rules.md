# Implementation Rules - QuantLab

## General Principles
- Follow a **layered architecture**: `data -> indicators -> strategies -> backtest -> execution -> reporting`.
- Keep `main.py` limited to **CLI orchestration only**. Business logic must not live there.
- Prefer **pure functions** for analytics, metrics, and transformation logic whenever possible.
- Use **type hints** for new code and follow **PEP 8** style conventions.
- Favor **small, reversible changes** over broad refactors.

## Architectural Discipline
- Keep responsibilities clearly separated across modules.
- Do not mix strategy logic, portfolio logic, execution logic, and reporting concerns in the same implementation layer.
- New functionality should fit into the existing architecture rather than bypassing it.
- Avoid premature infrastructure complexity unless it clearly improves research quality or maintainability.

## Data and State
- All session outputs must go to the `outputs/` directory.
- Avoid side effects on import.
- Seed randomness to ensure deterministic behavior in backtests.
- Prefer explicit configuration over hidden defaults when behavior affects reproducibility.

## Testing & Quality
- New metrics or core logic **must** include unit tests using `pytest`.
- Handle edge cases explicitly, including:
  - empty datasets
  - missing values where applicable
  - non-standard trade sequences
  - zero-trade scenarios
  - no-op or resume cases
- Documentation (docstrings) is required for public functions and modules.
- If behavior or contracts change, validate the change against existing tests before considering the work complete.

## Desktop Security and Reliability Gates

These gates are mandatory for work under `desktop/`:

- Preserve IPC path hardening:
  - validate and normalize request paths
  - reject absolute URLs
  - require `/`-prefixed relative API paths
  - enforce local token headers for sensitive POST endpoints
- Never use hardcoded fallback credentials (API keys, tokens, secrets) in runtime desktop services.
- Keep smoke tests aligned with the current UI, not legacy-only selectors.
  - `smoke:fallback` and `smoke:real-path` must pass before merge.
- Keep tests synchronized with moved/removed modules in the same PR.
  - broken import paths are blocking failures.
- Enforce canonical filesystem boundary checks using `realpath` for workspace/repo guards.
- Do not log sensitive request payloads or response bodies in IPC paths.

## Reporting and Artifacts
- Reporting outputs in Markdown, JSON, CSV, and charts should remain consistent when they describe the same run, experiment, or portfolio.
- Do not silently change reporting schemas or field meanings.
- Artifact naming should remain stable and predictable across runs.

## Trading Safety
- **Paper mode only** by default.
- Never commit secrets, API keys, credentials, or sensitive environment-specific data.
- Any future live execution capability must remain opt-in, explicit, and outside the default development path.

## Safe Change Protocol

Before implementing any code change, Codex or any execution agent must follow this protocol.

### Step 1 — Inspect
Identify the exact files involved in the task.

Do not modify files outside this set unless explicitly required.

### Step 2 — Verify existing behavior
Confirm whether the requested functionality already exists in the repository.

Do not implement duplicate logic.

### Step 3 — Minimal change
Prefer the smallest change that satisfies the task.

Avoid architectural changes unless the task explicitly requires them.

### Step 4 — Preserve architecture boundaries
Do not move business logic into `main.py`.

Command routing belongs in:
`src/quantlab/cli/`

Core logic belongs in:
`src/quantlab/`

### Step 5 — Validate tests
After implementing a change, ensure:

- `pytest` passes

If tests fail, identify whether:
- behavior changed unintentionally
- tests require adjustment

### Step 6 — Document impact
If the change affects:

- artifact contracts
- CLI behavior
- reporting outputs
- forward evaluation

note this explicitly in the PR summary.

### No hidden side effects
Do not introduce behavior changes unless explicitly requested.

Refactors should preserve observable behavior.

Codex must inspect the repository before implementing changes.

## Scope Control for Codex
- Only modify the files explicitly required for the approved task.
- Do not create alternative paths, duplicated nested folders, or inferred file locations.
- If a target path is ambiguous, stop and report the ambiguity instead of guessing.
- If unrelated modified or untracked files are present, leave them untouched unless explicitly instructed otherwise.

## GitHub
GitHub is the **task and state manager**.

Responsibilities:

- Issues represent tasks
- Project board represents workflow state
- Branches implement work
- Pull requests integrate work

## Development Workflow
QuantLab follows a simplified GitHub workflow:

**1 issue = 1 branch = 1 pull request**

Pull requests should reference the issue using:

`Closes #<NUMBER>`

- Work in a **dedicated branch** for each significant task.
- Do not stage unrelated files.
- Do not use broad staging commands such as `git add .` when task scope is limited.
- Before committing, verify that only intended files are staged.
- Leave a clear summary of what changed, what was tested, and what remains pending.

## Session Log
All research sessions must be logged in:

`.agents/session-log.md`

Each entry should include, when applicable:

- session ID
- timestamp
- command used
- key parameters
- relevant metrics
- links to `outputs/`

This log is the **source of truth** for run history.

## Guiding Rule
QuantLab must remain a **research-first system**: prioritize correctness, reproducibility, and clarity over speed, convenience, or premature platform expansion.

## High-Control Modules

The following modules handle live execution boundaries, broker communication, or irreversible state transitions. They require elevated change discipline.

### Declared high-control modules

| Module | Reason |
|--------|--------|
| `src/quantlab/brokers/hyperliquid.py` | Broker adapter for Hyperliquid. Manages order signing, submission, reconciliation, and ambiguous-state detection. Any bug here can cause unrecoverable production positions. |
| `src/quantlab/cli/hyperliquid_submit_sessions.py` | CLI orchestrator for Hyperliquid submit sessions. Manages session lifecycle, D.2 index counters, reconciliation reporting, and cancel flows. |

### Rules for modifying high-control modules

1. **No refactoring without proven production need.** Do not restructure, rename, or reorganize these files unless a concrete bug or operational requirement demands it. Aesthetic or style refactors are explicitly prohibited.

2. **Mandatory preflight.** Before touching either module, run the full relevant test suite and confirm it passes on `main`. Document the baseline in the PR.

3. **Full diff review required.** Every line changed in a high-control module must appear in the PR diff. No squashing of individual changes. The reviewer must be able to trace each modification to a stated requirement.

4. **Test coverage is mandatory.** Any behavioral change — including edge cases, error paths, and state transitions — must be covered by a new or updated test before the PR is opened.

5. **D.2 contract is non-negotiable.** The following states and counters must remain present and correct at all times:
   - `submitted_remote_identifier_missing` detection in `build_submit_report`
   - `missing_reconciliation_identifiers` error label
   - `reconciliation_required_sessions` and `identifier_missing_sessions` in the index payload

6. **No silent removal of tests.** Deleting or weakening a test that covers a high-control module requires explicit written justification in the PR body. Accidental removal is treated as a regression.

