# Stage M.3 - Portfolio Selection / Session Inclusion Rules

## Status
Planned

## Objective
Add a configurable selection layer before portfolio aggregation so the user can control which forward sessions are eligible for inclusion in the aggregated portfolio.

## Why This Stage Matters
Stage M.2 solved allocation, but not selection.

At the moment, the portfolio layer can:
- aggregate valid sessions
- deduplicate noisy/duplicate sessions
- apply allocation modes

But it still lacks an explicit inclusion layer.
That means the aggregated portfolio is still mostly driven by “everything valid on disk” instead of a deliberate research subset.

## Scope

### In Scope
- Top-N session selection
- Rank metric selection
- Minimum return filter
- Maximum drawdown filter
- Include/exclude by ticker
- Include/exclude by strategy
- Latest-per-source-run mode

### Out of Scope
- External benchmark comparison
- Portfolio optimization algorithms
- Strategy recommendation logic
- Live portfolio rebalancing

## Expected CLI Additions
- `--portfolio-top-n`
- `--portfolio-rank-metric`
- `--portfolio-min-return`
- `--portfolio-max-drawdown`
- `--portfolio-include-tickers`
- `--portfolio-exclude-tickers`
- `--portfolio-include-strategies`
- `--portfolio-exclude-strategies`
- `--portfolio-latest-per-source-run`

## Relevant Files
- `main.py`
- `src/quantlab/reporting/portfolio_report.py`
- `test/test_portfolio_report.py`
- `test/test_portfolio_hygiene.py`
- `test/test_portfolio_allocation.py`
- `test/test_portfolio_selection.py` (new)

## Acceptance Criteria
- Default portfolio behavior remains unchanged if no selection flags are passed
- Selection runs after hygiene/dedup and before allocation
- JSON report includes selection configuration and selection counters
- Markdown report includes a dedicated selection section
- Selection behavior is deterministic
- Full pytest passes
- Stage-specific tests pass

## Selection Pipeline Order
1. Scan sessions
2. Normalize metadata
3. Apply hygiene / incomplete-session filtering
4. Apply deduplication
5. Apply selection rules
6. Apply allocation mode
7. Build final aggregated portfolio report

## Verification Checklist
- [ ] Full `pytest` passes
- [ ] Stage-specific selection tests pass
- [ ] Default `--portfolio-report` still behaves as before
- [ ] Portfolio report includes selection section in Markdown
- [ ] Portfolio report includes selection block in JSON
- [ ] Filtering by ticker works
- [ ] Filtering by strategy works
- [ ] Top-N works
- [ ] Min return works
- [ ] Max drawdown works
- [ ] Latest-per-source-run works

## Next Recommended Step
Implement selection configuration parsing and the internal selection pipeline in `portfolio_report.py` before updating rendering or tests.