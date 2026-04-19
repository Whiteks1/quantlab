# QuantLab Desktop v0.1 - April 2026 Sprint Freeze

Status: active  
Target date: 2026-04-30  
Scope owner issue: #391

## Release target

Ship a local-first Desktop v0.1 that is stable, demonstrable, and explicit about known limitations.

This sprint does not attempt to complete the full Desktop migration roadmap.

## Must ship

- default desktop launch is stable with `npm start`
- no placeholder-only shell as the default user experience
- core inspection flow is usable: Runs -> Run Detail -> Artifacts
- decision flow is usable when data exists: Candidates and Compare
- runtime and degraded state messaging is clear enough for local operations
- smoke and typecheck pass on `main`
- quickstart and manual validation checklist are published
- known limitations are explicit

## Should ship

- launch pathway is minimally usable or clearly marked as transitional
- System and Paper Ops surfaces communicate readiness/degraded state clearly
- product proof artifacts exist (screenshots and short release proof notes)
- branch and worktree hygiene is clean at release candidate closeout

## Not now

- full React surface migration
- legacy renderer retirement
- major Launch redesign
- new roadmap capability expansion
- Stepbit advanced integration and distributed orchestration
- live trading extension work
- visual-system rewrites that do not improve v0.1 usability

## Issue mapping

- #391 - scope freeze and acceptance checklist authority
- #384 - desktop safety and runtime stability blocker
- #392 - core happy-path inspection flow restoration
- #393 - launch/system/degraded-state clarity
- #394 - release hardening, quickstart, validation, known limitations

Reference only, not part of this sprint unless directly required:

- #264, #265 - native Run Detail and Artifact Explorer direction
- #351, #357, #358, #356 - renderer migration and cleanup follow-ups
- #61, #29, #19 - Stepbit integration track

## Acceptance checklist (release gate)

Use this gate before calling v0.1 ready.

1. Desktop opens from `desktop/` with `npm start` on the target machine.
2. The default shell is functional and usable (not placeholder-only).
3. Runs list is inspectable from API or local fallback.
4. At least one run can be opened to detail and artifacts.
5. Candidates and Compare are usable when enough run data exists.
6. Degraded/offline states are explicit and non-crashing.
7. Validation commands pass:
   - `npm run typecheck`
   - `npm run smoke:fallback`
   - `npm run smoke:real-path`
8. Quickstart and manual validation docs match actual behavior.
9. Known limitations are documented.
10. `main` is clean and no stale sprint branches/worktrees remain.

## Governance note

During this sprint, no new architecture track starts unless it is required to close a must-ship item above.
