# QuantLab Agent Guide

This repository uses explicit project context under `.agents/` and `.cursor/rules/`.
Read those files before making changes.
If Cursor is available, also honor `.cursor/mcp.json` and use the project MCP tools for validation before improvising ad hoc commands.

For public web work, also read:

- `docs/brand-guidelines.md`
- `docs/landing-governance.md`
- `landing/AGENTS.md`

## Working Rules

- Keep changes small and scoped to the requested task.
- Do not edit unrelated files.
- Do not create parallel implementations for the same concept.
- Treat existing docs, content files, and contracts as the source of truth before adding new ones.
- Default workflow is issue -> branch -> PR -> merge.
- One branch should carry one technical story with one clear dominant scope.
- Do not start branch work without an issue unless the task is an urgent fix and the user explicitly says to skip it.
- Multi-scope PRs that mix core, desktop, docs, CI, or auxiliary cleanup are not accepted by default; they require explicit written justification in the PR.
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
- If a change replaces an existing surface, remove the old surface instead of leaving both versions side by side.
- Do not introduce alternate package managers or lockfiles without explicit approval.
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

## Desktop Non-Negotiables (Agent Policy)

These rules are mandatory for any change under `desktop/`.

- Keep IPC hardening in place for request paths:
  - Normalize and validate `relativePath` (no absolute URLs, must start with `/`).
  - Require local token protection (`X-QuantLab-Token`) for sensitive POST routes.
  - Do not remove these guards without an explicit ADR.
- Never ship hardcoded default API keys or credentials in desktop runtime code.
  - Environment variables may be optional for local endpoints, but secrets must be required when used for auth.
- Desktop smoke must represent the real operator happy path.
  - `smoke:fallback` and `smoke:real-path` must both pass before merge.
  - Do not keep legacy-only selectors/assertions when UI structure has migrated.
- Keep test imports aligned with current code layout.
  - If a module is migrated or removed, update tests in the same PR.
  - A broken test import path is treated as a blocking regression.
- Treat filesystem boundaries as security boundaries.
  - Use canonical path checks (`realpath`) for repo/workspace guards.
  - `resolve + relative` alone is not sufficient when symlinks are possible.
- Do not log sensitive IPC payloads or raw responses.
  - Avoid full request bodies, tokens, prompts, or raw response excerpts in logs.
  - Keep logs minimal and operational.
- If a PR only has minor merge conflicts in CI/workflow files, resolve and merge quickly.
  - If failing checks indicate behavioral regressions (for example smoke happy-path failures), fix before merge.

## Before Implementing

1. Read `.agents/project-brief.md`.
2. Read `.agents/implementation-rules.md`.
3. Read `.agents/current-state.md`.
4. Inspect `.cursor/rules/` and `.cursor/mcp.json` when working in this repo.
5. Inspect the exact files involved in the task.
6. Confirm existing behavior before changing it.
7. For repo-level Codex guidance, use `.agents/prompts/quantlab-agent-definitive.md`.
8. For public landing work, also read `docs/landing-governance.md` and `landing/AGENTS.md`.
9. Search for duplicate copy, duplicate surfaces, and duplicate contracts before writing new ones.

## Quality Bar

- Use type hints for new Python code.
- Avoid side effects on import.
- Keep documentation aligned with observable behavior.
- Do not introduce secrets or environment-specific data into version control.

## Agent Coordination

- If multiple agents or workers are active, assign disjoint file ownership.
- Do not edit the same file from parallel tasks unless the task explicitly requires it.
- Reuse the existing source of truth instead of introducing a second version of the same data or copy.
- Tie branch names, PRs, and commits back to the originating issue when one exists.
- Summaries should name the files changed and note whether anything was removed or replaced.

## Validation

- Run the smallest relevant validation first.
- For code changes, prefer `pytest` or the repo MCP checks that cover the touched surface.
- For public web changes, verify build and the documented deploy path.
