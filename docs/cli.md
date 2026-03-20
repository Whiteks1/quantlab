# QuantLab CLI Guide

QuantLab is a CLI-first quantitative research environment. Research workflows are driven from `main.py`, which delegates command handling to specialized CLI modules.

## Command Overview

The CLI supports several main modes of operation:

### `run`
Standard backtest execution for a single strategy workflow.

### `forward`
Forward evaluation and resume-aware paper-trading style validation.

### `portfolio`
Portfolio aggregation and portfolio-level analysis across multiple sessions.

### `sweep`
Parameter exploration and optimization workflows.

### `report`
Artifact generation or regeneration for existing runs.

## Design Rules

- `main.py` and `src/quantlab/cli/` are orchestration only.
- Quantitative and domain logic must live in core modules.
- CLI documentation should describe the current repository behavior, not future integrations.

## Outputs

QuantLab writes research artifacts under `outputs/`.

For artifact details, see `.agents/artifact-contracts.md`.