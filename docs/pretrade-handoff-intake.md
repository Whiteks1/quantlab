# Pre-Trade Handoff Intake

QuantLab now supports a bounded intake for external
`calculadora_riego_trading` handoff artifacts.

This surface exists to consume upstream planning artifacts without
reintroducing the broader `pretrade` runtime that was intentionally reverted.

## Boundary

The integration rule remains:

- the calculator proposes
- QuantLab validates
- QuantLab decides
- QuantLab executes

This means the handoff artifact is treated as external input only.

It does not:

- grant execution authority
- bypass `ExecutionPolicy`
- create broker approval
- create paper or broker sessions

## CLI

Validate a bounded handoff artifact:

```bash
python main.py --pretrade-handoff-validate path/to/quantlab_handoff.json
```

Optionally choose where the local validation artifact should be written:

```bash
python main.py \
  --pretrade-handoff-validate path/to/quantlab_handoff.json \
  --pretrade-handoff-validation-outdir outputs/pretrade_handoff/demo
```

## Output

QuantLab writes:

```text
pretrade_handoff_validation.json
```

The validation artifact records:

- source artifact path
- contract metadata
- pre-trade context
- trade-plan metadata
- explicit rejection reasons when the handoff is incomplete or malformed
- a local QuantLab-owned readiness flag for future draft execution bridging

## Current scope

This intake is intentionally narrow.

It validates:

- handoff contract type and version
- source lineage metadata
- `symbol`
- `venue`
- `side`
- trade-plan contract metadata consistency

It does not yet:

- create a canonical `pretrade` session
- bridge into draft `ExecutionIntent`
- run broader policy approval
- touch any broker submit surface
