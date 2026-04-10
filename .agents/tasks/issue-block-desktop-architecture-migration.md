# Desktop Architecture Migration Block

This block groups the real migration slices for the QuantLab Desktop architecture transition.

Order:

1. `#350` Desktop target architecture and shared contract guardrails
2. `#354` TypeScript base real across main, preload, shared, and renderer
3. `#353` Modularize the desktop main process
4. `#355` Complete typed preload bridge and stable Desktop IPC surface
5. `#352` Establish the minimal React shell frame
6. `#359` Migrate core workstation surfaces: Runs, Compare, Candidates
7. `#351` Migrate Run Detail and Artifacts
8. `#357` Migrate Paper Ops, System, and Experiments
9. `#358` Decide and resolve Launch target-state
10. `#356` Retire the legacy shell renderer

Principle:
- one real slice = one issue = one branch = one PR
- micro-cuts stay inside the slice branch and do not become backlog units
