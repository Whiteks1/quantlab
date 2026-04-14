# Issue #370 — Roadmap Promotion Gating and Clarity

## Goal

Update `docs/roadmap.md` so it stays a product and system roadmap, not a historical changelog of the repo.

## In scope

- introduce an explicit gate between `D.2` and `E`
- add minimum exit criteria for `C.1`, `D.2`, and `E`
- reduce historical overload in advanced stages
- add a minimal promotion policy for secrets and canonical alerts
- make Desktop/UI explicit as a transversal capability track
- reframe `D.2` as the central hardening and evidence frontier

## Scope rule

By default, touch only:

- `docs/roadmap.md`

Any change outside that file must be minimal and justified by direct contradiction.

## Out of scope

- runtime code
- desktop code
- engine code
- workflow or governance cleanup
- runbook expansion

## Done when

- `docs/roadmap.md` is more compact and more promotable
- the `D.2 -> D.3/E.0 -> E` path is explicit
- advanced-stage exit criteria are visible
- Desktop/UI is explicit without becoming a primary linear stage
- the roadmap stops overstating exact repository-state precision
