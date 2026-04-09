# Session Log - QuantLab

## 2026-04-09 — Single-Scope Merge Discipline Rule (Issue #277)
- **Session Focus**: Add the minimum written rule needed to stop multi-scope technical branches from becoming normal practice.
- **Tasks Completed**:
  - Updated `AGENTS.md` to state that one branch should carry one technical story and that mixed-scope PRs are not accepted by default.
  - Updated `CONTRIBUTING.md` to define the same rule at PR level and require explicit written justification for any core/desktop/docs/CI/cleanup mix.
- **Key Decisions**:
  - This slice adds only a minimal governance rule in existing authoritative workflow surfaces.
  - The goal is not process overhead; it is to make unjustified multi-scope PRs visibly out of policy.
- **Validation Notes**:
  - Verified by checking that the rule is now present in both `AGENTS.md` and `CONTRIBUTING.md`.

## 2026-04-09 — D.2 State Alignment and Stale Governance Cleanup (Issue #307)
- **Session Focus**: Bring `.agents/current-state.md` back into sync with the Hyperliquid D.2 work already merged into `main`, and clear stale governance noise.
- **Tasks Completed**:
  - Updated `.agents/current-state.md` to reflect the April D.2 slices already merged for idempotency, ambiguous-submit labeling, reconciliation precedence, aggregate visibility, aggregate alert priority, and critical-priority regression coverage.
  - Removed the stale `strategy_research.md` debt note because that duplicate workflow file no longer exists in the tree.
  - Reframed Stage D.2 as residual hardening-by-evidence rather than broad execution expansion by default.
  - Closed stale governance issue #284 because the referenced `broker_preflight` blocker was already resolved by later merged Motor/Core work.
- **Key Decisions**:
  - This is a state/governance cleanup slice only; it does not change runtime, contracts, or desktop behavior.
  - D.2 remains the active execution-safety stage, but new slices now require a demonstrated operator-safety gap instead of roadmap inertia alone.
- **Validation Notes**:
  - Verified by comparing `.agents/current-state.md` and `.agents/session-log.md` against the merged April D.2 history on `main`.

## 2026-04-09 — Hyperliquid Critical Alert Precedence Coverage (Issue #305)
- **Session Focus**: Lock the aggregate Hyperliquid alert-priority policy with focused regressions for critical post-submit states.
- **Tasks Completed**:
  - Added helper fixtures in `test/test_hyperliquid_submit_sessions.py` for reconciliation and cancel-response artifacts.
  - Added regression coverage proving aggregate health prefers `HYPERLIQUID_ORDER_REJECTED` over a newer `HYPERLIQUID_CANCEL_REQUEST_FAILED`.
  - Added regression coverage proving aggregate alerts prefer `HYPERLIQUID_CANCEL_REQUEST_FAILED` over a newer `HYPERLIQUID_SUBMIT_REQUEST_FAILED`.
- **Key Decisions**:
  - This slice changes no runtime behavior; it locks the explicit priority map already present in the Hyperliquid aggregate alert surface.
  - Coverage targets representative critical states across reconciliation, cancel, and submit branches to catch recency regressions and priority drift.
- **Validation Notes**:
  - Verified with `PYTHONPATH=<worktree>/src python -m pytest -q test/test_hyperliquid_submit_sessions.py`.

## 2026-04-09 — Hyperliquid Aggregate Alert Priority (Issue #303)
- **Session Focus**: Make aggregate Hyperliquid submit alerts surface operator urgency instead of picking the newest alert by timestamp alone.
- **Tasks Completed**:
  - Updated `src/quantlab/cli/hyperliquid_submit_sessions.py` so aggregate `latest_alert_*` selection uses explicit alert priority plus severity before recency.
  - Added focused regression tests proving a critical identifier-missing acknowledgement outranks a newer warning and a newer generic unknown-status alert in aggregate surfaces.
- **Key Decisions**:
  - This slice changes only aggregate alert prioritization; it does not alter per-session alert emission or the underlying D.2 state machine.
  - Priority is encoded explicitly for known Hyperliquid submit alert codes so operator-facing aggregate surfaces reflect urgency deterministically.
- **Validation Notes**:
  - Verified with `PYTHONPATH=<worktree>/src python -m pytest -q test/test_hyperliquid_submit_sessions.py`.

## 2026-04-09 — Hyperliquid Aggregate Ambiguity Visibility (Issue #300)
- **Session Focus**: Make aggregate Hyperliquid submit visibility call out the new D.2 ambiguity states explicitly instead of burying them in generic counts.
- **Tasks Completed**:
  - Updated `src/quantlab/cli/hyperliquid_submit_sessions.py` health output to expose explicit counts for `reconciliation_required` sessions and `submitted_remote_identifier_missing` submits.
  - Updated `src/quantlab/reporting/hyperliquid_submit_index.py` to expose the same counts in JSON and to render them in the Markdown summary.
  - Added focused tests covering the new aggregate counts in both health and index surfaces.
- **Key Decisions**:
  - This slice is visibility-only; it does not change any per-session state machine.
  - The new counts are additive and explicit, so operators do not need to infer D.2 ambiguity from raw maps alone.
- **Validation Notes**:
  - Verified with `python -m pytest -q test/test_hyperliquid_submit_sessions.py`.

## 2026-04-09 — Hyperliquid Status Refresh Reconciliation Precedence (Issue #298)
- **Session Focus**: Prevent `--hyperliquid-submit-sessions-status` from degrading canonical session status when a prior reconciliation already knows the effective remote order state.
- **Tasks Completed**:
  - Updated `src/quantlab/cli/hyperliquid_submit_sessions.py` so status refresh preserves the reconciled effective state and alert posture when the fresh order-status probe is still `unknown`.
  - Added a regression test proving `session_status.json` stays aligned with the known reconciliation instead of regressing to `unknown`.
- **Key Decisions**:
  - The fresh `order_status` artifact is still written as-is; only the effective session summary and alerts keep reconciliation precedence.
  - This slice does not redesign reporting or remove the raw order-status signal; it only prevents misleading regression in the canonical session status file.
- **Validation Notes**:
  - Verified with `python -m pytest -q test/test_hyperliquid_submit_sessions.py`.

## 2026-04-09 — Hyperliquid Unreconcilable Submit Acknowledgement Labeling (Issue #295)
- **Session Focus**: Tighten Stage D.2 submit safety by making ambiguous successful Hyperliquid submit acknowledgements explicit when they cannot be reconciled immediately.
- **Tasks Completed**:
  - Updated `src/quantlab/brokers/hyperliquid.py` so a remote `status: ok` response without both `oid` and `cloid` is labeled `submitted_remote_identifier_missing` instead of looking like a normal `submitted_remote`.
  - Updated `src/quantlab/cli/broker_preflight.py` so canonical submit sessions route that state to `reconciliation_required`.
  - Updated `src/quantlab/cli/hyperliquid_submit_sessions.py` to emit a dedicated critical alert for the missing-identifier case.
  - Added focused adapter, broker-preflight, and session-alert tests for the new behavior.
- **Key Decisions**:
  - The slice preserves the fact that remote submit was called and may have succeeded; it only removes the false sense of normal post-submit traceability.
  - The ambiguous case is treated as an operator-visible reconciliation problem, not as a generic rejection.
- **Validation Notes**:
  - Verified with `PYTHONPATH=<worktree>/src python -m pytest -q test/test_hyperliquid_broker_adapter.py test/test_cli_broker_preflight.py test/test_hyperliquid_submit_sessions.py`.

- 2026-04-09: Created the Desktop/UI UX remediation issue block after consolidating desktop findings into three root problems: workstation containment, right-rail support-lane clarity, and decision guidance across runs surfaces. Opened GitHub issues #286, #287, and #288 to map the next implementation sequence before touching renderer behavior.
- 2026-04-09: Created a Desktop/UI issue block for the right-rail support lane after confirming that the upper quick-entry box and the lower assistant panel currently share the same output log and therefore duplicate semantics. Added issues #218–#221 to separate quick commands from assistant history, clarify Stepbit routing, and reduce right-rail noise before touching renderer behavior.
## 2026-04-09 — CLI Health Worktree-Safe Check (Issue #293)
- **Session Focus**: Remove a false negative in CLI health validation so `--check` remains trustworthy across non-canonical worktree names.
- **Tasks Completed**:
  - Updated `test/test_cli_health.py` to assert stable path invariants from `--check` instead of assuming the checkout folder must be named `quant_lab` or `quantlab`.
  - Kept the runtime health payload unchanged because it already exposes the correct machine-facing fields: `project_root`, `main_path`, and `src_root`.
- **Key Decisions**:
  - The health surface should report the real filesystem path; tests should validate truthfulness, not enforce a naming convention on checkouts.
  - This slice stays test-only and does not change CLI behavior.
- **Validation Notes**:
  - Verified with `python -m pytest -q test/test_cli_health.py`.

- 2026-04-09: Started issue #275 in a clean Desktop/UI worktree from `main`. Scope is limited to desktop validation semantics: explicit fallback smoke, explicit real-path smoke, and CI wiring that makes the distinction visible without mixing in renderer or core changes.
- 2026-04-09: Expanded issue #275 scope minimally to include `desktop/preload.js` because current `main` still carries the known preload bridge syntax regression. Without that blocker fix, both fallback and real-path smoke stop at `bridgeReady: false`, so the desktop validation slice cannot be validated.
- 2026-04-09: Completed local validation for issue #275. `desktop/package.json` now exposes explicit `smoke:fallback` and `smoke:real-path` scripts, `desktop/scripts/smoke.js` and `desktop/main.js` distinguish the two semantics, and both modes passed locally after restoring the preload bridge blocker fix. CI wiring was updated in `.github/workflows/ci.yml` to add a dedicated `desktop-real-path` job.

## 2026-04-09 — Hyperliquid Canonical Submit Replay Guard (Issue #291)
- **Session Focus**: Tighten Stage D.2 idempotency on the first supervised Hyperliquid submit path by blocking duplicate canonical session replays.
- **Tasks Completed**:
  - Added a canonical-session guard in `src/quantlab/cli/broker_preflight.py` so `--hyperliquid-submit-session` now fails early if the derived session already has `hyperliquid_submit_response.json`.
  - Kept the scope narrow to the canonical session path; the sibling one-off artifact path was left unchanged.
  - Added targeted pytest coverage to prove the duplicate replay is rejected and does not re-call the adapter submit path.
- **Key Decisions**:
  - The canonical session identity remains the existing derived `session_id`; this slice does not introduce a new replay token or override flag.
  - Once a canonical session already has a persisted submit response, the safe operator path is inspect/reconcile, not blind resubmit.
  - This is an idempotency-safety guard, not a broader retry policy.
- **Validation Notes**:
  - Verified with `PYTHONPATH=<worktree>/src python -m pytest -q test/test_cli_broker_preflight.py test/test_hyperliquid_broker_adapter.py test/test_hyperliquid_submit_sessions.py`.

## 2026-04-09 — Stepbit External-Provider Compatibility Smoke (Issue #281)
- **Session Focus**: Consolidate a QuantLab-owned smoke for the external Stepbit provider boundary without widening the runtime surface.
- **Tasks Completed**:
  - Added `test/test_stepbit_external_provider_compat.py` to cover external-consumer success paths for `run` and `sweep`.
  - Added a deterministic failure-path assertion for `sweep` when the canonical `report.json` is missing.
  - Fixed session signalling so `SESSION_COMPLETED.mode` remains the public command type instead of being overwritten by narrower artifact modes such as `grid`.
- **Key Decisions**:
  - The external boundary remains the existing CLI contract: `--json-request`, optional `--signal-file`, and canonical `report.json.machine_contract`.
  - The public signal `mode` field must stay stable as the command type (`run`, `sweep`, etc.); internal artifact modes stay available inside `report.json.machine_contract.mode`.
  - This slice stays test-first and contract-oriented; no new integration surface was introduced.
- **Validation Notes**:
  - Verified with `python -m pytest -q test/test_stepbit_external_provider_compat.py test/test_machine_sweep_smoke.py test/test_signals.py test/test_cli_run.py test/test_sweep_contract.py`
  - Verified broader local compatibility with `python -m pytest -q -k "not test_check"`; local `test_check` remains worktree-path-sensitive because this checkout lives under `quant_lab-issue-281/`.

## 2026-03-24 — Canonical Run Machine Contract (Issue #62)
- **Session Focus**: Reduce the remaining contract asymmetry between plain `run` and `sweep` inside canonical `report.json`.
- **Tasks Completed**:
  - Extended `src/quantlab/reporting/run_report.py` so successful plain `run` reports now expose `report.json.machine_contract`.
  - Kept top-level `summary` / `kpi_summary` behavior unchanged for backward compatibility.
  - Added contract-oriented tests covering the canonical `run.machine_contract` shape and CLI-produced run reports.
  - Updated `.agents` docs and the Stepbit I/O contract docs to reflect the new machine-facing `run` surface.
- **Key Decisions**:
  - Plain `run` now publishes `contract_type = "quantlab.run.result"` inside the same canonical report artifact already used by `sweep`.
  - `sweep` keeps its richer `best_result` field, while plain `run` stays narrower and summary-focused.
  - Backward-compatible top-level KPI blocks remain in place so older consumers do not break.
- **Validation Notes**:
  - Verified focused behavior with `pytest` on `test_run_report.py`, `test_cli_run.py`, `test_sweep_contract.py`, and `test_machine_sweep_smoke.py`.

## 2026-03-24 — Canonical Run Outputs and Automatic Runs Index Refresh
- **Session Focus**: Align plain `run` with the canonical run artifact model and keep the shared runs index synchronized automatically.
- **Tasks Completed**:
  - Updated `src/quantlab/cli/run.py` so successful `run` executions create `outputs/runs/<run_id>/`.
  - Added canonical `run` artifact persistence for `metadata.json`, `config.json`, `metrics.json`, and `report.json`.
  - Ensured successful `run` executions always return a non-null `run_id` and canonical artifact paths.
  - Updated `main.py` to refresh `runs_index.csv/json/md` automatically after successful `run`, `sweep`, and `forward` commands.
  - Extended report generation so canonical `run` directories render a valid `report.json` without relying on legacy output conventions.
  - Added contract-oriented tests for canonical `run` outputs and main-level index refresh behavior.
  - Updated CLI, artifact-contract, and Stepbit I/O docs to reflect the new behavior.
- **Key Decisions**:
  - The primary storage contract for plain `run` is now the same canonical run directory model already used by the more mature flows.
  - Automatic runs-index refresh is centralized in `main.py` after successful run-producing commands instead of being duplicated across handlers.
  - The dedicated `machine_contract` block was deferred for plain `run` and handled in follow-up Issue #62 after the artifact layout stabilized.
- **Validation Notes**:
  - Verified focused behavior with `pytest` on `test_cli_run.py`, `test_runs_index_refresh.py`, `test_machine_sweep_smoke.py`, and `test_run_report.py`.
  - Verified broader artifact/index/CLI compatibility with `pytest` on `test_stage_g_artifacts.py`, `test_artifact_consistency.py`, `test_json_request.py`, `test_cli_health.py`, `test_run_index.py`, and `test_cli_runs.py`.

## 2026-03-23 — Preflight Checks and Sweep Smoke Validation (Issue #57)
- **Session Focus**: Add lightweight CLI preflight checks and a reproducible validation path for the machine-facing `sweep` contract.
- **Tasks Completed**:
  - Added `--version` to print the stable QuantLab version string.
  - Added `--check` to emit a deterministic JSON runtime health report.
  - Anchored `src/` into `sys.path` before CLI imports so preflight commands can run without depending on the caller's current working directory.
  - Deferred heavy runtime imports until after `--version` / `--check` so the health path can validate missing runtime dependencies instead of crashing before argument handling.
  - Added CLI regression tests for `--version` and `--check`.
  - Added a smoke test that drives `main.py --json-request` with `command: "sweep"` and validates the emitted session context against `report.json.machine_contract`.
- **Key Decisions**:
  - `--version` stays intentionally simple and prints the bare project version.
  - `--check` prints a JSON object to stdout and exits with code `0` on success or `2` on invalid runtime state.
  - The existing machine-facing `--json-request` route remains the single smoke-validation surface for `sweep`; no new execution interface was added.
- **Validation Notes**:
  - Full `pytest` execution still depends on installing the repo's `dev` extras in the local venv.
  - Focused validation now has dedicated tests for CLI health and machine-facing `sweep` smoke coverage.

## 2026-03-23 — Stable Sweep Contract and Canonical Run Artifacts (Issue #53)
- **Session Focus**: Define and implement a stable machine-facing `sweep` output contract for Stepbit while normalizing run artifacts.
- **Tasks Completed**:
  - Added canonical run artifact handling around `metadata.json`, `config.json`, `metrics.json`, and `report.json`.
  - Updated the sweep path to validate `params.config_path`, return stable context, and require canonical `report.json` after execution.
  - Extended `report.json` with a `machine_contract` block for `sweep` consumption.
  - Switched new sweep-generated runs away from writing `meta.json` and `run_report.json`; kept legacy read compatibility in reporting/index/forward-loading code.
  - Fixed the backtest initial-entry bug where the first bar could skip trade counting and costs when `positions[0] == 1`.
  - Fixed `--report` with `--trades_csv` so validation and report generation use the same path.
  - Added regression and contract-oriented tests for the new sweep/reporting behavior.
- **Key Decisions**:
  - `report.json` remains the canonical machine-readable artifact; the stable `sweep` contract lives inside `report.json.machine_contract`.
  - Legacy artifact names remain read-compatible only.
  - `run_report.md` remains the human-readable Markdown artifact name for run directories.
- **Validation Notes**:
  - `pytest` is not installed in the local venv, so full test execution could not be completed in-session.
  - Verified syntax with `python -m compileall src test main.py`.
  - Verified the new sweep contract path with a focused smoke test that generated and read a canonical `report.json`.

## 2026-03-23 — Research Dashboard UI Polish
- **Session Focus**: Upgrade the research dashboard from MVP registry table to a richer, read-only analysis surface.
- **Tasks Completed**:
  - Redesigned `research_ui/index.html` into a stronger research-terminal style layout.
  - Rebuilt `research_ui/app.js` to add richer registry summary state, mode pills, toasts, and run detail loading from canonical artifacts.
  - Reworked `research_ui/styles.css` for a more intentional visual system with improved responsive behavior.
- **Key Decisions**: Kept the UI strictly read-only and artifact-driven. Used `runs_index.json` for registry state and loaded per-run `run_report.json` / `report.json` only for detail inspection.
- **Next Steps**: Verify the dashboard in a local browser session and decide whether Comparison should remain disabled or become the next UI slice.

## 2026-03-22 — Research Dashboard MVP (Phase 1)
- **Session Focus**: Create a tangible, read-only UI layer for browsing research runs.
- **Tasks Completed**:
  - Scaffolded `research_ui/` with Vanilla JS/CSS (zero-dependency SPA).
  - Implemented `research_ui/server.py` for local dev-preview with 302 redirect for asset routing.
  - Built the Run Index table with real-time sorting and filtering.
  - Fixed unstyled UI issue caused by root-path asset resolution.
  - Handled port conflicts in the dev server.
- **Key Decisions**: Kept the UI strictly read-only and decouped from the core. Used a 302 redirect in the dev server to normalize browser context for relative asset paths.
- **Next Steps**: Phase 2 implementation for Run Detail and Comparison views.

## 2026-03-21 — Event Signalling & Session Hooks (Issue #25)
- **Session Focus**: Implement file-based session lifecycle notifications for Stepbit.
- **Tasks Completed**:
  - Implemented `SignalEmitter` in `main.py` with append-only JSON Lines support.
  - Added `--signal-file` CLI argument.
  - Updated CLI handlers (`run`, `sweep`, `forward`, `portfolio`, `report`, `runs`) to return execution context.
  - Implemented `SESSION_STARTED`, `SESSION_COMPLETED`, and `SESSION_FAILED` event emission in `main.py`.
  - Synchronized `.agents/stepbit-io-v1.md` and `docs/stepbit-io-v1.md`.
  - Fixed a literal `%` bug in `argparse` help strings causing `ValueError`.
- **Key Decisions**: Used append-only JSON Lines for best-effort signalling; deferred webhook delivery. Ensured handler changes were minimal for context propagation.
- **Next Steps**: Hand over for Stepbit integration testing.

## 2026-03-21 — QuantLab Runbook for Stepbit (Issue #26)
- **Session Focus**: Create operational documentation for Stepbit integration and sync I/O contract status.
- **Tasks Completed**:
  - Created `.agents/stepbit-runbook.md` organized by Prepare, Invoke, Interpret, and Recover.
  - Synchronized `.agents/stepbit-io-v1.md` and `docs/stepbit-io-v1.md`.
  - Updated I/O status labels for `schema_version` validation, `request_id` propagation, and exit codes 3/4 [done].
  - Documented missing Issue #24 features (`--check`, `--version`, path anchoring) as explicit operational gaps.
- **Key Decisions**: Documented current repository reality only, deferring restoration of missing runtime features to a dedicated slot.
- **Next Steps**: Hand over for review and eventual restoration of Issue #24 features if required.

## 2026-03-20 — Stepbit Error Policy (Issue #23)
- **Session Focus**: Harden the CLI for predictable headless Stepbit-driven execution.
- **Tasks Completed**:
  - Implemented strict `schema_version` and `command` validation in `main.py` (exit 2 for invalid input).
  - Propagated `request_id` to `args._request_id` for traceability.
  - Implemented explicit command dispatch for JSON requests, ensuring predictable routing regardless of flag fallthrough.
  - Added 8 unit tests in `test/test_json_request.py`.
- **Key Decisions**: Forced `command` field in JSON requests as hard required. Treated missing command as invalid input (exit 2).
- **Next Steps**: Proceed to Issue #22 for consistent `report.json` and artifact production.

## 2026-03-20 — Stepbit I/O Contract (Issue #20)
- **Session Focus**: Verify and publish the Stepbit I/O contract document.
- **Tasks Completed**:
  - Analyzed gap between `.agents/stepbit-io-v1.md` design and current CLI/artifact reality.
  - Created `docs/stepbit-io-v1.md` with accurate `[done]`/`[planned]` labels, corrected artifact path (`run_report.json`), and linked gaps to Issues #21–#23.
  - Synced `.agents/stepbit-io-v1.md` to match `docs/stepbit-io-v1.md` exactly — both files now share the same corrected contract.
- **Key Decisions**: No code changes. Response envelope, fingerprint, and schema validation deferred to #21–#23.
- **Next Steps**: Hand over to user for review and branch merge.

## 2026-03-20 — Runs CLI Interface (Issue #12)
- **Session Focus**: Implement the `runs.py` command surface for run navigation.
- **Tasks Completed**:
  - Implemented `--runs-list`, `--runs-show`, `--runs-best` in `src/quantlab/cli/runs.py`.
  - Wired `handle_runs_commands` into `main.py` before the report handler.
  - Migrated `--list-runs` and `--best-from` out of `report.py`; kept deprecated aliases for backward compat.
  - Added 13 tests in `test/test_cli_runs.py`; full test suite passes.
- **Key Decisions**: Kept `--compare` in `report.py` — it writes artifacts and is a reporting operation, not run navigation. Migrating it is deferred.
- **Next Steps**: Hand over to user for review and branch merge.

## 2026-03-20 — Post-CLI Roadmap Definition (Issue #14)
- **Session Focus**: Define the next development milestones for QuantLab after the CLI refactor.
- **Tasks Completed**:
  - Analyzed repository state and maturity.
  - Formalized Stage N (Run Lifecycle Management) and Stage O (Stepbit Automation Readiness) in `current-state.md`.
- **Key Decisions**: Prioritized internal run management (`quantlab runs`) over immediate Stepbit integration to ensure the research lab's utility.
- **Next Steps**: Begin Stage N implementation (Issue #12).

## 2026-03-20 — Stage M.4 Gap Closure
- **Session Focus**: Enrich portfolio mode comparison artifacts (JSON/Markdown) to meet specification.
- **Tasks Completed**:
  - Updated `portfolio_mode_compare.py` to store full mode blocks (candidates, allocation, summary) in the JSON payload.
  - Added "Weight Comparison" table to `portfolio_compare.md`.
  - Updated `test/test_portfolio_mode_compare.py` and verified all portfolio tests pass.
- **Key Decisions**: Decided to include full candidate metadata in the comparison JSON to ensure each mode's aggregation is fully traceable.
- **Next Steps**: Hand over to user for review and branch merge.

## 2026-03-10 — Run System Foundations
- **Session Focus**: Implement minimal infrastructure for structured, reproducible run storage.
- **Tasks Completed**:
  - Created `quantlab.runs` module.
  - Implemented `serializers.py`, `run_id.py`, `run_store.py`, and `registry.py`.
  - Added comprehensive unit tests in `test/test_runs_foundation.py`.
  - Verified all tests pass.
- **Key Decisions**: 
  - Centralized run identity and storage to ensure strict adherence to `artifact-contracts.md`.
  - Adopted deterministic JSON serialization and run IDs.
- **Next Steps**: Integrate the new Run Store into the experiment `runner.py` and migrate existing "legacy" outputs.

## 2026-03-07 — Stage M.3 Closed
- **Session Focus**: Final verification and closure of Stage M.3.
- **Tasks Completed**:
  - Verified that `test/test_portfolio_selection.py` passes.
  - Verified that `test/test_portfolio_report.py` passes.
  - Verified that `test/test_portfolio_allocation.py` passes.
  - Verified that `test/test_portfolio_hygiene.py` passes.
  - Verified that normal CLI portfolio reporting still works with `--portfolio-report .\outputs\forward_runs`.
  - Verified that empty-selection behavior now fails loudly with a clear `ValueError`.
- **Key Decisions**: Stage M.3 is considered closed, with explicit fail-loud behavior when no sessions remain after selection rules are applied.
- **Next Steps**: Begin Stage M.4 for portfolio mode comparison across `raw_capital`, `equal_weight`, and `custom_weight`.

## 2026-03-07 — Workflow Alignment
- **Session Focus**: Align `.agents` documentation with the actual project state.
- **Tasks Completed**:
  - Updated `current-state.md` with the completed stages currently tracked in the workflow system: I, J, K, L, L.1, L.2, L.2.a, L.2.b, M, M.1, and M.2.
  - Rewrote `stage-m3-selection-rules.md` to describe M.3 candidate selection and inclusion filters, instead of M.2 allocation controls.
  - Fixed `read-and-plan.md` by correcting `session_log.md` → `session-log.md`, adding the `implementation-rules.md` read step, and making the approval gate explicit.
  - Updated `project-brief.md` to include the `portfolio/` component, the full staged roadmap table, and the source-of-truth file list.
- **Key Decisions**: M.3 is defined as the stage for session selection and inclusion control, including top-N filtering, metric-based filters, ticker/strategy filters, and latest-per-source-run selection. These rules are applied **before** M.2 allocation weighting.
- **Next Steps**: Begin Stage M.3 using the `/read-and-plan` workflow.

## 2026-03-07 — Documentation Structure Initialization
- **Session Focus**: Documentation and workflow structure cleanup.
- **Tasks Completed**:
  - Initialized the `.agents` structure with starter templates.
  - Standardized file naming using lowercase-hyphen format.
  - Verified preservation of existing files.
- **Key Decisions**: `.agents` will serve as the lightweight project memory and workflow coordination layer for QuantLab.
- **Next Steps**: Continue aligning documentation and workflow files with the real project structure and stage progression.

- 2026-04-08: Started issue #215 renderer tab dispatch registry in a clean Desktop/UI worktree from `main`. Scope is limited to `desktop/renderer/app.js` plus `.agents` continuity, replacing the `renderTabs()` tab-kind conditional chain with a local render registry while preserving the existing fallback placeholder behavior.
- 2026-04-08: Completed issue #215 renderer tab dispatch registry. `renderTabs()` now dispatches through a local `TAB_RENDERERS` registry with the same fallback placeholder behavior, and validation passed against both desktop smoke and a live `research_ui` surface at `http://127.0.0.1:8000/research_ui/index.html`.
- 2026-04-09: Tightened both workflow documents so real diffs now default to the full closeout path: issue or task, branch, checks, coherent commit, PR, merge, issue closure, and local/remote cleanup unless the user explicitly pauses or repository state blocks the next step.
- 2026-04-09: Hardened issue #275 after the first CI run exposed an early-exit gap in desktop smoke. `desktop/main.js` now writes a smoke failure result for normal early shutdown paths, and `desktop/scripts/smoke.js` now reports a missing result artifact with child exit context instead of failing with a raw `ENOENT`.
- 2026-04-09: Kept issue #275 open after the next CI run exposed a Linux-only Electron sandbox abort on GitHub-hosted runners. `desktop/scripts/smoke.js` now adds the standard CI-only `--no-sandbox` flag for Linux smoke runs without changing local desktop behavior.
- 2026-04-09: Started and completed issue #286 workstation containment in a clean Desktop/UI worktree from `main`. The desktop shell now keeps one primary surface at a time, bounds context-tab accumulation, restores old workspace state into a single preserved primary surface, and tightens scroll containment across sidebar, workbench, workflow, and command palette. Validation passed with `npm run smoke:fallback` and `npm run smoke:real-path` from `desktop/`.
- 2026-04-09: Started and completed issue #287 right-rail support lane semantics in a clean Desktop/UI worktree from `main`. The upper support entry now behaves as `Quick commands` with deterministic feedback, the lower panel is the single assistant/history locus, Stepbit routing is explicit, and sidebar suggested actions no longer masquerade as a second assistant input. Validation passed with `npm run smoke:fallback` and `npm run smoke:real-path` from `desktop/`.
- 2026-04-09: Started and completed issue #288 decision clarity in a clean Desktop/UI worktree from `main`. `Runs`, `Run Detail`, `Artifacts`, `Compare`, and `Candidates` now expose evidence state, decision state, next-step guidance, compare readiness, and visible decision feedback after candidate/shortlist/baseline changes. Validation passed with `npm run smoke:fallback` and `npm run smoke:real-path` from `desktop/`.
- 2026-04-09: Started issue #313 after a clean `origin/main` review showed `real-path` still failing. Root cause was project-root precedence in worktrees: desktop bootstrap and smoke resolved the sibling `quant_lab` checkout before the actual current worktree. The fix now prefers the current checkout whenever it is a valid QuantLab project root.
- 2026-04-09: Completed issue #313 root-cause isolation and validation. `research_ui/server.py` can auto-increment from port `8000` to `8001+`, but `desktop/main.js` only probed `8000`. Desktop reachability probes now cover the retry range, and sequential validation passed with `npm run smoke:real-path` via `http://127.0.0.1:8001` and `npm run smoke:fallback` via the same live server. Parallel smoke runs were rejected as invalid because both modes contend for the same desktop and `research_ui` boot path.

---

## Template for New Sessions

```markdown
## YYYY-MM-DD — [Session Title]
- **Session Focus**: [Brief goal]
- **Tasks Completed**:
  - [Task 1]
  - [Task 2]
- **Key Decisions**: [Logic, scope, or architecture changes]
- **Next Steps**: [Planned work for the next session]


