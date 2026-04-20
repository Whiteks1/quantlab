# Desktop Platform Convergence Inventory

Issue: #415

## Purpose

This inventory fixes the contract for the Desktop platform convergence port before
any functional code is moved into the canonical product repository.

Canonical product repository: `Whiteks1/quantlab`

Local canonical checkout used for this inventory:
`C:\Users\marce\Documents\QUANT LAB PERSONAL\worktrees\quantlab-issue-415`

## Canonical Baseline

- Remote: `https://github.com/Whiteks1/quantlab.git`
- Default branch: `main`
- Base ref: `origin/main`
- Base commit: `790c629f9f8d16491465f384a665cd28096ea6a3`
- Base commit summary: `docs: update current-state.md to reflect Desktop v0.1 RC and D.2 posture`
- Worktree policy applied: the primary canonical checkout was dirty, so this
  slice used a fresh worktree from `origin/main`.

Primary canonical checkout status observed before creating this worktree:

```text
branch: feat/desktop-native-run-detail
modified:
  desktop/main/smoke-service.js
  desktop/renderer/app-legacy.js
  desktop/renderer/components/App.jsx
  desktop/renderer/components/MainContent.jsx
  desktop/renderer/components/RunsPane.jsx
  desktop/renderer/components/Sidebar.jsx
  desktop/renderer/hooks/useLegacyBridge.js
untracked:
  desktop/renderer/components/RunDetailPane.css
  desktop/renderer/components/RunDetailPane.jsx
  desktop/renderer/components/TabsBar.css
  desktop/renderer/components/TabsBar.jsx
```

Those changes were not touched.

## Ecosystem Source State

Local Ecosystem checkout:
`C:\Users\marce\Documents\QUANT-ECOSYSTEM\quantlab`

- Remote: `https://github.com/stepbit-labs/quantlab.git`
- Local branch: `feat/desktop-shell-convergence`
- HEAD commit: `c444a7ef045111489658e304727ea0a8b955d8fa`
- HEAD summary: `Merge pull request #2 from stepbit-labs/feat/react_refactor`
- Related merged PR: `https://github.com/stepbit-labs/quantlab/pull/2`

Important traceability finding:

The desktop shell convergence delta is not currently represented by a committed
source PR or source commit in the Ecosystem repository. It exists as a dirty
local working-tree delta on top of `c444a7ef045111489658e304727ea0a8b955d8fa`.

Observed Ecosystem dirty files:

```text
modified:
  desktop/main/local-store-service.js
  desktop/main/register-ipc.js
  desktop/main/stepbit-service.js
  desktop/mcp-server.mjs
  desktop/package-lock.json
  desktop/tests/snapshot-status.test.mjs
untracked:
  desktop/shared/snapshot-status.mjs
```

Observed dirty diff stat, excluding the untracked file:

```text
desktop/main/local-store-service.js    |  7 +---
desktop/main/register-ipc.js           | 73 +++++++++++++++++++++++++++-------
desktop/main/stepbit-service.js        |  7 +++-
desktop/mcp-server.mjs                 | 53 +++++++++++++++++++-----
desktop/package-lock.json              | 42 -------------------
desktop/tests/snapshot-status.test.mjs |  2 +-
6 files changed, 108 insertions(+), 76 deletions(-)
```

Trace hashes recorded for this inventory:

- Dirty tracked diff hash: `64eca1a82eed1d2d30f493c538fc72d53df692cb`
- Untracked `desktop/shared/snapshot-status.mjs` SHA-256:
  `A6E2BE57FD438881175FE1AE78AE3ABFBABC8B3C94DF6F685D99C30A6801EFC3`

## Port Contract

The next port slice must not be treated as a normal feature migration. It is a
mechanical platform convergence port from the approved source snapshot into the
canonical repo.

Because the current source is not a committed PR/commit, #416 should not start
until one of these conditions is true:

1. the Ecosystem convergence delta is committed or opened as a source PR; or
2. the project explicitly accepts the local dirty snapshot above as the source
   of truth for the port.

## In Scope For The Mechanical Port

Candidate files from the Ecosystem convergence delta:

- `desktop/main/local-store-service.js`
- `desktop/main/register-ipc.js`
- `desktop/main/stepbit-service.js`
- `desktop/mcp-server.mjs`
- `desktop/tests/snapshot-status.test.mjs`
- `desktop/shared/snapshot-status.mjs`

Allowed intent:

- converge desktop shell IPC/snapshot behavior
- preserve canonical repo branding and product decisions
- apply only mechanical path/script adaptations required by canonical layout
- keep the full convergence DoD as the target

## Explicitly Out Of Scope

- #409 run-detail/native surface migration
- #410 paper ops/system/experiments migration
- `desktop/renderer/**` product surface work
- Assistant, Stepbit, or Pulse product decisions
- UX/branding changes not required by the platform port
- broad dependency upgrades
- broad supply-chain remediation
- unrelated docs cleanup

## `desktop/package-lock.json` Provisional Policy

Canonical baseline state:

- `desktop/package-lock.json` exists in `origin/main`.
- SHA-256:
  `6E9E4F42A50BFCC00A2FDC5DFFC55D1EEFDF38B352ECC6F812D56F1C9615CF10`

Ecosystem dirty state includes changes to `desktop/package-lock.json`, but this
inventory does not classify them as safe to port automatically.

Provisional decision:

- do not include `desktop/package-lock.json` in #416 unless it is unavoidable
  for the mechanical port to build or run;
- if it changes, the PR must explain why it was unavoidable;
- otherwise resolve the lockfile policy explicitly in #417.

## Validation Performed For This Inventory

- canonical repo resolved: `Whiteks1/quantlab`
- canonical base commit recorded: `790c629f9f8d16491465f384a665cd28096ea6a3`
- primary canonical checkout dirty state recorded and not touched
- fresh worktree created from `origin/main`
- Ecosystem source branch and dirty source snapshot recorded
- in-scope and out-of-scope boundaries defined
- `desktop/package-lock.json` provisional policy recorded

## Next Slice

Next issue: #416

Do not start #416 until the source snapshot ambiguity above is accepted or
resolved with a committed source PR/commit.
