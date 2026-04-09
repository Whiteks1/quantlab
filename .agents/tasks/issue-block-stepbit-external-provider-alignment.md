# Stepbit External Provider Alignment - Proposed Issue Block

This issue block defines the next integration slices needed to turn the existing Stepbit external-provider pattern into a QuantLab-owned, explicitly verified boundary.

## Proposed sequence

1. Issue #211 - QuantLab-owned Stepbit external-provider compatibility smoke
2. Issue #212 - Local sibling validation runbook for the external provider path
3. Issue #213 - External strategy surface policy and deterministic coverage

## Intent

The goal is not to make QuantLab subordinate to Stepbit. The goal is to make the external boundary explicit, reproducible, and reviewable where it already matters:

- canonical `--json-request` invocation
- optional `--signal-file` lifecycle signalling
- canonical `report.json.machine_contract` consumption
- explicitly bounded strategy support for external consumers

## Rules for this block

- Keep QuantLab as the authority over runtime semantics and research behavior.
- Do not port Stepbit runtime ownership into QuantLab.
- Prefer contract, tests, and runbooks over new integration surfaces.
- Treat the checked-in Stepbit external provider as the consumer to match, not as a source of product direction.
- Avoid broadening strategy support implicitly; make the supported surface explicit.
