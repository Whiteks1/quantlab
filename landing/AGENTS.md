# QuantLab Landing Agent Guide

This folder is the public web surface for QuantLab Research.

Read these files before changing landing content:

1. `../AGENTS.md`
2. `../docs/brand-guidelines.md`
3. `../docs/landing-governance.md`

If you are working with multiple agents, follow the repo-level coordination rules in `../AGENTS.md` first.

## Working Rules

- Keep changes scoped to the public landing surface.
- Treat `docs/brand-guidelines.md` as the source of truth for positioning, voice, and visual direction.
- Treat `docs/landing-governance.md` as the source of truth for landing ownership and workflow.
- Do not create alternate hero copy, taglines, or color systems in landing files.
- Do not duplicate roadmap or contract content that belongs in repo docs.
- Do not create parallel landing sections for the same message.
- Replace stale copy instead of leaving old variants in place.
- Use shared constants or shared content files when the same copy appears in multiple landing components.
- Keep the landing aligned with the GitHub Pages workflow in `.github/workflows/pages.yml`.
- If public positioning changes, update `docs/brand-guidelines.md` first and the landing second.

## Validation

- If you change copy, verify it still matches the brand guide.
- If you change layout or styles, verify the landing remains readable and responsive.
- If you change the public surface, prefer the smallest reversible patch.
- If you add or move a surface, check for duplication across `landing/`, `docs/`, and `src/`.
