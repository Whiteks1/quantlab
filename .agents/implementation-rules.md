# Implementation Rules - QuantLab

## General Principles
- Follow a **layered architecture**: `data -> indicators -> strategies -> backtest -> execution -> reporting`.
- Keep `main.py` limited to **CLI orchestration only**. Business logic must not live there.
- Prefer **pure functions** for analytics, metrics, and transformation logic whenever possible.
- Use **type hints** for new code and follow **PEP 8** style conventions.
- Favor **small, reversible changes** over broad refactors.

## Architectural Discipline
- Keep responsibilities clearly separated across modules.
- Do not mix strategy logic, portfolio logic, execution logic, and reporting concerns in the same implementation layer.
- New functionality should fit into the existing architecture rather than bypassing it.
- Avoid premature infrastructure complexity unless it clearly improves research quality or maintainability.

## Data and State Management
- All session outputs must be written under the `outputs/` directory.
- Avoid side effects during module import.
- Seed randomness whenever stochastic behavior is used, so backtests and research runs remain deterministic.
- Prefer explicit configuration over hidden defaults when behavior affects reproducibility.

## Testing and Quality
- Any new metric, portfolio rule, or core logic change **must** include unit tests using `pytest`.
- Handle edge cases explicitly, including:
  - empty datasets
  - missing values where applicable
  - non-standard trade sequences
  - zero-trade scenarios
  - no-op or resume cases
- Public functions and modules should include clear docstrings.
- Changes that alter contracts or behavior should be validated against existing tests before being considered complete.

## Reporting and Artifacts
- Reporting outputs in Markdown, JSON, CSV, and charts should remain consistent with one another whenever they describe the same run or experiment.
- Do not silently change reporting schemas or field meanings.
- Artifact naming should remain stable and predictable across runs.

## Trading Safety
- **Paper mode only** by default.
- Never commit secrets, API keys, credentials, or sensitive environment-specific data.
- Any future live execution capability must remain opt-in, explicit, and outside the default development path.

## Workflow Expectations
- Read the relevant `.agents` workflow and state files before implementing changes.
- Work in a **dedicated branch** for each significant task.
- Do not stage unrelated files.
- Do not use broad staging commands such as `git add .` when task scope is limited.
- Before committing, verify that only intended files are staged.
- Leave a clear summary of what changed, what was tested, and what remains pending.

## Scope Control for Antigravity
- Only modify the files explicitly required for the approved task.
- Do not create alternative paths, duplicated nested folders, or inferred file locations.
- If a target path is ambiguous, stop and report the ambiguity instead of guessing.
- If unrelated modified or untracked files are present, leave them untouched unless explicitly instructed otherwise.

## Guiding Rule
- QuantLab must remain a **research-first system**: prioritize correctness, reproducibility, and clarity over speed, convenience, or premature platform expansion.