# Desktop Renderer Rollback Policy

React is the default desktop renderer.

Legacy remains available as a controlled rollback path.

## Start commands

- Default (React): `cd desktop && npm start`
- Rollback (Legacy): `cd desktop && npm run start:legacy`

Equivalent environment override:

```powershell
$env:QUANTLAB_DESKTOP_RENDERER="legacy"
npm start
```

## Rollout validation gate

Before promoting renderer changes, run:

```powershell
cd desktop
npm run smoke:renderer-rollout
```

This command enforces:

1. React smoke fallback is green.
2. Legacy rollback smoke fallback is green.

If either fails, renderer rollout is blocked.
