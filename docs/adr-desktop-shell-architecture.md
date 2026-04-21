# ADR: Desktop Shell Architecture
**Date**: 2026-04-19
**Status**: Accepted

## Context
Within the `quant_lab` repository, two parallel desktop shell implementations currently coexist:
1. **The Legacy/Transitional Workstation**: Built on older web technologies, but fully implements the current functional product vision (Launch, Runs index, Candidate selection, Compare, Artifacts rendering, and runtime telemetry).
2. **The React Shell**: Built on React and Vite, delivering a fundamentally stronger, more stable, and structurally consistent UI baseline.

This has caused tension between *functional completeness* (the legacy shell) and *architectural stability* (the React shell). Treating both as competing canonical destinations fragments development effort and introduces release risk. 

## Decision
We establish a phased architectural boundary rather than forcing an immediate migration.

1. **Short-Term (April v0.1 Release)**: The **Legacy/Transitional Workstation** is the official release surface. It already contains the verified "happy path" and functional value. We will freeze new features here and only accept stabilization/bug fixes required for v0.1.
2. **Medium/Long-Term (vNext Architecture)**: The **React Shell** is designated as the canonical architecture. 
3. **Migration Policy**: We eliminate the "competing desktops" paradigm. The legacy workstation becomes the functional blueprint/UX reference for the React shell. Post-v0.1, all new functionality and migrated slices must land in the React shell.

## 2026-04-20 Clarification
`#411` formalizes desktop product intent and continuity boundaries; it does not implement Launch expansion or legacy retirement.

Launch remains part of the QuantLab Research workstation flow, not a separate product identity. The release surface may keep the current workflow panel, assistant commands, and browser-backed continuity where required, but future work should migrate Launch toward native, supervised, evidence-linked operation rather than expanding `research_ui` as the product owner.

The legacy workstation remains the v0.1 release surface. `research_ui` and browser-backed paths are continuity mechanisms only; they are not the long-term shell architecture.

## 2026-04-21 Clarification: Desktop v1 Release Boundary

`#442` defines Desktop v1 as a release-state boundary, not as a new implementation slice.

Desktop v1 is a functional operator workstation with explicit transitional boundaries. Legacy remains the default release runtime where still required for complete operator flow. React is a validated selectable runtime and the canonical future direction, but not yet the default release path.

This means Desktop v1 does not require pretending the migration is complete. It requires an honest operator release state:

- `npm start` remains the default release runtime while complete operator flow still depends on legacy-backed paths.
- `npm run start:react` remains the validated selectable React runtime.
- React remains the canonical future shell direction.
- Making React the default runtime is post-v1 unless the remaining Launch / operator-flow boundary is resolved explicitly.
- `#412` must not be interpreted as broad legacy deletion until its preconditions are satisfied or the issue is re-scoped.
- `#266` remains post-v1 unless it is recut into a much smaller release-alignment slice.

## Operational Guardrails
To enforce this architectural division, the following rules apply immediately:

- **No new feature work lands in the legacy/transitional workstation after the v0.1 scope freeze, except release-blocking fixes.**
- **Any post-v0.1 desktop slice must declare whether it is:**
  - `[legacy release fix]`
  - *or* `[React migration slice]`

## Consequences
- **Positive**: v0.1 is unblocked and relies on the already-validated inspection flows. We avoid the high risk of rushing a full feature parity migration into React before April 30.
- **Positive**: The technical debt of the legacy shell is bounded; it is officially a transitional release rather than a permanent foundation.
- **Negative/Trade-off**: For the v0.1 cycle, we accept delivering a stable but technically indebted UX renderer, deferring the cleaner React foundation to future milestones.

*The guiding principle: The legacy workstation currently owns the v0.1 happy path, but the React runtime is the stronger long-term shell foundation. Release should not be blocked by a full migration now; however, future desktop work should converge on the React shell and treat the older workstation as a functional reference, not the final architecture.*
