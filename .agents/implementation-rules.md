# Implementation Rules - QuantLab

## General Principles
- Follow **layered architecture**: data -> indicators -> strategies -> backtest -> execution -> reporting.
- Logic is strictly prohibited in `main.py` (CLI orchestration only).
- Prefer **pure functions** for analytics and metric calculations.
- Use **type hints** and **PEP8** standards for all new code.

## Data & State
- All session outputs must go to the `outputs/` directory.
- Avoid side effects on import.
- Seed randomness to ensure deterministic behavior in backtests.

## Testing & Quality
- New metrics or core logic MUST include unit tests using `pytest`.
- Handle edge cases: empty datasets, non-standard trade sequences, etc.
- Documentation (docstrings) is required for all public functions/modules.

## Trading Safety
- **Paper mode only** by default.
- Never commit secrets or API keys.

## Safe Change Protocol

Before implementing any code change, the execution agent must follow this protocol.

### Step 1 — Inspect
Identify the exact files involved in the task.

Do not modify files outside this set unless explicitly required.

### Step 2 — Verify existing behavior
Confirm whether the requested functionality already exists in the repository.

Do not implement duplicate logic.

### Step 3 — Minimal change
Prefer the smallest change that satisfies the task.

Avoid architectural changes unless the task explicitly requires them.

### Step 4 — Preserve architecture boundaries

Do not move business logic into main.py.

Command routing belongs in:
src/quantlab/cli/

Core logic belongs in:
src/quantlab/

### Step 5 — Validate tests

After implementing a change, ensure:

pytest passes.

If tests fail, identify whether:
- behavior changed unintentionally
- tests require adjustment

### Step 6 — Document impact

If the change affects:

- artifact contracts
- CLI behavior
- reporting outputs
- forward evaluation

note this explicitly in the PR summary.

### No hidden side effects

Do not introduce behavior changes unless explicitly requested.

Refactors should preserve observable behavior.

Antigravity must inspect the repository before implementing changes.

---

## GitHub

GitHub is the **task and state manager**.

Responsibilities:

- Issues represent tasks
- Project board represents workflow state
- Branches implement work
- Pull requests integrate work

---

# Development workflow

QuantLab follows a simplified GitHub workflow:

1 issue = 1 branch = 1 pull request

Pull requests should reference the issue using:

Closes #<NUMBER>

## Session Log

All research sessions must be logged in:

.agents/session-log.md

Each entry must include:

- session ID
- timestamp
- command used
- key parameters
- relevant metrics
- links to outputs/

This log is the **source of truth** for run history.
