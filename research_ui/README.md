# QuantLab Research Dashboard - Local Preview

This directory contains a strictly read-only, tangible UI layer for QuantLab research results.

## Phase 1.5: Research Registry + Paper Ops Pulse
This version supports:
- Automatic synchronization with `outputs/runs/runs_index.json`.
- Paper-session health visibility from `outputs/paper_sessions/` through the local preview server.
- Sortable table by any metric column.
- Real-time search by ticker or run ID.
- Mode filtering (Run, Sweep, Forward).
- Read-only operator pulse for `Stage C.1 - Paper Trading Operationalization`.

## How to Run (Local Preview)

1. **Open a terminal** in the QuantLab project root.
2. **Execute the dev server**:
   ```bash
   python research_ui/server.py
   ```
3. **Open your browser** to:
   [http://localhost:8000](http://localhost:8000)

## Constraints & Architecture
- **Read-Only**: This dashboard cannot execute runs or modify data.
- **Low Coupling**: It reads standard JSON artifacts from the `outputs/` directory and a tiny local health endpoint for paper sessions.
- **No Dependencies**: Built with Vanilla JS/CSS for maximum stability and zero-install preview.

---
*Note: Run Detail views and side-by-side comparison are planned for Phase 2.*
