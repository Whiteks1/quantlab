# QuantLab Desktop

This directory contains the first desktop shell for QuantLab.

Current scope:

- Electron-based shell
- auto-starts `research_ui/server.py`
- desktop sidebar
- chat-centered command bus
- context tabs that embed `research_ui`
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
