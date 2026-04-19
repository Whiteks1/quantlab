# Issue #393 - Runtime State Clarity for v0.1

## Goal

Make degraded/runtime-offline states explicit so Desktop remains understandable and demonstrable even when browser-backed surfaces are unavailable.

## In scope

- clarify runtime mode messaging (managed, local-only fallback, degraded)
- mark Launch browser path as transitional in shell copy
- improve System and Paper Ops wording for missing sessions/services
- keep Stepbit offline state explicit and non-blocking

## Out of scope

- Launch redesign
- React/Vite migration work
- new backend contracts
- feature expansion beyond clarity and safe degraded behavior

## Done when

- runtime mode is explicit in shell status copy and support summaries
- Launch browser surface is clearly transitional and non-blocking
- System/Paper Ops empty states read as expected conditions, not crashes
- smoke fallback + real-path still pass
