# Stage M.4 - Portfolio Mode Comparison

## Status
Planned

## Objective
Add a comparison layer for portfolio aggregation modes so QuantLab can compare portfolio behavior under different allocation policies over the same eligible session universe.

## Why This Stage Matters
Stage M.2 introduced allocation modes:
- `raw_capital`
- `equal_weight`
- `custom_weight`

Stage M.3 introduced selection rules that define which sessions are eligible.

The next logical step is to compare how portfolio results change when the same selected universe is aggregated under different allocation modes.

## Scope

### In Scope
- Compare portfolio outputs for:
  - `raw_capital`
  - `equal_weight`
  - `custom_weight`
- Reuse the same post-selection session universe for fair comparison
- Produce a machine-readable comparison payload
- Produce a human-readable Markdown comparison report
- Include side-by-side summary metrics for each mode

### Out of Scope
- External market benchmark comparison
- Portfolio optimization algorithms
- Live portfolio rebalancing logic
- Risk parity / optimizer-based weighting

## Expected Deliverables
- Comparison report for portfolio modes
- JSON payload with one block per allocation mode
- Markdown report with side-by-side comparison table
- Deterministic comparison behavior
- Regression-safe tests

## Relevant Files
- `main.py`
- `src/quantlab/reporting/portfolio_report.py`
- `src/quantlab/reporting/portfolio_mode_compare.py` (expected new file or equivalent)
- `test/test_portfolio_report.py`
- `test/test_portfolio_allocation.py`
- `test/test_portfolio_mode_compare.py` (expected new file)

## Acceptance Criteria
- The same filtered session universe is used for each compared allocation mode
- Comparison report includes, at minimum:
  - starting value
  - ending value
  - total pnl
  - total return
  - max drawdown
  - aggregate bars
- JSON and Markdown remain aligned
- Full pytest passes
- Stage-specific tests pass
- Existing `--portfolio-report` behavior remains unchanged

## Suggested CLI Shape
Possible new command:
- `--portfolio-compare ROOT_DIR`

Optional behavior:
- reuse all existing selection flags from M.3
- allow a custom weights file when `custom_weight` is part of the comparison set

## Verification Checklist
- [ ] Full `pytest` passes
- [ ] Mode comparison tests pass
- [ ] Same selected session set is reused across compared modes
- [ ] Markdown comparison table renders clearly
- [ ] JSON comparison payload is complete and aligned with Markdown
- [ ] Existing `--portfolio-report` behavior unchanged

## Next Recommended Step
Design the comparison payload shape first, then implement the internal comparison function before wiring CLI or rendering.