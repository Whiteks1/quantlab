# QuantLab Desktop — Product Surfaces Inventory

> Last updated: 2026-04-21
> Status: authoritative. Update this file when surfaces change ownership or status.

---

## Primary product surfaces

These are the core workflow surfaces. They should be actively maintained, deepened, and shaped for research + execution discipline.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **Runs** | `runs` | `keep` | desktop-native | Primary workspace. Run table, spotlight card, decision queue, operational card. All native. |
| **Run detail** | `run` | `keep` | desktop-native | Evidence rail: identity header, metrics summary, config provenance, artifacts continuity, decision block. All native. |
| **Artifacts** | `run` subview | `keep` | desktop-native | Integrated into Run Detail as artifact continuity over canonical `outputs/runs/<run_id>/`. Do not restore a separate protagonist tab unless a future ADR changes this. |
| **Compare** | `compare` | `keep` | desktop-native | Ranking table across selected runs. Native renderer. Depends on candidates shortlist. |
| **Candidates** | `candidates` | `keep` | desktop-native | Shortlist management. Promote/demote from run detail. Native. |

---

## Secondary / support surfaces

These surfaces exist and function but are not the primary focus of the current product sprint.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **Paper Ops** | `paper` | `keep` | desktop-native | Native-hosted (via #410). Uses existing render logic from `renderPaperOpsTab()`. Broker boundary, decision queue, operational continuity. No iframe. |
| **System** | `system` | `keep` | desktop-native | Native-hosted (via #410). Uses existing render logic from `renderSystemTab()`. Runtime diagnostics, workspace status, API refresh, logs. No iframe. |
| **Experiments** | `experiments` | `keep` | desktop-native | Native-hosted (via #410). Uses existing render logic from `renderExperimentsTab()`. Config catalog, sweep leaderboards, decision tracking. No iframe. |
| **Launch** | none / future `launch` | `target-state` | desktop-native capability | First-class workstation capability, not a separate product identity. Current release surface keeps the shell workflow panel and assistant commands. Future native React work may promote it to a dedicated surface only if it preserves supervised execution and evidence continuity. |
| **Job / Launch Review** | `job` | `keep` | React-owned with transitional Launch API | Active job review. Reads launch job state and stdout/stderr from the `research_ui` API boundary while React owns the review surface. |
| **Sweep Decision** | `sweep-decision` | `freeze` | transitional continuity | Rarely used sweep handoff. Keep frozen until sweep workflow matures; do not promote through `research_ui`. |

---

## Legacy / transitional surfaces

These surfaces exist but should be migrated, replaced, or eliminated in the current desktop maturity block.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **iFrame** | `iframe` | `freeze` | external URL | Generic iframe for arbitrary URLs. Keep as utility, do not promote. |

---

## research_ui dependency map

| Area | Current dependency | Classification | Cutoff decision |
|------|--------------------|----------------|-----------------|
| Runs | None; reads run index and local artifacts | Canonical native | Keep native. Do not reintroduce browser ownership. |
| Run detail / Artifacts | None for core path; reads `outputs/runs/` | Canonical native | Keep integrated in Run Detail. |
| Compare | None | Canonical native | Keep native. |
| Candidates | None | Canonical native | Keep native. |
| Paper Ops | Uses API payloads when a server is reachable, otherwise native/local state | Transitional API input | Keep native surface. Browser ops links are continuity-only and removable once native job/paper continuity is sufficient. |
| System | Shows `research_ui` reachability and links | Transitional diagnostics | Keep diagnostics, but do not treat `research_ui` as shell owner. |
| Experiments | Local configs/sweeps; launch actions still submit through API | Transitional launch API | Keep native inspection. Launch submission needs a native/contracted path before #412. |
| Launch | Form/assistant commands submit to `/api/launch-control` | Transitional execution API | Allowed only as supervised execution continuity until a native Launch contract exists. |
| Job / Launch Review | Job state and logs come from `research_ui` launch records | React-owned review surface / transitional API input | React owns the review UX; the launch/job data source remains an explicit API boundary before #412. |
| Sweep Decision | Frozen handoff surface | Deprecated / continuity-only | Do not expand. Remove or re-scope during legacy retirement. |
| Generic iframe | Arbitrary browser surface | Deprecated / continuity-only | Do not promote. Candidate for #412 deletion unless kept as explicit external utility. |
| `smoke:real-path` | Requires reachable `research_ui` server | CI/runtime continuity | Keep as API/reachability validation, not product ownership validation. |

## research_ui cutoff decision

`research_ui` remains allowed only as an external continuity and API boundary for:

- real-path smoke and runtime reachability checks
- launch/job execution APIs that do not yet have a native replacement
- paper, broker, Stepbit, and launch-control payloads while the desktop still reads them through server endpoints
- browser-backed fallback links during the transition

`research_ui` must not be treated as:

- the target shell architecture
- the Launch product owner
- the canonical workstation UI
- the owner of Job review UX
- the place for new desktop product behavior

Before #412 can retire the legacy shell renderer, every remaining `research_ui` dependency must be either:

- preserved explicitly as an external API dependency, or
- replaced by a native/React-owned surface, or
- marked as safe to delete with the legacy renderer.

Issue #436 moves Job / Launch Review into the second category: React owns the review surface, while launch/job data remains preserved as an explicit transitional API dependency.

## Desktop v1 release boundary

Desktop v1 is a functional operator workstation with explicit transitional boundaries. Legacy remains the default release runtime where still required for complete operator flow. React is a validated selectable runtime and the canonical future direction, but not yet the default release path.

For this inventory, that means:

- release-critical operator flow may still rely on legacy-backed paths
- React-owned surfaces remain canonical future direction and validated selectable runtime coverage
- `research_ui` remains a transitional API and reachability boundary, not product ownership
- making React the default runtime is not required to declare Desktop v1
- removing the legacy shell renderer is not required to declare Desktop v1

## #412 deletion boundaries

#412 may delete or remove from the primary runtime only after these conditions are true:

- React has native or React-owned handling for Job / Launch Review tabs, including stdout, stderr, status, linked run, and artifacts.
- Launch submission has an explicit native contract or an intentionally documented transitional API boundary.
- Browser links such as `Open research_ui`, `Browser ops`, and `Browser view` are no longer primary actions.
- `smoke:real-path` is documented as API/reachability validation, not evidence that browser UI owns the product.
- `legacy.html` and `app-legacy.js` no longer own any required release path that React cannot reproduce or intentionally delegate.

#412 must not remove:

- `research_ui/server.py` if desktop still relies on its API endpoints
- real-path smoke reachability while it remains the only end-to-end server validation
- launch/job API support unless a native replacement exists

---

## Guiding principle

> **Native = keep and deepen. Iframe = freeze or migrate-piece.**

The desktop's competitive advantage is the native evidence rail over canonical artifacts. Every sprint should expand the native surface and reduce iframe dependency.

Launch should remain visible and operationally important, but it must be framed as supervised QuantLab execution flow, not as a trading console, fintech dashboard, or standalone product identity.

---

## Desktop v1 classification

Current backlog classification for Desktop v1 closure:

- **#442** — v1 release-state definition. This document records the release boundary; no code or runtime switch is implied.
- **#412** — needs re-scope or split. It must not be executed as broad deletion while legacy still owns required release flow.
- **#266** — post-v1 unless recut into a much smaller release-alignment slice. It must not expand Desktop v1 closure into new hypothesis-builder product work.

---

## Out of scope for this document

- No UI code is changed here.
- No renderer architecture is changed.
- No Stepbit contract work.
- No shell architecture changes.
