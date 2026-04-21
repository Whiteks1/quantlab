# QuantLab System Governance Matrix

This document defines the canonical governance matrix for QuantLab Research: a local-first quantitative research, evidence, and supervised execution system.

It also defines how the Neural Research Track is governed without changing QuantLab's core identity.

The matrix is intended to be reused as a source-of-truth architecture and governance artifact across docs, planning notes, NotebookLM sources, ADRs, and review workflows.

---

## Matrix Of Governance

| Block | Mandate | Primary risk | Required artifact | Promotion blocker | Owner layer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Product Identity** *(The Quantitative Laboratory)* | Maintain a local-first environment for reproducible research, disciplined validation, and supervised execution. Transform hypotheses into evidence. | Product drift toward an autonomous trading bot, generic dashboard, fintech shell, or AI-marketing surface. | Canonical immutable artifacts such as `config.json`, `metrics.json`, and `report.json`. | If an experiment cannot generate a canonical, auditable, and sufficiently stable `report.json` for comparison and external consumption, it is rejected and does not advance. | **QuantLab Core** *(Authority of Evidence)* |
| **2. System Architecture** *(The Tripartite Model)* | Respect strict boundaries: Quant Pulse proposes, QuantLab requires evidence, Stepbit orchestrates. Stepbit may decide flow, retries, and escalation, but it must not classify the financial value of an experiment beyond the state of the output contract. | Architectural collapse through glue code or by allowing Stepbit to absorb market logic, feature generation, or quantitative validation. | Strict JSON contracts such as `intent.json` for input and `report.json` for output. | If a pipeline or design allows Stepbit to inspect financial metrics to make market decisions instead of routing workflow states, it is blocked immediately. | **Stepbit** *(Control Plane / Orchestrator)* |
| **3. Operational Roadmap** *(The Execution Corridor)* | Subordinate automation to operator visibility and operational safety. Mature execution boundaries by handling transient failure states before broader real-capital exposure. | Jumping into live trading before mature safety limits, signer discipline, stop rules, and order reconciliation. | Canonical session registries, reconciliation artifacts, alert snapshots, and supervised submit evidence. | If a supervised session presents ambiguity between local intent and broker or venue state, `stop-on-ambiguity` is triggered and advancement is blocked. | **Operator & QuantLab Execution** *(Safety Boundary)* |
| **4. Neural Line** *(Track N - Neural Research)* | Integrate learned hypotheses under validation standards equal to or stricter than explicit rules. Enforce mandatory baselines and temporal discipline. | Kaggle-style modeling: optimizing predictive performance while ignoring temporal leakage, regime change, baseline comparison, and operational cost. | `dataset_manifest.json`, `feature_manifest.json`, `model_config.json`, and `training_summary.json`; `validation_summary.json` when evaluation support exists; `model_risk_report.json` as a promotion-layer artifact required before paper promotion. | If a model cannot be reproduced, cannot be compared against explicit or classical ML baselines, or cannot produce a promotion-layer risk report before paper promotion, it must not advance. | **QuantLab Core** *(Neural Research Track)* |
| **5. Build Workflow** *(Engineering Operations)* | Treat production code as the real system design through stable contracts and disciplined promotion. In QuantLab, deployment is not a technical event; it is a promotion event: `research -> paper -> sandbox -> micro-live -> supervised live -> automation`. | Configuration debt, dead experimental branches, undocumented local state, and premature deployment automation. | Local contract validation, stable data schemas, CI validation, and promotion history. | If a module breaks a schema contract or attempts to skip a promotion stage without the required prior artifacts, integration must fail and the change must not merge. | **System Architecture** *(CI/CD & Governance)* |

---

## Why This Matrix Matters

This matrix is more than documentation. It is a decision filter for the system.

Any new pull request, API integration, runtime behavior, execution venue, or learned-model workflow should be evaluated against this table.

If a proposal:

- violates a promotion blocker
- blurs an owner layer
- weakens artifact discipline
- bypasses the promotion chain
- reframes QuantLab as an autonomous trading bot, generic fintech dashboard, or AI product

then it must be rejected or redesigned before promotion.

---

## Decision Rule

If a proposed change violates a promotion blocker, blurs an owner layer, weakens artifact discipline, or bypasses the promotion chain, it must not be promoted until redesigned.

---

## Recommended Uses

This document can be reused as:

- a canonical source in NotebookLM
- a PR review checklist
- an architecture governance note in the repository
- a roadmap decision filter
- an issue triage filter
- a systems-design doctrine for QuantLab Research

---

## Placement

Canonical repository path:

```text
docs/architecture/quantlab-system-governance-matrix.md
```

Do not treat this document as a Neural-only ADR. Neural research is one governed track inside QuantLab, not the identity of the full system.
