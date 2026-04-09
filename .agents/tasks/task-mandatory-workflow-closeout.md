# Task — Mandatory Workflow Closeout

## Goal
Make the repository workflow documents explicit about the default closeout path for real code changes.

## Scope

### In scope
- `.agents/workflow.md`
- `docs/workflow-operativo-codex.md`
- `.agents/session-log.md`

### Out of scope
- runtime code
- desktop code
- core Python
- CI changes

## Expected outcome

Both workflow documents must state that a real diff should normally proceed through:
- issue
- dedicated branch
- focused checks
- coherent commit
- PR
- merge
- issue closure
- local and remote branch cleanup

Exceptions must be explicit:
- user asks to stop earlier
- permissions or repository state block the next step
