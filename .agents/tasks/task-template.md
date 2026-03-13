# Issue #<NUMBER> — <TITLE>

## Goal
Describe the concrete objective of this task.

What should exist or be true after this work is finished?

Example:
Ensure that main.py only parses arguments and routes commands,
while command logic lives inside src/quantlab/cli/.

---

## Why this matters
Explain briefly why this task matters for QuantLab.

Examples:
- improves architecture clarity
- preserves modular CLI design
- ensures reproducibility of research runs
- prepares next stage of development

Keep this short.

---

## Scope

### In scope
List what is allowed to change.

Example:
- verify CLI modules
- inspect main.py
- confirm behavior consistency
- propose cleanup if necessary

### Out of scope
Things this task must NOT do.

Example:
- redesign CLI
- add new features
- modify artifact contracts

---

## Relevant files

List the files or directories likely involved.

Example:

- main.py
- src/quantlab/cli/
- .agents/current-state.md
- .agents/architecture.md

---

## Expected deliverable

Describe what this task should produce.

Examples:

- verification report
- design proposal
- minimal code refactor
- documentation update

---

## Done when

Clear criteria for completion.

Examples:

- pytest passes
- main.py contains no command logic
- CLI modules confirmed complete
- documentation updated

---

## Notes (optional)

Extra context if needed.

Example:
QuantLab uses a simplified GitHub workflow:

1 issue = 1 branch = 1 pull request

Pull requests should reference the issue using:

Closes #<NUMBER>