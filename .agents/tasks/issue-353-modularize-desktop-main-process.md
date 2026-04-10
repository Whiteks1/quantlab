# Issue #353 — Modularize Desktop Main Process

## Goal
Split the Electron main process by responsibility after the TypeScript base exists.

## Expected deliverable
- thin `main.js`
- typed modules for bootstrap, window, workspace, IPC, and smoke support

## Done when
- responsibilities are separated into coherent modules
- runtime behavior stays unchanged
