# Session Log - QuantLab

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
```

## 2026-04-07 — Desktop Workstation UI Direction
- **Session Focus**: Define a workstation-oriented desktop UI issue block and implement the first high-impact slice in QuantLab Desktop.
- **Tasks Completed**:
  - Added a proposed desktop UI workstation issue block under `.agents/tasks/`.
  - Created issue packets #201 to #205 covering shell hierarchy, runs home, run detail evidence rail, compare/candidates density, and assistant demotion.
  - Implemented default desktop startup behavior so the shell now prefers `Runs` when indexed run data is available and falls back to `System` otherwise.
  - Redesigned the native `Runs` tab into a denser workbench with summary cards, central table, and an evidence/context rail.
  - Verified the desktop with `npm run smoke` in `desktop/`.
- **Key Decisions**:
  - The UI reference should guide layout maturity and hierarchy, not trading semantics or portfolio-monitoring language.
  - `Runs` is the correct primary desktop surface because it best expresses QuantLab's research, artifact, and decision identity.
  - The remaining workstation redesign should proceed as incremental slices instead of a full renderer rewrite.
- **Next Steps**:
  - Implement Issue #203 to harden `Run Detail` into a stronger evidence rail.
  - Implement Issue #204 to align `Compare` and `Candidates` with the new workstation density.

## 2026-04-07 — Run Detail Evidence Rail
- **Session Focus**: Implement Issue #203 so `Run Detail` matches the workstation direction established in `Runs`.
- **Tasks Completed**:
  - Reworked `Run Detail` into a two-column workstation layout with a primary evidence stack and a persistent right-side rail.
  - Moved result evidence, config provenance, launch review linkage, and sweep linkage into the primary evidence column.
  - Hardened the right-side rail around run decision context, artifact continuity, and workspace linkage.
- **Key Decisions**:
  - `Run Detail` should prioritize evidence review and operational continuity over a flat sequence of panels.
  - The right rail should remain stable and summary-oriented while the main column carries the denser inspection blocks.
- **Next Steps**:
  - Implement Issue #204 to bring `Compare` and `Candidates` up to the same workstation density and hierarchy.

## 2026-04-07 — Compare and Candidates Workbench Density
- **Session Focus**: Implement Issue #204 so comparison and decision-queue surfaces match the workstation grammar already established in `Runs` and `Run Detail`.
- **Tasks Completed**:
  - Rebuilt `Compare` around a dense ranking matrix with a stable right-side decision rail.
  - Reworked `Candidates` into a queue-oriented workstation with persistent filters, baseline visibility, shortlist readiness, and recency-aware ordering.
  - Hardened candidate cards to expose decision-relevant metrics, continuity metadata, and actions directly in the queue.
- **Key Decisions**:
  - `Compare` should optimize for operator ranking speed, so the center of gravity moved from loose cards to a sortable matrix.
  - `Candidates` should behave like explicit local decision memory, so baseline and shortlist state must remain visible even while filtering.
- **Next Steps**:
  - Implement Issue #205 to demote the assistant and command surface behind the workstation-first shell hierarchy.

## 2026-04-07 — Assistant and Command Surface Demotion
- **Session Focus**: Implement Issue #205 so the desktop reads workstation-first while retaining the assistant as support tooling.
- **Tasks Completed**:
  - Reordered the main shell layout so focused work surfaces and workflow blocks lead the page, with assistant support moved into a dedicated lateral column.
  - Moved the quick command entry into the support lane and reduced the visual weight of browser/assistant controls.
  - Changed assistant focus behavior so opening the assistant no longer clears the active work surface.
  - Trimmed sidebar suggested actions to a smaller workstation-oriented set.
- **Key Decisions**:
  - The assistant remains always available, but it should not reset or replace the active investigation surface.
  - The command palette stays global, while the inline support command becomes secondary to tabs, runs, compare, and workflow.
- **Next Steps**:
  - Use the next slice to polish visual density and product-brand alignment now that the shell hierarchy is workstation-first.

## 2026-04-07 — Desktop Visual Polish and Renderer Cleanup
- **Session Focus**: Complete the next ordered tranche after the workstation issue block: visual polish first, then renderer cleanup.
- **Tasks Completed**:
  - Polished the desktop workstation palette, surface treatments, and brand mark in `desktop/renderer/index.html` and `desktop/renderer/styles.css` so the shell reads closer to a QuantLab research instrument than a generic dashboard.
  - Standardized dense workstation surfaces across run detail, runs, compare, candidates, system, workflow, and assistant support panels by removing leftover older panel treatments and fixing a stray CSS brace.
  - Extracted shell chrome copy, nav mapping, and command palette metadata into `desktop/renderer/modules/shell-chrome.js` so `desktop/renderer/app.js` is more focused on state, events, and rendering.
  - Validated `research_ui` reachability and reran desktop smoke until it passed cleanly.
- **Key Decisions**:
  - Desktop branding stays local to the renderer for now; the immediate goal is workstation coherence, not a cross-repo asset package.
  - Static shell chrome and action definitions are now treated as renderer configuration, not inline app-state logic.
- **Next Steps**:
  - If the desktop continues to evolve, the next cleanup slice should target renderer module boundaries and shared surface primitives rather than more copy accretion in `app.js`.

## 2026-04-07 — Renderer Surface Primitives
- **Session Focus**: Execute the next renderer cleanup slice by extracting repeated HTML primitives used across dense workstation tabs.
- **Tasks Completed**:
  - Added `desktop/renderer/modules/view-primitives.js` for reusable action buttons, action rows, empty states, and metric-list rendering.
  - Repointed key workstation surfaces in `desktop/renderer/modules/tab-renderers.js` to the shared primitives, especially runs, run detail, artifacts, candidates, sweep handoff, and system.
  - Removed dead `renderSummaryCard` / `compareMetric` pass-through wrappers from `desktop/renderer/app.js`.
  - Revalidated the desktop with `npm run smoke`.
- **Key Decisions**:
  - Shared surface helpers belong beside the renderer modules, not back in `app.js`.
  - The immediate goal is reducing markup duplication while preserving the existing `data-*` event contract used by the shell bindings.
- **Next Steps**:
  - The next renderer slice should target event-binding consolidation for repeated `data-*` actions so `app.js` keeps shrinking without changing shell behavior.

## 2026-04-07 — Renderer Data-Action Binding Consolidation
- **Session Focus**: Execute the next hardening slice by consolidating repeated `data-*` event bindings in the desktop renderer.
- **Tasks Completed**:
  - Added generic binding helpers in `desktop/renderer/app.js` for `data-*` click/change handlers plus shared external-URL and local-path actions.
  - Replaced repeated manual selector loops in workflow lists, tab content binding, and run context actions with the new helpers.
  - Preserved the existing `data-*` contract so `tab-renderers.js` and `view-primitives.js` continue to interoperate without markup changes.
  - Revalidated the desktop with `npm run smoke`.
- **Key Decisions**:
  - This slice stays inside `app.js`; no event contract or tab payload shape was changed.
  - The correct cleanup axis is to centralize binding mechanics first, then consider reducing the number of action variants later.
- **Next Steps**:
  - The next renderer slice should target common tab-action maps so each `tab.kind` block carries less inline binding code.

## 2026-04-07 — Tab Action Map Cleanup
- **Session Focus**: Continue renderer hardening by making `bindTabContentEvents` more declarative while preserving the existing desktop behavior.
- **Tasks Completed**:
  - Added batched action helpers in `desktop/renderer/app.js` for grouped `data-*`, external-link, and path bindings.
  - Rewrote the `tab.kind` branches in `bindTabContentEvents` to use grouped action specs instead of long runs of individual binding calls.
  - Kept the same `data-*` event contract used by `tab-renderers.js` and the workstation surfaces.
  - Revalidated the desktop with `npm run smoke`.
- **Key Decisions**:
  - The hardening path remains incremental: reduce binding boilerplate before attempting broader tab-dispatch abstraction.
  - No action names, tab ids, or renderer payload shapes were changed in this slice.
- **Next Steps**:
  - The next cleanup slice should extract per-tab binding maps or registries so `bindTabContentEvents` becomes a dispatcher rather than a large conditional block.

## 2026-04-07 — Issue #206 Topbar and Global Chrome Maturity
- **Session Focus**: Start the visual-maturity block by improving desktop topbar hierarchy and shell-level context without changing tab behavior.
- **Tasks Completed**:
  - Strengthened the shell topbar in `desktop/renderer/index.html` with clearer workstation framing, global-action copy, and visible runtime/server/surface chips.
  - Added topbar chrome styling in `desktop/renderer/styles.css` so the header reads as a deliberate workstation control band rather than a minimal shell row.
  - Extended `desktop/renderer/modules/shell-chrome.js` with topbar defaults and updated `desktop/renderer/app.js` to keep topbar runtime, server, and surface context synchronized with live state.
  - Revalidated the desktop with `npm run smoke`.
- **Key Decisions**:
  - This issue stays strictly shell-level: no tab payloads, no backend contracts, and no changes to workstation content surfaces.
  - Topbar maturity is handled through visible context chips rather than adding decorative controls or generic dashboard chrome.
- **Next Steps**:
  - Move to Issue #207 and focus specifically on `Runs` table semantics, row scanning speed, and visual state clarity.

## 2026-04-07 — Issue #207 Runs Table Visual Semantics and Density Polish
- **Session Focus**: Improve the primary `Runs` surface so row scanning is faster and operational state is more legible without changing data contracts.
- **Tasks Completed**:
  - Reworked the `Runs` table in `desktop/renderer/modules/tab-renderers.js` so run identity, metadata, window, metrics, and state are grouped more clearly by row.
  - Added per-row state summaries for decision memory, launch continuity, and artifact readiness using lightweight dot signaling rather than extra prose.
  - Polished table density and scanability in `desktop/renderer/styles.css`, including primary-cell hierarchy, inline mode chips, compact actions, and clearer state rows.
  - Revalidated the desktop with `npm run smoke`.
- **Key Decisions**:
  - The slice stays inside existing run data and local continuity context; no new backend metrics or contracts were introduced.
  - State signaling is kept sober and workstation-oriented rather than chart-heavy or trading-dashboard styled.
- **Next Steps**:
  - Move to Issue #208 and strengthen the right rail so the selected-context panels reach the same maturity level as the `Runs` table.

## 2026-04-07 — Current-State Debt Cleanup
- **Session Focus**: Remove stale technical debt from `.agents/current-state.md` so the repo state remains trustworthy.
- **Tasks Completed**:
  - Verified that the previously referenced duplicate workflow file `strategy_research.md` no longer exists under `.agents/workflows/`.
  - Removed the stale known-issue entry from `.agents/current-state.md`.
- **Key Decisions**:
  - `current-state.md` should only track active debt that still exists in the tree.
- **Next Steps**:
  - Keep future `.agents` debt items tied to verifiable repository state before carrying them forward.

## 2026-04-07 — Desktop Smoke CI and Positioning Alignment
- **Session Focus**: Close the next two follow-up blocks after the runtime hotfix: desktop smoke coverage in CI and minimal public positioning cleanup for the desktop shell.
- **Tasks Completed**:
  - Added a dedicated `desktop-smoke` GitHub Actions job that sets up Python and Node, installs desktop dependencies, and runs `npm run smoke` under `xvfb`.
  - Updated public desktop descriptions in `README.md` and `desktop/README.md` so the shell is described as workstation-first with assistant support, not chat-centered.
  - Updated `docs/quantlab-desktop-v1.md` so its top-level framing now reflects workstation-first hierarchy with a specialized assistant support lane.
- **Key Decisions**:
  - Desktop validation is now treated as a first-class CI concern rather than a local-only manual check.
  - The positioning cleanup stays narrow: align the shell hierarchy language without reopening broader product-brand or desktop roadmap debates.
- **Next Steps**:
  - Verify the new GitHub Actions desktop-smoke job on the next remote run and adjust only if the hosted runner needs extra Electron runtime packages.

## 2026-04-08 — Restore Desktop Boot Decoupling
- **Session Focus**: Resolve the semantic regression around `fix(desktop): decouple shell from research_ui boot` without overwriting the newer workstation renderer work.
- **Tasks Completed**:
  - Restored IPC response envelopes in `desktop/main.js` and matching unwrap logic in `desktop/preload.js` for `request-json`, `request-text`, and `post-json`.
  - Reinstated smoke semantics in `desktop/scripts/smoke.js` and `desktop/main.js` so the desktop passes when the shell boots from a local runs index even if `research_ui` does not become reachable.
  - Added a smoke-only environment flag so desktop smoke now exercises the local-fallback boot path deterministically instead of silently passing through a live `research_ui` server.
  - Ported local fallback loading back into `desktop/renderer/app.js` for runs registry refresh, run detail artifact reads, and optional text/log reads while keeping the current workstation layout intact.
  - Updated runtime messaging so the desktop explicitly reports when it is running from local artifacts rather than a live `research_ui` server.
- **Key Decisions**:
  - The port is surgical: preserve the current renderer chrome, tabs, and hardening work, and only reintroduce the pieces required for true boot decoupling.
  - Local fallback remains shell-first: native surfaces stay usable without `research_ui`, while browser-backed surfaces still wait for a live server.
- **Next Steps**:
  - Revalidate `npm run smoke` and then continue the visual maturity block starting with Issue #208.
- 2026-04-08: Completed issue #208 right-rail evidence panel maturity. Runs now prioritizes selected/baseline/latest context in a sticky evidence rail, and Run Detail exposes stronger artifact posture, continuity, and local file context without adding new runtime endpoints.
- 2026-04-08: Completed issue #209 status language and state signaling refinement. Desktop surfaces now reuse the same tone vocabulary for ready, pending or review, and degraded states across runs, run detail, system, paper ops, launch review, and topbar chrome.
- 2026-04-08: Completed issue #210 typography, spacing, and panel polish pass. The desktop chrome now uses a tighter mono label system, more consistent panel padding and hierarchy, and updated topbar defaults so the workstation reads as one cohesive product surface without changing runtime behavior.
- 2026-04-08: Updated `.agents/workflow.md` so chat ownership is now a constant repo rule. The workflow file now defines stable Engine versus Desktop/UI ownership, cross-boundary stop rules, branch and dirty-tree preflight checks, and a requirement to record the validation actually run.
- 2026-04-08: Started issue #214 renderer tab binding registry hardening. This slice is limited to `desktop/renderer/app.js` plus `.agents` continuity, and replaces the long `bindTabContentEvents` conditional chain with a local handler registry without changing renderer behavior.
- 2026-04-08: Completed issue #214 renderer tab binding registry hardening. `bindTabContentEvents` now dispatches through a local `TAB_CONTENT_EVENT_BINDERS` registry in `desktop/renderer/app.js`, and `npm run smoke` still passes via local runs fallback.
- 2026-04-10: Started issue #342 to restore primary workbench ownership after the desktop kept reserving too much width for empty or low-value side panes. This slice introduces a workbench-priority layout mode in the renderer so support and internal rails collapse earlier on common laptop widths instead of compressing the active surface.
- 2026-04-10: Completed issue #342 primary workbench ownership. The renderer now marks workbench-heavy surfaces explicitly and collapses the outer support lane plus internal two-column workbench grids earlier, so `Runs`, `Compare`, `Candidates`, `Run Detail`, and `Paper Ops` stop holding two side rails at the same laptop-width breakpoint. Validation passed with `node --check desktop/renderer/app.js`, `npm run smoke:fallback`, and `npm run smoke:real-path`.
- 2026-04-10: Started issue #346 to harden `desktop-smoke` result persistence after CI repeatedly failed with raw `ENOENT` on missing `result.json` in a planning-only PR. The slice is limited to `desktop/main.js`, `desktop/scripts/smoke.js`, and `.agents` continuity so smoke emits structured failures instead of crashing when Electron exits too early.
- 2026-04-10: Added the desktop layout regression remediation block after reviewing the post-merge desktop state in real screenshots. Opened issues #342, #343, and #344 to target empty-pane collapse, stronger active-surface focus and context containment, and better runs-family density plus right-rail space budgeting without reopening core or `research_ui` scope.
