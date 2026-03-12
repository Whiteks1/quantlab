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