---
description: How to execute the next implementation step in QuantLab
---

# Execute Task

This document defines the procedure for executing a task in QuantLab.

## Prerequisites

-   A task has been defined in `Task.md`.
-   A dedicated branch has been created.
-   The environment is set up and functional.

## Execution Procedure

1.  **Read and Plan**: Consult `Task.md` and the existing implementation plans.
2.  **Implementation**:
    -   Apply the specific code changes.
    -   Follow the QuantLab coding standards (Vanilla CSS, PEP8, type hints, etc.).
    -   Maintain a layered architecture: `data/`, `indicators/`, `strategies/`, `backtest/`, `execution/`, `reporting/`.
3.  **Verification**:
    -   Run `pytest` for any logic changes.
    -   Manually verify CLI runs and outputs in `outputs/`.
4.  **Logging**: Update `Task.md` as each step is completed.
5.  **Artifact Generation**: Ensure that any new metrics or reports are generated and verifiable.

## Safety Guards

-   Always work in **paper mode** unless live trading is explicitly required.
-   Never commit API keys or sensitive data.
-   Ensure all outputs are written to the `outputs/` directory.
-   Do NOT change `main.py` business logic; it is a CLI orchestrator.
