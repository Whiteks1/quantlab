# Issue #392 - Desktop Happy-Path Gate

## Goal

Make desktop smoke assert the minimum operator happy-path (Runs -> Run Detail -> Artifacts -> Candidates -> Compare/guard) instead of checking only shell bootstrap.

## In scope

- extend the shared smoke result contract with happy-path readiness fields
- execute deterministic UI-path checks from Electron smoke
- keep fallback and real-path smoke strict on non-breaking flow readiness
- keep missing-data handling explicit (guarded compare / empty states)

## Out of scope

- renderer migration work
- React/Vite surface implementation
- new IPC channels or model families outside smoke
- visual redesign

## Done when

- smoke result persists happy-path readiness signals
- `smoke:fallback` fails if the core inspection flow is broken
- `smoke:real-path` keeps real-server readiness and also verifies the inspection flow
