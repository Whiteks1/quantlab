# QuantLab Control Surface - Local Preview

This directory contains a strictly read-only, tangible UI layer for the QuantLab system as it is actually evolving.

## Current Surface
This version supports:
- Automatic synchronization with `outputs/runs/runs_index.json`.
- Paper-session health visibility from `outputs/paper_sessions/` through the local preview server.
- Broker order-validation and submission health visibility from `outputs/broker_order_validations/` when present.
- Hyperliquid surface visibility for read-only preflight, account readiness, and signed-action build progress.
- Stepbit workspace boundary visibility when local `stepbit-app` and `stepbit-core` repos are present beside `quant_lab`.
- Sortable table by any metric column.
- Real-time search by ticker or run ID.
- Mode filtering (Run, Sweep, Forward).
- Read-only operator pulse for the current bridge from paper operations into supervised execution safety.

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
- **Low Coupling**: It reads standard JSON artifacts from the `outputs/` directory plus a few tiny local summary endpoints for paper, broker, Hyperliquid, and Stepbit workspace state.
- **No Dependencies**: Built with Vanilla JS/CSS for maximum stability and zero-install preview.
- **Honest Boundary Model**: Stepbit is shown as an external connected workspace surface, not as an in-process QuantLab runtime.

---
*Note: The UI stays intentionally read-only even as broker and venue work becomes more operational.*
