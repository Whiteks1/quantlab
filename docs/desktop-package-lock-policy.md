# Desktop Package Lock Policy

Issue: #417

## Decision

Keep `desktop/package-lock.json` in the canonical repository and treat it as the
source of truth for reproducible Desktop installs.

Canonical install command:

```powershell
cd desktop
npm ci
```

## Rationale

The canonical Desktop `package.json` and `package-lock.json` are already aligned:

- `npm ci` succeeds from a clean worktree.
- `npm install --package-lock-only --ignore-scripts` produces no lockfile diff.
- `npm run -s typecheck` succeeds.
- `npm run -s build` succeeds.

The Ecosystem source snapshot used for #416 included a different
`desktop/package-lock.json`, but its `desktop/package.json` also differs from the
canonical repo. Importing only the Ecosystem lockfile would mix dependency
policy with the mechanical Desktop convergence port and could create an
inconsistent manifest/lock pair.

## Source Snapshot Reference

- Source repository: `stepbit-labs/quantlab`
- Source PR: `stepbit-labs/quantlab#3`
- Source commit: `2e935d4789feafdbb58e161097818f3bbeec0f11`

## Policy

- Use `npm ci` for reproducible Desktop installs.
- Keep `desktop/package-lock.json` committed.
- Update `desktop/package-lock.json` only when `desktop/package.json` changes or
  when an explicit dependency policy issue requires it.
- Do not import lockfile changes from Ecosystem snapshots unless the matching
  `desktop/package.json` changes are also intentionally in scope.

## Out Of Scope

- #409 run-detail/native surface migration.
- #410 paper ops/system/experiments migration.
- UX, layout, or branding changes.
- Broad dependency upgrades.
- Supply-chain remediation beyond recording the current `npm audit` result.

## Validation

Performed from `desktop/`:

```text
npm ci
npm install --package-lock-only --ignore-scripts
npm run -s typecheck
npm run -s build
```

Residual risk:

- `npm ci` reports 3 vulnerabilities (2 moderate, 1 high). This slice records
  the existing state only; remediation is intentionally out of scope.
