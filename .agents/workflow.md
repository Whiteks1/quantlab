# Project Workflow — QuantLab

This document defines the internal execution complement to the public workflow.

The public operating guide now lives in:

- `docs/workflow-operativo-codex.md`

Use this file to keep agent behavior aligned with that public guide without duplicating its full contents.

## 1. Branching Strategy

QuantLab follows a strict **Issue-Branch-PR** workflow:

1. **Issue**: Every task or bug should be represented by a GitHub Issue.
2. **Branch**: Create a dedicated branch for each issue.
3. **Pull Request**: All changes should be integrated via PR. Direct commits to `main` should be avoided.

Codex-created branches should use the `codex/` prefix.

---

## 2. Agent Collaboration Model

When working with Codex or another execution-focused AI assistant, follow this protocol:

### /read-and-plan
When starting a new issue or session:
- Confirm the task category and the correct repository before changing files.
- Read the relevant `.agents/` context files.
- Read the task file in scope.
- Propose a scoped implementation or cleanup plan, including touched files, assumptions, and non-obvious risks for substantial work.
- Wait for user approval when the request is plan-only, when scope is ambiguous, or when the change has non-obvious consequences.

If the user has already approved execution and the scope is clear, Codex may proceed after reading the required context.

### /execute-task
During implementation:
- Execute one well-defined step at a time.
- Keep changes tightly scoped to the approved task.
- Prioritize broken public surface first, then internal state, then public contract and docs.
- Log relevant continuity in `.agents/session-log.md` when appropriate.

### /close-session
When finishing work:
- Summarize what was completed.
- Note any important continuity for the next session.
- Leave the branch in a reviewable state for PR preparation.

---

## 3. Task Management (`.agents/tasks/`)

Active work is tracked in task files under `.agents/tasks/`.

- **Purpose**: Maintain a persistent record of the current objective and sub-tasks.
- **Use**: Tasks help preserve continuity across sessions and keep implementation aligned with issue scope.

---

## 4. Documentation First

- Public workflow and repository-facing guidance should live in `docs/`.
- Architecture changes must be reflected in `.agents/architecture.md`.
- File placement rules must be reflected in `.agents/code-map.md`.
- Artifact or output contract changes must be reflected in `.agents/artifact-contracts.md`.
- Codex-specific operating guidance belongs in `.agents/prompts/codex-master-prompt.md`.

---

## 5. Workflow Rule

Before changing files, confirm:
- why those files are the correct place for the change
- that the task scope is still respected
- that unrelated files remain untouched
- that stray files are not being pulled into the change without an explicit decision
