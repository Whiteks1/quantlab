# Task: Event Signalling & Session Hooks

## Goal
Add a minimal, optional session-level signalling mechanism so QuantLab can emit structured completion/failure signals for Stepbit without relying only on filesystem polling.

## Why
The current integration works through CLI invocation, exit codes, and artifact inspection. For longer or more structured research flows, Stepbit benefits from a lightweight push-style signal that indicates when a session starts, completes, or fails, while preserving QuantLab’s offline-first and CLI-first model.

## Scope
- define a minimal set of session-level event types
- implement one lightweight signalling transport for the first iteration:
  - `--signal-file`
- emit structured signals for the main session lifecycle outcomes
- ensure emitted signals include enough information for Stepbit to locate and interpret the produced result
- document the signal payload structure and operational usage

## Non-goals
- webhook delivery in this issue
- message brokers or infrastructure-heavy event systems
- trade-by-trade or bar-by-bar streaming
- retry engines, delivery guarantees, or event deduplication layers
- redesigning the QuantLab execution model

## Inputs
- current CLI integration behavior
- `main.py`
- `src/quantlab/cli/`
- `report.json` artifact contract
- current exit code policy
- current run/session identity conventions

## Expected outputs
- CLI support for an optional `--signal-file`
- structured session-level signal payloads
- documentation of emitted event types and payload shape

## Acceptance criteria
- QuantLab can optionally emit a signal when a session:
  - starts
  - completes successfully
  - fails
- signals do not break normal offline CLI usage
- emitted payloads include at least:
  - event type
  - run/session identifier when available
  - status
  - path to `report.json` when available
- Stepbit can consume the signal without requiring polling-only behavior

## Constraints
- prefer standard library only
- keep the transport local and lightweight
- keep changes minimal and reviewable
- preserve CLI-first behavior
- do not introduce heavy infrastructure dependencies

## GitHub issue
- #25 feat: integración - Emitir events/signals estructurados para Stepbit

## Suggested next step
Define the minimal session event model and implement file-based signalling first, leaving webhooks for a future issue if still needed.