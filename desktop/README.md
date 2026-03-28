# QuantLab Desktop

This directory contains the first desktop shell for QuantLab.

Current scope:

- Electron-based shell
- auto-starts `research_ui/server.py`
- desktop sidebar
- chat-centered command bus
- local decision store for candidates, shortlist, and baseline
- context tabs that combine embedded `research_ui` surfaces with shell-native run workspace, compare, artifacts, candidates, paper ops, and launch review tabs
- runtime strip for QuantLab and Stepbit visibility

This is intentionally a first block, not the final product shell.

## Start

From the repository root:

```powershell
cd desktop
npm install
npm start
```

## Current Tabs

- Chat
- Launch
- Runs
- Candidates
- Compare
- Paper Ops

## Notes

- The chat is deterministic and specialized for QuantLab commands.
- It does not yet delegate real reasoning to Stepbit.
- The shell reuses the existing `research_ui` as an embedded workspace surface.
- The renderer is now split into focused ES modules under `desktop/renderer/modules/` so workflow logic, decision-store helpers, and tab renderers no longer live in one file.
- The shell can now review recent launch jobs and explain the latest failure from local stdout/stderr logs.
- The shell now persists decision state locally in `outputs/desktop/candidates_shortlist.json`.
- `Run`, `Compare`, `Artifacts`, `Candidates`, and `Paper Ops` are now shell-native tabs designed to support launch -> inspect -> compare -> decide continuity.
