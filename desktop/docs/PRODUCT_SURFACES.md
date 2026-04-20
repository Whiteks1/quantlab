# QuantLab Desktop — Product Surfaces Inventory

> Last updated: 2026-04-20  
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
| **Job** | `job` | `keep` | `research_ui` iframe | Active job view. Delegates to `research_ui` `/launch`. Real-time feedback. |
| **Sweep Decision** | `sweep-decision` | `freeze` | `research_ui` iframe | Delegates to `research_ui` `/launch`. Rarely used. Freeze until sweep workflow matures. |

---

## Legacy / transitional surfaces

These surfaces exist but should be migrated, replaced, or eliminated in the current desktop maturity block.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **iFrame** | `iframe` | `freeze` | external URL | Generic iframe for arbitrary URLs. Keep as utility, do not promote. |

---

## research_ui dependency map

| Surface | Depends on research_ui? | Mode |
|---------|------------------------|------|
| Runs | ❌ No | Fully native |
| Run detail | ❌ No | Fully native (reads from `outputs/runs/`) |
| Artifacts | ❌ No | Integrated into Run Detail; reads from `outputs/` |
| Compare | ❌ No | Fully native |
| Candidates | ❌ No | Fully native |
| Paper Ops | ❌ No | Native-hosted wrapper (existing `renderPaperOpsTab()` logic) |
| System | ❌ No | Native-hosted wrapper (existing `renderSystemTab()` logic) |
| Experiments | ❌ No | Native-hosted wrapper (existing `renderExperimentsTab()` logic) |
| Launch | partial | Native workstation capability with `research_ui` continuity for browser-backed job/launch flows not yet replaced |
| Job | ✅ Yes | Iframe → `/launch` |
| Sweep Decision | ✅ Yes | Iframe → `/launch` |
| iFrame | varies | Arbitrary URL |

---

## Guiding principle

> **Native = keep and deepen. Iframe = freeze or migrate-piece.**

The desktop's competitive advantage is the native evidence rail over canonical artifacts. Every sprint should expand the native surface and reduce iframe dependency.

Launch should remain visible and operationally important, but it must be framed as supervised QuantLab execution flow, not as a trading console, fintech dashboard, or standalone product identity.

---

## Next implementation slices (ordered by dependency)

These are the viable issues from the current backlog, in execution order:

1. **#262** — design tokens and base panels (foundation for all native surfaces)
2. **#263** — harden runs table (primary workspace surface)
3. **#264** — native run detail workspace (evidence rail depth)
4. **#265** — artifact explorer around canonical outputs
5. **#266** — minimal hypothesis builder

---

## Out of scope for this document

- No UI code is changed here.
- No renderer architecture is changed.
- No Stepbit contract work.
- No shell architecture changes.
