# QuantLab Desktop

This directory contains the first desktop shell for QuantLab.

Current scope:

- Electron-based shell
- auto-starts `research_ui/server.py`
- desktop sidebar
- chat-centered command bus
- context tabs that combine embedded `research_ui` surfaces with shell-native compare, artifacts, and launch review tabs
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
- Compare
- Paper Ops

## Notes

- The chat is deterministic and specialized for QuantLab commands.
- It does not yet delegate real reasoning to Stepbit.
- The shell reuses the existing `research_ui` as an embedded workspace surface.
- The shell can now review recent launch jobs and explain the latest failure from local stdout/stderr logs.
