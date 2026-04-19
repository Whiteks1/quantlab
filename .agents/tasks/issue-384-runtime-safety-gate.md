# Issue #384 - Desktop Runtime Safety Gate

## Goal

Harden desktop smoke so it fails when the renderer opens with a broken workbench, not only when bridge/server checks fail.

## In scope

- extend shared smoke result contract with UI safety signals
- verify renderer mode and critical DOM readiness from Electron smoke
- require workbench-ready state in smoke pass criteria

## Out of scope

- surface migration work
- Launch redesign
- legacy retirement
- product copy changes

## Done when

- smoke captures `rendererMode`, `domReady`, and `workbenchReady`
- fallback smoke requires a functional default shell path
- real-path smoke keeps existing server readiness contract and includes UI safety checks
