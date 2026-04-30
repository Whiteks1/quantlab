# ADR NNNN: Agent layer on QuantLab — scope, variants, non-goals

- **Status**: Proposed
- **Date**: YYYY-MM-DD
- **Deciders**: TBD
- **Supersedes**: —
- **Superseded by**: —

## Context

QuantLab is a sovereign system. There is interest in adding a layer of agents on
top of it to assist with analysis, slicing, planning, and documentation tasks.
No such layer exists today in a defined form. Before introducing any
agent-related code, contract, or runtime change, the scope of this layer must
be fixed and its non-goals made explicit.

This ADR fixes scope and non-goals. It does not choose a first agent variant,
a trigger mechanism, an implementation path, or any repository layout. Those
decisions are deferred to subsequent ADRs and specs.

## Decision

Adopt an **agent layer** on top of QuantLab under the scope and non-goals
defined below. The first concrete agent, its variant, and its contracts are
deferred to a separate ADR.

All agents introduced under this layer inherit the non-goals of this ADR as
invariants. Any future agent that violates them requires an ADR superseding
this one.

## Scope

The agent layer may:

- Produce analysis artifacts (reports, summaries, comparisons) from read-only
  inputs.
- Assist in slicing technical work into executable units.
- Draft planning artifacts (ADR drafts, spec drafts, issue drafts, PR briefs).
- Produce documentation artifacts.
- Observe and describe system state using read-only access.

All outputs of the agent layer must be deterministic given their inputs, or
explicitly labeled as non-deterministic with rationale.

## Non-goals

The agent layer **must not**:

- **Govern or execute trading decisions.** No agent places, cancels, modifies,
  or routes orders.
- **Govern or execute risk decisions.** No agent sets, alters, or overrides
  risk limits, exposure caps, or hedging rules.
- **Govern or execute runtime behavior.** No agent triggers, halts, or modifies
  production processes, jobs, or services.
- **Write to production state without a human-reviewed change.** Any write path
  requires a human-approved artifact (PR, ticket, or equivalent).
- **Act as an actuator over external systems by default.** Actuation, if ever
  introduced, requires its own ADR and its own boundary contract.

These non-goals are invariants of the layer, not defaults. They apply
regardless of variant, operator, or context.

## Permissions model

- **Default**: read-only access to an explicitly declared allow-list of paths
  and artifacts.
- **Writes**: permitted only into a declared, bounded output area. Never into
  runtime, risk, or trading paths.
- **Secrets and credentials**: out of scope for this ADR. Any future agent that
  requires them needs its own ADR.
- **Human in the loop**: required for any change that leaves the agent's
  output area.

## Variants considered

The layer is defined independently of which variant is implemented first.
Three variants are on the table; exactly one is chosen in a follow-up ADR:

- **Observer** — read-only; produces descriptive artifacts. Lowest boundary
  surface. Recommended as first pilot unless evidence supports otherwise.
- **Analyst** — read-only plus derived artifacts (aggregations, diffs, drafts).
  Still no actuation.
- **Actuator** — can propose changes to be executed by a human-gated path.
  Out of scope for the first pilot under this ADR; would require an explicit
  superseding ADR before implementation.

## Open questions

- Concrete task of the first pilot agent.
- Whether the first pilot writes artifacts or is fully read-only.
- Trigger model: on-demand, scheduled, or event-driven.
- Expected artifact shape and naming for the first pilot.
- PR granularity policy for slices that follow this ADR.
- Observability requirements (log schema, retention, correlation).
- Relationship with any existing automation in the repo, if any.
- Portability requirements across LLM or orchestration providers.

## Consequences

- Unblocks a context-inventory slice (S0.2) and a variant-selection ADR (S0.3).
- Does **not** unblock implementation. No code slice may start before the
  pilot's contracts are defined.
- Establishes grep-able invariants (`non-goals`, `trading`, `risk`,
  `execution`) that downstream PRs must respect.
- Any future ADR introducing actuation must explicitly reference and supersede
  the relevant sections of this ADR.

## References

- Slice plan: agent layer slicing proposal (internal).
- Follow-ups: ADR NNNN+1 (context inventory), ADR NNNN+2 (first agent variant).
