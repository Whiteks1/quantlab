# Frontend Integration: QuantLab With Optional Stepbit UI

QuantLab can be surfaced through a Stepbit UI, but that UI should be treated as an optional external experience layer, not as QuantLab's sovereign control surface.

The main product authority still lives in QuantLab itself.

## 1. UI Integration Principle

If Stepbit presents QuantLab data visually, it should do so by consuming stable QuantLab artifacts and contracts.

That means:

- the UI reads QuantLab outputs
- the UI may trigger bounded QuantLab actions through documented interfaces
- the UI does not become the owner of QuantLab's internal lifecycle, risk policy, or strategy authority

## 2. Example Connection Model

The Stepbit interface may still use a frontend such as React + Vite and a backend gateway layer.

### Example data flow

1. **Artifact access**: a backend route exposes selected QuantLab outputs, reports, and machine-readable summaries.
2. **Frontend state**: the UI queries canonical run artifacts and run-history data.
3. **Visualization**: the UI renders charts, metrics, and comparisons based on QuantLab-owned outputs.

## 3. Good UI Responsibilities

- run explorer views
- artifact browsing
- comparison dashboards
- AI-assisted explanation panels
- paper-session monitoring support

## 4. Responsibilities The UI Should Not Own

- QuantLab session sovereignty
- trading-policy authority
- risk-policy ownership
- promotion of strategies into broker-connected operation
- replacing QuantLab's own core operating model

## 5. Practical Implementation Direction

If this integration is pursued, the clean approach is:

1. expose stable QuantLab artifacts and machine-facing reports
2. consume them from Stepbit through a narrow API or MCP boundary
3. keep execution, risk, and product authority inside QuantLab

## 6. Strategic Benefit

This approach preserves the best of both systems:

- QuantLab remains an autonomous research and trading system
- Stepbit can offer a better external UI and AI-assisted workflow experience
- the integration remains reversible rather than structurally invasive
