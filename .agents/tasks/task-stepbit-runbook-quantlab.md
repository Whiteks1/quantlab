# Task: QuantLab Runbook for Stepbit

## Goal
Create a concise operational runbook inside the QuantLab repository that explains how Stepbit should invoke, validate, and troubleshoot QuantLab in its current integration-ready form.

## Why
After stabilizing the JSON request path, machine-readable reporting, error policy, runtime resolution, and validating the first end-to-end slice, the integration now needs a single operational source of truth. The runbook should help both humans and AI agents execute QuantLab reliably and interpret outcomes correctly.

## Scope
- document the current recommended invocation pattern for Stepbit -> QuantLab execution
- document the role of:
  - `--json-request`
  - `report.json`
  - exit codes
  - `--check`
  - `--version`
- provide minimal command patterns for:
  - run
  - sweep
  - forward
  - portfolio, only if already naturally supported and stable
- explain the expected machine-readable artifacts and where to find them
- explain the meaning of common failure outcomes and how to respond
- include a short troubleshooting section for configuration/runtime/data-related failures
- reference the canonical internal docs already created during the integration work

## Non-goals
- documenting every internal module or function
- creating external documentation sites or wikis
- redesigning the integration architecture
- documenting unimplemented future features as if they were operational

## Inputs
- `.agents/stepbit-io-v1.md`
- `.agents/artifact-contracts.md`
- `.agents/session-log.md`
- completed work from issues #20, #21, #22, #23, #24, and #27

## Expected outputs
- a new file: `.agents/stepbit-runbook.md`

## Acceptance criteria
- the runbook is concise, operational, and action-oriented
- an AI agent can use it to execute a basic QuantLab run via the CLI
- the runbook clearly identifies:
  - how to invoke QuantLab
  - which artifact is canonical
  - how to interpret exit codes
  - how to verify runtime health before execution
- the runbook reflects current repo reality rather than aspirational future behavior

## Constraints
- must live in `.agents/`
- must prioritize reproducibility and operational clarity
- must not duplicate large sections of other docs unnecessarily
- prefer linking/reference patterns over redundant duplication

## GitHub issue
- #26 docs: integración - Completar runbook QuantLab <-> Stepbit

## Suggested next step
Inspect the current integration-ready behavior and write a runbook organized around: prepare runtime, invoke QuantLab, inspect artifacts, interpret results, recover from common failures.
