# QuantLab Agent Guide

This repository uses explicit project context under `.agents/` and `.cursor/rules/`.
Read those files before making changes.
If Cursor is available, also honor `.cursor/mcp.json` and use the project MCP tools for validation before improvising ad hoc commands.

## Working Rules

- Keep changes small and scoped to the requested task.
- Do not edit unrelated files.
- Preserve the repository architecture:
  - core logic in `src/quantlab/`
  - CLI routing in `src/quantlab/cli/`
  - desktop shell work in `desktop/`
  - public docs in `docs/`
  - public landing surface in `landing/`
  - generated artifacts in `outputs/`
- Keep `main.py` limited to compatibility/bootstrap behavior.
- Prefer reversible changes over broad refactors.
- Add or update `pytest` coverage when behavior changes.
- Treat broker and execution changes as safety-sensitive.
- Preserve deterministic behavior and artifact contracts unless the task explicitly changes them.
- Prefer the repo MCP tools for routine validation:
  - `quantlab_check`
  - `quantlab_version`
  - `quantlab_runs_list`
  - `quantlab_paper_sessions_health`
  - `quantlab_desktop_smoke`
- For public web work, use these references:
  - `docs/brand-guidelines.md`
  - `docs/landing-governance.md`
  - `landing/AGENTS.md`

## Before Implementing

1. Read `.agents/project-brief.md`.
2. Read `.agents/implementation-rules.md`.
3. Read `.agents/current-state.md`.
4. Inspect `.cursor/rules/` and `.cursor/mcp.json` when working in this repo.
5. Inspect the exact files involved in the task.
6. Confirm existing behavior before changing it.
7. For repo-level Codex guidance, use `.agents/prompts/quantlab-agent-definitive.md`.
8. For public landing work, also read `docs/landing-governance.md` and `landing/AGENTS.md`.

## Quality Bar

- Use type hints for new Python code.
- Avoid side effects on import.
- Keep documentation aligned with observable behavior.
- Do not introduce secrets or environment-specific data into version control.
