# Desktop Platform Convergence Status

Issue: #419

## Status

Desktop platform convergence is complete in the canonical repository.

Canonical repository: `Whiteks1/quantlab`

Canonical `origin/main` after convergence:

- Commit: `bc807998d2d3081c56153201297a7313e4ca607a`
- PR: `Whiteks1/quantlab#423`

## Source Snapshot

The source snapshot ambiguity from #415 was resolved before the port.

- Source repository: `stepbit-labs/quantlab`
- Source PR: `stepbit-labs/quantlab#3`
- Source commit: `2e935d4789feafdbb58e161097818f3bbeec0f11`
- Previous local source checkout:
  `C:\Users\marce\Documents\QUANT-ECOSYSTEM\quantlab`
- Previous source base commit:
  `c444a7ef045111489658e304727ea0a8b955d8fa`

## Canonical Baseline

#415 recorded the original canonical baseline:

- Base commit before convergence:
  `790c629f9f8d16491465f384a665cd28096ea6a3`
- Inventory PR: `Whiteks1/quantlab#420`
- Inventory merge commit:
  `f400527a64a6eeb44a35948eefda9506d0782cbd`

## Completed Slices

- #415: inventory convergence source and canonical baseline
  - PR: `Whiteks1/quantlab#420`
  - Merge commit: `f400527a64a6eeb44a35948eefda9506d0782cbd`
- #416: port converged shell baseline to canonical repo
  - PR: `Whiteks1/quantlab#421`
  - Merge commit: `d6892261c17ba68d6a981412b5026601ced12766`
- #417: reconcile Desktop package-lock policy
  - PR: `Whiteks1/quantlab#422`
  - Merge commit: `f653e7413fd30fc8c7afa26a0210529b85592386`
- #418: restore full convergence DoD in canonical repo
  - PR: `Whiteks1/quantlab#423`
  - Merge commit: `bc807998d2d3081c56153201297a7313e4ca607a`

## Files Ported In #416

- `desktop/main/local-store-service.js`
- `desktop/main/register-ipc.js`
- `desktop/main/stepbit-service.js`
- `desktop/mcp-server.mjs`
- `desktop/shared/snapshot-status.mjs`
- `desktop/tests/snapshot-status.test.mjs`

## Package Lock Status

Decision from #417:

- Keep `desktop/package-lock.json`.
- Use `npm ci` for reproducible Desktop installs.
- Do not import the Ecosystem lockfile because its `desktop/package.json`
  differs from the canonical repo.
- Update the lockfile only when `desktop/package.json` changes or an explicit
  dependency-policy issue requires it.

Reference: `docs/desktop-package-lock-policy.md`

## Preserved Canonical Decisions

The convergence port preserved the canonical QuantLab Research identity:

- QuantLab remains the protagonist.
- Stepbit remains a support/integration boundary.
- Quant Pulse remains an upstream signal/context layer.
- Desktop surfaces remain evidence-first QuantLab surfaces.
- No #409 or #410 product migration was included.
- No branding, layout, Assistant, Stepbit, or Pulse product decisions were
  introduced by the platform convergence port.

Binding brand reference: `docs/brand-guidelines.md`

## Final DoD Result

#418 verified the full Desktop convergence DoD from `desktop/`:

```text
npm ci
npm run -s typecheck
npm run -s build
npm run -s smoke:fallback
npm run -s smoke:real-path
node --test tests/snapshot-status.test.mjs
npm audit --omit=dev --json
git diff --check
```

Result:

- typecheck: pass
- build: pass
- smoke fallback: pass
- smoke real-path: pass
- snapshot status tests: pass
- production audit: pass, zero production vulnerabilities
- diff check: pass
- remote CI: pass

## Residual Risks

- Dev-scope vulnerabilities are still reported by `npm ci`; production audit
  with `npm audit --omit=dev --json` is clean.
- #409 has a local WIP checkpoint on `feat/desktop-native-run-detail` and must
  be rebased/reviewed separately before product work resumes.
- #410 remains blocked until #409 is intentionally resumed or re-scoped.
- The source snapshot PR `stepbit-labs/quantlab#3` remains a traceability
  artifact and should not become the product roadmap source of truth.

## Roadmap Gate

Allowed next slices:

- #409: Desktop native Run Detail and Artifact Explorer surfaces.
- #410: Desktop Paper Ops, System, and Experiments native surfaces after #409
  is explicitly handled.

Not yet allowed:

- Work outside the immediate Desktop roadmap unless it is a critical bug.
- New branding/layout/product changes that bypass
  `docs/brand-guidelines.md`.
- Assistant, Stepbit, Pulse, or risk-calculator surface expansion without a
  scoped issue and explicit boundary review.

## Operational Note

The pre-existing #409 work has been checkpointed locally:

- Branch: `feat/desktop-native-run-detail`
- Commit: `3fab62e77832f9e49c0c1759cb2579b5dd9e59e8`
- Commit message:
  `wip(desktop): checkpoint native run detail migration for #409`

Do not mix that work with platform convergence closure.
