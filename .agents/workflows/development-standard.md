---
description: QuantLab Official Development Workflow Standard
---

# Development Standard

This document defines the official development workflow for QuantLab. All contributors and agents must adhere to these rules to ensure research reproducibility and code quality.

## Core Philosophy

QuantLab is a **research-focused, CLI-first environment**. It is NOT a SaaS platform or a multi-user system. The priority is **reproducibility, traceability, and architectural clarity**.

## Workflow Roles

1.  **Architect (ChatGPT)**: Defines requirements, designs system changes, and provides implementation plans.
2.  **Execution Agent (Antigravity)**: Implements the approved plans, executes tasks, and verifies correctness.

## Development Process

1.  **Planning**: Every change starts with a plan (Stage-level or Task-level).
2.  **Branching**: All work occurs in a dedicated branch. Never commit to `main`.
3.  **Implementation**:
    - Follow layered architecture: `data/`, `indicators/`, `strategies/`, `backtest/`, `execution/`, `reporting/`.
    - Keep `main.py` as a CLI entrypoint only.
    - Use type hints and PEP8 standards.
4.  **Verification**:
    - Add/extend unit tests for any new logic using `pytest`.
    - Verify that outputs are generated in the `outputs/` directory.
5.  **Review**: Changes are reviewed before merging into `main`.

## Constraints

- No side effects on import.
- Pure functions for analytics.
- Paper mode only by default.
- No infrastructure complexity (APIs, AUTH, Multi-user).
