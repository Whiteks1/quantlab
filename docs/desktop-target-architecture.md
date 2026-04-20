# QuantLab Desktop Target Architecture and Shared Contract Guardrails

Status: accepted
Date: 2026-04-14
Issue: #350

## Decision

QuantLab Desktop will evolve toward a native operator workspace with this target shape:

- Electron shell as the host runtime
- typed preload plus stable IPC surface as the process boundary
- shared contract models under `desktop/shared/` as the only cross-process contract source
- native renderer-owned workstation surfaces as the long-term UI target

`research_ui` remains a transitional continuity layer. It may continue to provide browser-backed reachability where the desktop still depends on it, but it is not the target shell architecture and it must not reclaim product authority from the native workspace.

## 2026-04-20 Update: Launch Target State

Issue #411 formalizes desktop product intent and continuity boundaries; it does not implement Launch expansion or legacy retirement.

After #409, #410, and #427, the desktop owns the primary inspection and operation surfaces:

- Runs
- Run Detail with integrated artifact continuity
- Compare
- Candidates
- Paper Ops
- System
- Experiments

Launch is not a separate product identity and should not become a trading-console protagonist. Its target state is a first-class desktop capability inside the QuantLab Research workstation:

- visible in the shell workflow and navigation model
- bounded by deterministic inputs, explicit requests, and supervised operation
- connected to engine-owned launch contracts and canonical artifacts
- reviewable through jobs, run detail, paper/system state, and evidence surfaces

Launch may become a dedicated native surface in a later React migration slice if that is the smallest coherent implementation step, but #411 only fixes the product decision. It does not add a new Launch UI, expand the legacy shell, or retire `research_ui`.

`research_ui` now remains only as a continuity boundary for:

- real-path smoke and runtime reachability checks
- browser-backed job or launch continuity still not replaced by native surfaces
- temporary fallback while the release surface remains the transitional workstation

It must not be treated as the target Launch experience.

## 2026-04-20 Update: research_ui Cutoff Before Legacy Retirement

Issue #432 fixes the cutoff for `research_ui` before #412 can remove the legacy shell renderer.

`research_ui` remains allowed as a transitional external boundary for:

- real-path smoke and runtime reachability checks
- launch/job execution endpoints that do not yet have a native replacement
- paper, broker, Stepbit, and launch-control payloads while desktop still reads them through server APIs
- browser-backed fallback links during the transition

`research_ui` is no longer allowed to be treated as:

- the target shell runtime
- the canonical workstation UI
- the Launch product owner
- the Job / Launch Review UX owner
- the place for new desktop product behavior

This means #412 is not a blind deletion task. It can only remove legacy renderer ownership after every remaining `research_ui` dependency is either preserved as an explicit external API, replaced by a native/React-owned surface, or marked safe to delete.

#412 must not remove `research_ui/server.py`, real-path smoke reachability, or launch/job API support while desktop still depends on those endpoints.

Issue #436 narrows the remaining Launch blocker by moving Job / Launch Review ownership into React while keeping `/api/launch-control` as the explicit transitional data boundary. This does not make React the default runtime and does not authorize legacy renderer deletion.

## Why

The desktop now spans shell bootstrap, preload, shared contracts, browser continuity, and future native workstation surfaces. Without an explicit target architecture, each migration slice would risk reopening the same debates:

- whether the desktop should stay browser-first
- whether `research_ui` remains a permanent dependency
- whether renderer state can invent ad hoc payloads
- whether Stepbit or other external surfaces can become the de facto workspace authority

This ADR fixes those decisions now so later slices stay small.

## Architecture Direction

### 1. Authority stays in QuantLab engine and artifacts

Desktop is a workstation layer, not a second product authority.

The engine and canonical artifacts remain authoritative for:

- run and sweep truth
- paper and broker evidence
- machine-facing contracts
- execution and promotion semantics

Desktop may visualize, filter, compare, and launch bounded actions, but it does not redefine engine authority.

### 2. Shared-contract-first boundary

Anything that crosses:

- main process to preload
- preload to renderer
- smoke/runtime boundary to tests

must use the shared contract layer in `desktop/shared/`.

Guardrail:

- do not add ad hoc channel names or payload shapes directly in `main.js`, `preload.js`, or renderer modules when the payload belongs to an owned desktop contract

### 3. Native desktop is the target state

The target workspace is native desktop-owned, not a long-lived embedded browser shell.

Target native surfaces include:

- Runs
- Compare
- Candidates
- Run Detail
- Artifact Explorer
- Paper Ops
- System and experiments visibility
- Launch as a bounded workstation capability

`research_ui` may continue to exist during migration, but only as bounded continuity for capabilities that have not yet moved into native surfaces.

### 4. `research_ui` is transitional, not sovereign

`research_ui` is allowed to provide:

- real-path continuity checks
- browser-backed fallback behavior where still required
- temporary access to views not yet migrated

`research_ui` is not allowed to become:

- the main workspace owner
- the permanent shell target
- the place where desktop contracts are defined

### 5. Stepbit remains external and optional

Stepbit may assist through automation, reasoning, or external UI integration, but it does not own QuantLab Desktop architecture.

Desktop should remain coherent and useful without Stepbit being present.

## Required Guardrails

- one shared contract source for desktop-owned payloads
- one shell authority: Electron desktop, not browser continuity
- one migration direction: native surfaces replace transitional browser-backed ones
- one ownership model: engine owns truth, desktop owns workstation presentation
- no runtime slice should reopen stack choice, workspace authority, or `research_ui` permanence unless a new ADR explicitly replaces this one

## Migration Order

The intended migration order is:

1. shared contract foundation
2. typed desktop base across main, preload, shared models, and renderer
3. main-process modularization and stable IPC ownership
4. minimal React shell frame
5. migration of core workstation surfaces
6. migration of run detail and artifacts
7. migration of paper, system, and experiment surfaces
8. explicit Launch target-state decision (#411)
9. `research_ui` cutoff and legacy-retirement preconditions (#432)
10. retirement of the legacy shell renderer after the cutoff conditions are satisfied (#412)

Micro-cuts may happen inside a slice, but this order should not be reopened casually.

## Consequences

Good consequences:

- later desktop slices can stay implementation-focused
- `research_ui` continuity can remain honest without becoming the destination
- shared contracts become the stable seam between shell, preload, renderer, and smoke

Tradeoffs:

- some temporary duplication between native surfaces and browser continuity is acceptable during migration
- renderer slices must stay disciplined about not expanding into engine-owned logic

## Non-Goals

This ADR does not:

- replace engine workflow authority
- commit QuantLab to a web-service or SaaS architecture
- make Stepbit a first-party control plane
- require every desktop surface to migrate in one block
