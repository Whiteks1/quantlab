# Known Issue: Shell Bootstrap Smoke Regression

**GitHub Issue:** #427  
**Status:** Open (blocking #409, #410)  
**Severity:** Medium  
**Discovered:** 2026-04-20  
**Introduced by:** #409 work (native run detail migration checkpoint)

## Symptom

Smoke tests fail with:
```
shellReady: false
hasShell: false
error: "run detail unavailable (activeId=..., hasTabsBar=true, hasShell=false)"
```

Failure occurs in both `smoke:fallback` and `smoke:real-path`.

## Root Cause

Main shell initialization or renderer shell bootstrap not completing successfully.

The failure point is upstream of MainContent routing—likely in:
- `desktop/main/` (main process initialization)
- Shell renderer bootstrap code
- NOT in surface routing or component logic

## Affected Tests

- `npm run smoke:fallback` — fails (research_ui unreachable, shell absent)
- `npm run smoke:real-path` — fails (shell absent)

Both show identical JSON state across all 20+ metrics.

## Context

- **Last known passing state:** #418 convergence DoD completion (commit `bc80799`)
- **Failure introduced:** During #409 native run detail migration (WIP checkpoint on `feat/desktop-native-run-detail`)
- **Not a regression from #410:** #410 does not change shell bootstrap; verified identical failure state on `origin/main`

## Workaround

None. Smoke tests fail on any branch post-#409 checkpoint.

## Impact

- Blocks merge of #410 under strict DoD interpretation (expects smoke green)
- Does not block #410 if accepted as pre-existing known issue
- Requires explicit resolution or acceptance before product work resumes

## Next Steps

1. Investigate shell bootstrap in #409 WIP checkpoint
2. Fix root cause or defer shell work to separate issue
3. Restore smoke to passing state before final merge
4. Document as part of #409 completion or create follow-up issue #?? for shell bootstrap hardening
