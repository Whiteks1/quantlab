# Task: Stepbit Integration Roadmap

## Goal
Sequence and track the integration between QuantLab and Stepbit-core to enable AI-orchestrated quantitative research.

## Why
QuantLab is a rigorous research environment. Stepbit-core is an AI orchestration layer. Integrating them allows for automated, reproducible, and scalable strategy discovery while maintaining QuantLab's high standards for auditability and determinism.

## Scope
1. **I/O Contract**: Define the JSON schema for strategy parameters.
2. **Stable CLI**: Harden `main.py` for non-interactive execution.
3. **report.json**: Standardize machine-readable metrics.
4. **Error Policy**: Centralize exit codes and exception mapping.
5. **venv Resolution**: Standardize runtime paths and environment parity.
6. **QuantLab Runbook**: Document CLI operations for AI agents.
7. **Adapter Interface**: Define the `QuantLabTool` interface in Stepbit-core.
8. **E2E Flow**: Verify the bridge with a smoke test research loop.
9. **Stepbit Runbook**: Document orchestration patterns for Stepbit agents.
10. **Events & Signals**: Implement optional push notifications (post-E2E).
11. **Distributed Sweeps**: Implement large-scale scaling (deferred).

## Non-goals
- Live trading integration.
- Expansion of QuantLab's internal strategy logic beyond integration needs.
- Significant UI/Dashboard expansion within QuantLab.

## Inputs
- `.agents/architecture.md`
- `.agents/artifact-contracts.md`
- `.agents/implementation-rules.md`

## Expected outputs
- A functional and verified bridge between QuantLab and Stepbit-core.

## Acceptance criteria
- All 11 steps are completed and verified end-to-end.
- The bridge preserves QuantLab's "research-first" integrity.

## Constraints
- Minimum viable bridge focused on stability first.
- Distributed sweeps are deferred to the final scaling step.

## GitHub issues
- #19 meta: backlog consolidado QuantLab ↔ Stepbit
- #20 feat: integración - Definir contrato input/output QuantLab <-> Stepbit
- #21 feat: quantlab - CLI estable para integración automatizada
- #22 feat: quantlab - Generar report.json consistente para integración
- #23 core: integración - Política de errores y reintentos QuantLab <-> Stepbit
- #24 core: integración - Detectar y usar virtualenv local para ejecución automatizada
- #25 feat: integración - Emitir events/signals estructurados para Stepbit
- #26 docs: integración - Completar runbook QuantLab <-> Stepbit
- #27 test: integration - End-to-end Reasoning Engine -> QuantLabTool flow
- #28 docs: integration - Add QuantLab integration runbook
- #29 feat: integration - Distributed QuantLab sweeps orchestration

## Suggested next step
Proceed to [task-stepbit-io-contract.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-io-contract.md).
