# Issue #313 — Restore real-path research_ui reachability in main

## Goal
Restore the real desktop path in `main` so Electron reaches `research_ui` from a clean worktree instead of falling back to local runs because it resolved the wrong project root.

## Why this matters
`npm run smoke:real-path` from a clean worktree on `origin/main` currently fails with:

- `bridgeReady: true`
- `localRunsReady: true`
- `serverReady: false`
- `apiReady: false`
- `serverUrl: ""`

The desktop shell is booting, but the real browser/API path is not.

## Scope

### In scope
- `desktop/main.js`
- `desktop/scripts/smoke.js`
- `.agents/session-log.md`

### Out of scope
- `src/quantlab/**`
- core/broker/CLI logic
- `research_ui/**`
- CI changes unless the local validation path proves they are required

## Hypothesis
Two desktop-side assumptions can break real-path validation from a clean worktree:

- worktrees whose folder name is not exactly `quant_lab` can resolve the sibling checkout `.../quant_lab` before the actual current checkout
- `desktop/main.js` only probes `research_ui` on port `8000`, while `research_ui/server.py` can auto-increment to `8001+` when the base port is busy

## Done when
- clean worktree on `origin/main` resolves its own checkout as project root
- `npm run smoke:fallback` passes
- `npm run smoke:real-path` passes
