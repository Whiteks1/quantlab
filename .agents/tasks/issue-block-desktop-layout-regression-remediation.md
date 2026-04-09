# Desktop Layout Regression Remediation — Proposed Issue Block

This issue block targets the remaining Desktop/UI regression after the workstation and support-lane slices already merged. The problem is no longer shell semantics alone. The current regression is spatial: too much empty pane ownership, weak active-surface dominance, and poor width allocation between the workbench and its auxiliary lanes.

## Proposed sequence

1. Issue #342 — Collapse empty panes and restore primary workbench ownership
2. Issue #343 — Enforce stronger active-surface focus and context containment
3. Issue #344 — Rebalance runs-family density and right-rail space budget

## Intent

The goal is to fix the remaining layout/workbench problems now visible in real desktop use:

- the active surface still loses too much width to empty or low-value panes
- context accumulation still weakens focus after a short navigation sequence
- runs-family surfaces remain compositionally sparse in some places and over-compressed in others

## Rules for this block

- Keep the focus on `desktop/` renderer composition and shell containment only.
- Do not mix this block with core Python, broker, CLI, or `research_ui` changes.
- Treat this as layout/workbench remediation, not a restart of the broader workstation direction.
- Prefer slices that improve space ownership, density, and surface focus over decorative polish.
