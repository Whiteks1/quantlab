# Desktop Right-Rail Assistant Clarity — Proposed Issue Block

This issue block defines the next Desktop/UI slices needed to remove the duplicated support semantics in the right rail and make the shell easier to read and operate.

## Proposed sequence

1. Issue #218 — Quick commands versus assistant surface separation
2. Issue #219 — Assistant output locus and history clarity
3. Issue #220 — Stepbit routing and support-mode separation
4. Issue #221 — Right-rail density and vertical-noise reduction

## Intent

The goal is to stop the right rail from behaving like two overlapping assistants.

QuantLab should expose:

- one compact command surface for deterministic shortcuts
- one single assistant surface for history and responses
- one explicit Stepbit route when reasoning is needed

## Rules for this block

- Keep the right rail support-oriented, not chat-first.
- Do not introduce new backend, protocol, or LLM dependencies.
- Do not blur deterministic QuantLab commands with Stepbit reasoning.
- Preserve workstation hierarchy: workbench first, support lane second.
- Favor semantic clarity over adding more controls.
