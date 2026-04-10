# Issue #354 — TypeScript Base Across Desktop

## Goal
Establish the real TypeScript base for `desktop/` without changing runtime behavior.

## Expected deliverable
- `tsconfig.json`
- `types/global.d.ts`
- `typecheck`
- native use of `desktop/shared`

## Done when
- current Desktop JS entrypoints pass typecheck
- smoke remains green
- no functional change is introduced
