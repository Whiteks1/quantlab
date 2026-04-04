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

Smoke check:

```powershell
cd desktop
npm run smoke
```

## Cursor MCP

This folder also exposes a local MCP server for Cursor via [`.cursor/mcp.json`](../.cursor/mcp.json).

Available tools:

- `quantlab_check`
- `quantlab_version`
- `quantlab_runs_list`
- `quantlab_paper_sessions_health`
- `quantlab_desktop_smoke`
- `quantlab_read_file`

The server entrypoint is `mcp-server.mjs`, and the `mcp` npm script runs it directly.

## Current Tabs

- Chat
- Experiments
- Launch
- Runs
- Candidates
- Compare
- Paper Ops

## Notes

- The chat is deterministic and specialized for QuantLab commands.
- The chat can now route explicit `ask stepbit ...` prompts through a Stepbit-backed adapter while keeping QuantLab as the primary shell and decision surface.
- The shell reuses the existing `research_ui` as an embedded workspace surface.
- The renderer is now split into focused ES modules under `desktop/renderer/modules/` so workflow logic, decision-store helpers, and tab renderers no longer live in one file.
- The shell can now review recent launch jobs and explain the latest failure from local stdout/stderr logs.
- The shell now persists decision state locally in `outputs/desktop/candidates_shortlist.json`.
- `Run`, `Compare`, `Artifacts`, `Candidates`, and `Paper Ops` are now shell-native tabs designed to support launch -> inspect -> compare -> decide continuity.
- `Experiments` is now a shell-native workspace for local sweep configs and recent sweep outputs under `configs/experiments` and `outputs/sweeps`.
- Sweep rows can now be tracked, shortlisted, baselined, and compared in a local handoff layer persisted in `outputs/desktop/sweep_decision_handoff.json`.
- The shell now restores lightweight workspace context from `outputs/desktop/workspace_state.json`, including tabs, active context, selected runs, and launch form inputs.
