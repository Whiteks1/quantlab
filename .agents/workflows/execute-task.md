---
description: How to execute the next implementation step in QuantLab
---

# Execute Task Workflow

Use this workflow only **after the implementation plan has been approved**.

## Purpose
This workflow defines how Antigravity should execute an approved task in a controlled, traceable, and repository-safe way.

## Preconditions
Before execution begins, Antigravity must confirm that:

- the implementation plan has been explicitly approved
- the active task is clearly defined
- the expected file scope is known
- the relevant `.agents` files have already been read

## Execution Steps
1. Ensure the implementation plan has been approved.
2. Update `.agents/current-state.md` to reflect that the task is **In Progress**, if appropriate.
3. Implement the approved changes according to `.agents/implementation-rules.md`.
4. Add or update unit tests in `test/` when behavior, logic, or metrics are affected.
5. Run relevant tests regularly during implementation using `pytest`.
6. Keep the implementation strictly within the approved task scope.
7. Stage only the exact files related to the task.
8. Verify the staged diff before committing.
9. Commit changes with a clear, scoped commit message.
10. Push the branch after the task is complete.
11. Document relevant results, deviations, and continuity notes in `.agents/session-log.md`.

## Scope Rules
During execution, Antigravity must:

- modify only the files required by the approved task
- avoid unrelated changes
- avoid creating alternative or duplicated paths
- avoid touching untracked files unless explicitly required
- stop and report any ambiguity instead of guessing

## Git Rules
Antigravity must not use broad staging commands such as:

```bash
git add .