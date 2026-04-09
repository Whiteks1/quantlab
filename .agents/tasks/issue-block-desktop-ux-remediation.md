# Desktop UX Remediation — Proposed Issue Block

This issue block defines the next Desktop/UI slices needed to move QuantLab Desktop from a functional shell into a more disciplined workstation.

## Proposed sequence

1. Issue #286 — Workstation containment and active-surface discipline
2. Issue #287 — Simplify right-rail support lane semantics
3. Issue #288 — Add decision clarity across runs surfaces

## Intent

The goal is to address the three dominant Desktop/UI problems now visible in stable use:

- workstation containment is weak
- the support lane is semantically duplicated
- decision readiness is not explicit enough

## Rules for this block

- Keep the focus on `desktop/` and `research_ui/` surfaces only.
- Do not mix Desktop/UI work with core Python, broker logic, or CLI changes.
- Treat early bootstrap failures as debugging history, not as the canonical desktop state.
- Preserve the workstation direction: fewer ambiguities, clearer focus, stronger next-step guidance.
