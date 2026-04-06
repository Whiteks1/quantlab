# QuantLab Landing Governance

## Scope

The `landing/` directory is the public web surface for QuantLab Research.

It owns presentation only:

- page copy
- layout and visual system
- local preview behavior
- GitHub Pages deployment payload

It does not own:

- trading logic
- CLI behavior
- broker or paper execution logic
- core research contracts
- product roadmap decisions

## Source Of Truth

Use this order when resolving conflicts:

1. `docs/brand-guidelines.md`
2. `docs/landing-governance.md`
3. `landing/index.html`
4. `landing/styles.css`
5. `landing/app.js`
6. `landing/README.md`

If a public positioning change is required, update the brand guide first and the landing surface second.

## Ownership Rules

- `docs/brand-guidelines.md` owns positioning, voice, taglines, and visual direction.
- `landing/index.html` owns rendered public copy and structural content.
- `landing/styles.css` owns the visual tokens and layout treatment for the public web surface.
- `landing/app.js` owns only lightweight interaction and reveal behavior.
- `landing/README.md` owns local preview and deploy notes for contributors.

## Anti-Duplication Rules

- Do not create alternate taglines, hero copy, or public positioning in multiple files.
- Do not copy roadmap details into the landing surface.
- Do not duplicate brand guidance inside landing markup or styles.
- Do not introduce a second palette or a second naming system for the web surface.
- Do not add copy that conflicts with `docs/brand-guidelines.md` or the repo-level contract docs.

## Change Workflow

1. Identify whether the change is brand, copy, layout, or deploy related.
2. Update the canonical doc first if the public position or voice changes.
3. Update the landing surface second.
4. Keep the change small and limited to the landing surface unless the task explicitly spans the repo.
5. Verify the deploy path still targets `landing/` through GitHub Pages.

## Review Checklist

- Does the title, description, and hero still match the brand guide?
- Does the landing README stay operational and non-promotional?
- Are the copy, palette, and layout still consistent with the brand tokens?
- Did the change avoid duplicating content that belongs in docs?
- Is the GitHub Pages workflow still publishing `landing/` without extra plumbing?
