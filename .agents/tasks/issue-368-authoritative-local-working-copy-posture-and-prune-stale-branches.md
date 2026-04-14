# Issue #368 — Authoritative Local Working-Copy Posture and Stale Branch Pruning

## Goal

Restore a clean and authoritative local starting point for future slices.

## In scope

- define which local branch and worktree are the canonical base after merges
- prune merged branches or worktrees that no longer need to exist
- document when to keep an active worktree and when to remove it
- align local posture with repo workflow rules

## Out of scope

- product behavior
- runtime code
- renderer code
- architecture redesign

## Done when

- the local repo has an unambiguous working base
- stale merged branches or deleted remotes are no longer treated as valid starting points
- the posture is documented and repeatable
