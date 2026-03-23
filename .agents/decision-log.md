# Decision Log — QuantLab

This document records key architectural and workflow decisions.

The goal is to prevent architectural drift and ensure continuity between development sessions.

Each entry includes:

- context
- decision
- consequences

---

# 2026-03-10 — CLI-first architecture

## Context

QuantLab is evolving as a research environment for quantitative strategies.

It could naturally drift toward API layers, services, or platform-style infrastructure.

However, this would introduce unnecessary complexity at the current stage.

## Decision

QuantLab will remain **CLI-first**.

The system will be designed primarily for command-line execution and batch experiments.

## Consequences

- no service layer
- no web API
- no microservices
- workflows centered around CLI commands and artifacts

---

# 2026-03-10 — Branch-first development workflow

## Context

Development involves collaboration between ChatGPT (architecture/design) and Antigravity (execution).

To avoid instability in the repository, changes must be isolated.

## Decision

All work must occur in **dedicated branches**.

Direct commits to `main` are prohibited.

## Consequences

- every change occurs through a branch
- pull requests are the integration mechanism
- main branch remains stable

---

# 2026-03-23 — `.agents` treated as shared repo context for Codex

## Context

The repository memory under `.agents/` was originally phrased around a ChatGPT plus Antigravity split.

Codex now works directly inside the repository and benefits from the same architecture, workflow, and contract context.

## Decision

`.agents/` should be treated as **shared repository context** that is directly consumable by Codex.

Agent-specific phrasing should prefer:

- Codex explicitly, when guidance is Codex-specific
- execution agent generically, when the rule should apply to any implementation agent

## Consequences

- workflow files should not depend on a ChatGPT versus Antigravity split
- Codex can use `.agents/` as a first-class operating handbook
- prompt files may coexist, but Codex should have a dedicated prompt entry

---

# 2026-03-10 — QuantLab as a research laboratory

## Context

QuantLab could evolve toward a live trading platform.

However the current objective is research and experimentation.

## Decision

QuantLab is defined as a **quantitative research laboratory**, not a trading platform.

## Consequences

- focus on experimentation
- reproducible experiments
- strong reporting
- forward evaluation before any live execution
