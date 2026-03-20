# Task: QuantLabTool Adapter Interface

## Goal
Define the high-level interface for the `QuantLabTool` in Stepbit-core.

## Why
Before implementation, we must agree on how Stepbit agents will interact with the tool. A clean interface ensures that agents can reason about research tasks without being exposed to CLI flags or file paths.

## Scope
- Define the `QuantLabTool` class signature in Stepbit.
- Define the schema for input arguments (e.g., `ticker`, `strategy`, `params`).
- Define the schema for the tool output (what the agent sees after execution).
- Map high-level tool errors to Stepbit's internal agent signals.

## Non-goals
- Implementing the shell execution logic.
- Implementing the result parsing logic.

## Inputs
- `.agents/tasks/task-stepbit-io-contract.md`
- Stepbit-core tool architecture documentation.

## Expected outputs
- A Python interface definition (e.g., `quantlab_tool.py` wrapper).
- Example tool-call JSON for an LLM agent.

## Acceptance criteria
- The interface is stateless and decoupled from QuantLab's internal logic.
- The interface covers `run`, `sweep`, and `forward` operations at a high level.

## Constraints
- Follow Stepbit-core's tool standards.
- No QuantLab business logic in the interface.

## GitHub issue
- #19 meta: backlog consolidado QuantLab ↔ Stepbit

## Derived from
- `.agents/tasks/stage-stepbit-integration-roadmap.md`

## Suggested next step
Move to [task-stepbit-e2e-flow.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-e2e-flow.md).
