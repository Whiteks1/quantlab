# QuantLab Integration With Stepbit

This document explains how QuantLab should integrate with Stepbit under the current architectural decision.

The key point is:

- Stepbit is not the control plane of QuantLab
- QuantLab is not a subordinate runtime owned by Stepbit
- QuantLab may consume Stepbit capabilities through a narrow, reversible integration boundary

For the authority model, see [quantlab-stepbit-boundaries.md](./quantlab-stepbit-boundaries.md).

## 1. Correct Relationship

The relationship is not:

```text
Stepbit -> controls -> QuantLab
```

and not:

```text
Stepbit -> orchestrates -> QuantLab as a subordinate engine
```

The intended relationship is:

```text
QuantLab -> consumes -> Stepbit capabilities
```

or, at the boundary level:

```text
QuantLab <-> Stepbit
```

with one strict authority rule:

- functional authority over QuantLab remains inside QuantLab

## 2. Integration Goal

The purpose of the integration is to let QuantLab benefit from external AI and automation capabilities without compromising its autonomy.

Good uses of Stepbit for QuantLab include:

- reasoning-assisted interpretation of results
- workflow automation around QuantLab artifacts
- AI-generated suggestions for next actions
- MCP-based access to stable QuantLab execution and reporting surfaces

The integration should not redefine QuantLab's core identity or ownership boundaries.

## 3. Allowed Boundary Surface

The QuantLab boundary exposed to Stepbit should remain narrow and contract-based.

Examples of good boundary surfaces:

- execute a well-scoped QuantLab action
- read canonical artifacts
- inspect machine-readable reports
- query run history
- request AI analysis over QuantLab outputs

In practical terms, that means Stepbit should interact with surfaces such as:

- `main.py --json-request`
- `main.py --signal-file`
- `report.json.machine_contract`
- canonical run artifacts under `outputs/runs/<run_id>/`

## 4. What Stepbit Should Not Own

Stepbit should not become the sovereign owner of:

- QuantLab session lifecycle
- QuantLab risk policy
- QuantLab trading logic
- strategy promotion rules
- broker execution authority
- capital and safety boundaries

Those remain QuantLab-owned concerns.

## 5. MCP Philosophy

The QuantLab MCP surface exists to expose a clean interface to Stepbit, not to surrender internal control.

### MCP should enable

- contract-driven invocation
- artifact access
- external analysis
- bounded automation

### MCP should avoid

- invasive lifecycle control
- internal policy ownership
- deep coupling to QuantLab internals
- making QuantLab dependent on Stepbit to remain useful

## 6. Roadmap Consequence

Because QuantLab is sovereign, its roadmap remains QuantLab-first.

That means the main product priority is still inside QuantLab itself:

- `Stage C.1 - Paper Trading Operationalization`
- then execution safety and broker dry-run stages

The integration track remains secondary and reactive:

- `Stage O - Stepbit Automation Readiness`
- `Stage O.1 - Integration Hardening` only when real consumer friction justifies it

## 7. Practical Integration Rule

A QuantLab-side change is justified by Stepbit only when:

- it improves the external contract
- it reduces boundary friction
- it does not compromise QuantLab independence

If a change exists only to make QuantLab subordinate to Stepbit, it should be rejected or isolated outside the QuantLab core.

## 8. Recommended Next Steps

For QuantLab:

- continue prioritizing its own paper-trading and execution-safety roadmap

For integration:

- keep the QuantLab boundary stable
- let Stepbit consume it cleanly
- avoid moving QuantLab-owned authority into Stepbit
