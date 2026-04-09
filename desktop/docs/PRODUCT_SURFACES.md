# QuantLab Desktop — Product Surfaces Inventory

> Last updated: 2026-04-09  
> Status: authoritative. Update this file when surfaces change ownership or status.

---

## Primary product surfaces

These are the core workflow surfaces. They should be actively maintained, deepened, and shaped for research + execution discipline.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **Runs** | `runs` | `keep` | desktop-native | Primary workspace. Run table, spotlight card, decision queue, operational card. All native. |
| **Run detail** | `run` | `keep` | desktop-native | Evidence rail: identity header, metrics summary, config provenance, artifacts continuity, decision block. All native. |
| **Artifacts** | `artifacts` | `keep` | desktop-native | File explorer over canonical `outputs/runs/<run_id>/`. Native renderer. |
| **Compare** | `compare` | `keep` | desktop-native | Ranking table across selected runs. Native renderer. Depends on candidates shortlist. |
| **Candidates** | `candidates` | `keep` | desktop-native | Shortlist management. Promote/demote from run detail. Native. |

---

## Secondary / support surfaces

These surfaces exist and function but are not the primary focus of the current product sprint.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **Paper Ops** | `paper` | `keep` | `research_ui` iframe | Delegates to `research_ui` `/ops` route. Not native. Ownership: research_ui side. |
| **Job** | `job` | `keep` | `research_ui` iframe | Active job view. Delegates to `research_ui` `/launch`. Real-time feedback. |
| **Sweep Decision** | `sweep-decision` | `freeze` | `research_ui` iframe | Delegates to `research_ui` `/launch`. Rarely used. Freeze until sweep workflow matures. |

---

## Legacy / transitional surfaces

These surfaces exist but should be migrated, replaced, or eliminated in the current desktop maturity block.

| Surface | Tab kind | Status | Owner | Notes |
|---------|----------|--------|-------|-------|
| **Experiments** | `experiments` | `migrate-piece` | `research_ui` iframe | Delegates to `research_ui` `/research_ui/index.html#/launch`. The experiment config/sweep picker should eventually be native. Not a current priority. |
| **System** | `system` | `freeze` | `research_ui` iframe | Root research_ui iframe fallback. Exists as escape hatch. Keep but do not develop. |
| **iFrame** | `iframe` | `freeze` | external URL | Generic iframe for arbitrary URLs. Keep as utility, do not promote. |

---

## research_ui dependency map

| Surface | Depends on research_ui? | Mode |
|---------|------------------------|------|
| Runs | ❌ No | Fully native |
| Run detail | ❌ No | Fully native (reads from `outputs/runs/`) |
| Artifacts | ❌ No | Fully native (reads from `outputs/`) |
| Compare | ❌ No | Fully native |
| Candidates | ❌ No | Fully native |
| Paper Ops | ✅ Yes | Iframe → `/ops` |
| Job | ✅ Yes | Iframe → `/launch` |
| Sweep Decision | ✅ Yes | Iframe → `/launch` |
| Experiments | ✅ Yes | Iframe → `/research_ui/index.html#/launch` |
| System | ✅ Yes | Iframe → root |
| iFrame | varies | Arbitrary URL |

---

## Guiding principle

> **Native = keep and deepen. Iframe = freeze or migrate-piece.**

The desktop's competitive advantage is the native evidence rail over canonical artifacts. Every sprint should expand the native surface and reduce iframe dependency.

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
