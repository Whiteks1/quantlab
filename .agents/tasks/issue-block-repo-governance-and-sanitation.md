# Issue Block — Repo Governance and Sanitation Alignment

## Why this block exists

The repository has an active mismatch between:

- the documented authority of `.agents/current-state.md`
- the actual local Git posture and branch/worktree reality
- the workflow rules after the desktop main-process modularization

This block keeps the repair narrow and operational. It is not a product or runtime block.

## Issues in this block

1. Issue #366 — Align `current-state.md` with actual repository authority and maintenance policy
2. Issue #367 — Update agent workflow for modular Desktop ownership and mandatory post-merge hygiene
3. Issue #368 — Restore authoritative local working-copy posture and prune stale merged branches/worktrees

## Ordering

1. `#366` first so the repo state document becomes trustworthy again
2. `#367` second so workflow and ownership rules match the current architecture
3. `#368` last so sanitation follows the updated authority and workflow rules

## Guardrails

- no runtime changes
- no renderer changes
- no core Python changes
- no CI changes unless strictly required by workflow documentation alignment
- keep this as repo governance and hygiene only
