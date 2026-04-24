# Desktop React Legacy Dependencies (Post-#480)

This note records the remaining legacy dependencies after removing React critical-flow reliance on legacy accessors.

## Removed in this slice

- `desktop/renderer/hooks/useLegacyBridge.js` (deleted)
- Positional `openTab(kind, arg, href)` shim in React context API

## Remaining legacy dependencies (non-critical)

- `desktop/renderer/legacy.html`
- `desktop/renderer/app-legacy.js`
- `desktop/renderer/app.js` (legacy runtime bootstrap path)
- `desktop/main/window.js` rollback selector (`QUANTLAB_DESKTOP_RENDERER=legacy`)

## Why they remain

- They are rollback/runtime-boundary dependencies, not React critical-flow data accessors.
- React run detail/artifacts/jobs/runtime paths continue through typed preload/shared contracts.

## Promotion posture

- React critical flows should not add new direct global legacy accessors.
- Legacy runtime assets remain until renderer-default promotion and rollback hardening are complete.
