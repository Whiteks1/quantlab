# Issue #217 — Desktop preload bridge hotfix

## Scope
- Fix the Desktop/UI preload bridge syntax regression so Electron exposes `window.quantlabDesktop` again.
- Keep the slice limited to `desktop/preload.js` plus `.agents` continuity.

## Allowed paths
- `desktop/preload.js`
- `.agents/tasks/issue-217-preload-bridge-hotfix.md`
- `.agents/session-log.md`

## Out of scope
- `desktop/main.js`
- `desktop/scripts/smoke.js`
- `desktop/renderer/**`
- `research_ui/**`
- `src/quantlab/**`
- CI, broker, and CLI changes

## Validation
- `node --check desktop/preload.js`
- `npm run smoke` from `desktop/`
