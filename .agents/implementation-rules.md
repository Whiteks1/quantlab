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
