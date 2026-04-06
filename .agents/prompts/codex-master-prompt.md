You are Codex working directly inside the QuantLab repository.

Treat `.agents/` as repository context and operating guidance, not as product runtime code.

Before making changes, read and treat these files as source of truth for the task:

- `AGENTS.md`
- `.agents/project-brief.md`
- `.agents/architecture.md`
- `.agents/code-map.md`
- `.agents/artifact-contracts.md`
- `.agents/current-state.md`
- `.agents/implementation-rules.md`
- `.agents/workflow.md`
- `.agents/session-log.md`
- `.agents/cursor-codex-cheatsheet.md`
- `docs/quant-pulse-quantlab-contract.md` when the task involves upstream signal intake or cross-repo boundary rules

If the task is stage-specific or issue-specific, also read the relevant file in:

- `.agents/tasks/`

## Operating constraints

- Keep changes small, reversible, and reviewable.
- Preserve repository architecture and artifact contracts unless the task explicitly changes them.
- Keep `main.py` thin and CLI/bootstrap-only.
- Prefer read-only inspection and validation for tooling tasks.
- Do not widen scope into adjacent broker, execution, UI, or signal-intake surfaces unless the task explicitly requires it.
- Use a dedicated `codex/<short-topic>` branch from up-to-date `main` when implementation is needed.
- Treat Quant Pulse intake as upstream and subordinate to QuantLab-owned decisions: only signals that improve research, validation, risk control, or product priorities should influence this repo.

## Current QuantLab priorities to respect

- Hyperliquid-first supervised safety is the active execution focus.
- Read-only artifact/output visibility is preferred over new execution surface.
- Desktop and MCP work should inspect and summarize, not add trading logic.
- Paper/session visibility matters as a bridge, not as the current bottleneck.
- Quant Pulse intake is valid only when it can be expressed as a testable research hypothesis, a risk filter, or a product/instrumentation priority.

## Two-phase workflow

### Phase 1 - Plan

Before editing, produce:

1. Goal
2. Exact files to change
3. What must not change
4. Minimal plan
5. Validation commands to run after edits
6. Suggested PR title and a short 4-line body template

Rules:

- no edits in the plan response
- no unrelated files
- no scope expansion
- preserve backward compatibility unless explicitly requested otherwise
- if scope, files, or behavior are ambiguous, stop and report the ambiguity

### Phase 2 - Execute

After approval, or when the user has already explicitly approved implementation and scope is clear:

1. Change only the approved files
2. Keep the change narrowly scoped
3. Add or update focused tests when behavior changes
4. Run the validation commands from the approved plan
5. Stage only the exact files for the task
6. Verify the staged diff before committing
7. Commit with a clear, scoped message
8. Push the branch if the task is complete
9. Report the result briefly and clearly

Rules:

- no unrelated cleanup
- no hidden refactors
- no duplicate implementation paths
- no ad hoc scope creep

## Validation matrix

Choose validation based on the touched area:

- `docs/` or `.agents/` markdown only:
  - `git diff --check`
  - human read-through
- `desktop/` or `*.mjs` MCP work:
  - `node --check <file>`
  - `git diff --check`
- `src/quantlab/` or tests:
  - focused `pytest`
  - `python main.py --check` when CLI/runtime behavior is touched
  - `git diff --check`
- `docs/quant-pulse-quantlab-contract.md` or other intake-boundary docs:
  - `git diff --check`
  - verify the wording matches the actual repo boundary and current roadmap

Prefer the repository MCP tools for routine validation when they apply:

- `quantlab_check`
- `quantlab_version`
- `quantlab_runs_list`
- `quantlab_paper_sessions_health`
- `quantlab_desktop_smoke`

## PR shape

Keep PRs short and structured:

- Summary
- Scope
- Validation
- Notes

The body should state:

- what changed
- which files changed
- how it was validated
- the compatibility or risk note

## Response shape

When planning:

1. current understanding
2. task in scope
3. what already exists
4. exact gap
5. minimal plan
6. risks or things to avoid
7. next logical step only

When finishing implementation:

1. files changed
2. what changed
3. tests run
4. results
5. deferred items
