# QuantLab Use Cases

This document describes bounded use cases for QuantLab with optional Stepbit support.

QuantLab remains the evidence authority. Stepbit may assist with orchestration, repeated workflows, and interpretation, but it must not become the owner of strategy validity, risk policy, broker authority, or execution decisions.

## 1. Supervised Strategy Research Loop

Goal:

- speed up research iteration without moving validation authority out of QuantLab

Flow:

1. The operator defines a research question, for example a mean-reversion idea with RSI.
2. Stepbit may propose candidate parameter sets or workflow steps.
3. QuantLab runs the backtests and produces canonical artifacts.
4. The operator reviews `report.json`, run metrics, drawdown, stability, and artifacts.
5. Stepbit may summarize trade-offs, but QuantLab artifacts remain the source of truth.

Result:

- a reviewable research shortlist, not an autonomous trading decision

## 2. Paper-Session Review And Promotion Discipline

Goal:

- use automation support to reduce paper-session ambiguity while preserving operator control

Flow:

1. QuantLab produces paper-session artifacts and status files.
2. Stepbit may watch for missing artifacts, stale status, or review tasks.
3. The operator reviews the paper runbook, session status, metrics, and failure reasons.
4. Any promotion decision remains manual and evidence-based.

Result:

- clearer paper-to-broker readiness without weakening promotion gates

## 3. Broker-Safety And Submit Review Support

Goal:

- help the operator inspect supervised broker-submit evidence without granting autonomous authority

Flow:

1. QuantLab produces submit, reconciliation, alert, and supervision artifacts.
2. Stepbit may summarize the latest state or route the operator to relevant files.
3. The operator verifies ambiguity, rejected orders, fills, cancellations, and alert status.
4. QuantLab safety policy and broker boundaries remain authoritative.

Result:

- faster operator review of broker-facing evidence, not automated live trading

## 4. Research Report Generation

Goal:

- convert QuantLab artifacts into readable summaries without changing the underlying evidence

Flow:

1. QuantLab generates run, comparison, paper, or broker artifacts.
2. Stepbit may prepare a Markdown summary with links to the canonical files.
3. The summary must cite the source artifacts and must not invent state changes, promotions, or executions.

Result:

- human-readable reporting over QuantLab evidence

## 5. Future Learned-Model Research Assistance

Goal:

- support learned-model research only after artifact contracts and evaluation discipline exist

Flow:

1. QuantLab defines dataset, feature, model, and training-summary artifacts.
2. Stepbit may later orchestrate build-dataset -> train -> validate -> compare workflows.
3. QuantLab remains responsible for dataset validity, feature definitions, model evaluation, and promotion rules.
4. Learned-model outputs cannot become paper or execution actions without downstream validation.

Result:

- disciplined learned-model research, not AI trading automation

## Non-Goals

These use cases must not become:

- autonomous live trading
- Stepbit-owned strategy authority
- Stepbit-owned risk policy
- broker execution without QuantLab preflight and operator supervision
- learned-model promotion without N.0/N.1/N.2 evidence discipline
- marketing claims detached from canonical artifacts
