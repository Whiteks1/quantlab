---
description: QuantLab Branching & Development Model
---

# Branching Model

QuantLab follows a simple but strict branching model to maintain a stable `main` branch.

## Branch Naming Conventions

All development must occur in a feature or fix branch.

-   **Features**: `feat/[stage-id]-[short-description]` (e.g., `feat/m3-selection-rules`)
-   **Fixes**: `fix/[issue-description]` (e.g., `fix/portfolio-aggregation-bug`)
-   **Docs**: `docs/[topic]` (e.g., `docs/quantlab-development-standard`)
-   **Refactor**: `refactor/[module-name]` (e.g., `refactor/backtest-engine`)

## Development Flow

1.  **Checkout**: Always source from `main`.
    ```bash
    git checkout main
    git pull
    ```
2.  **Branch creation**: Create a branch according to the naming convention.
    ```bash
    git checkout -b feat/m3-selection-rules
    ```
3.  **Iterative commits**: Make meaningful, atomic commits.
4.  **Verification**: Ensure all tests pass on the branch.
5.  **Merge**: Merge into `main` only after manual review or validation.

## Stability Guarantees

-   `main` must always be stable and runnable.
-   No code should be committed directly to `main`.
-   `main` represents the latest verified state of the QuantLab research environment.
