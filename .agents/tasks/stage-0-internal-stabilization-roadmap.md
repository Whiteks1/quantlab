# Task: Stage 0 internal stabilization roadmap

## Goal
Coordinate the internal QuantLab stabilization work that should be completed before Stepbit integration becomes a primary focus.

## Why
QuantLab is the primary system. Before expanding into external orchestration or cross-repository integration, the project needs internal clarity, architectural coherence, and a stable research-first workflow.

## Scope
This stage covers the remaining internal stabilization work around:
- architecture/documentation cleanup after CLI refactor
- defining the post-refactor roadmap
- clarifying the next role of runs.py in the CLI
- explicitly separating internal QuantLab priorities from later Stepbit integration work

## Non-goals
This stage does not include:
- Stepbit adapter implementation
- cross-repository E2E integration
- distributed sweep orchestration
- event/signals work
- external orchestration features as primary scope

## Inputs
- open GitHub issues:
  - #19 meta: backlog consolidado QuantLab ↔ Stepbit
  - #14 Define roadmap after CLI refactor
  - #13 Clean architecture notes and documentation changes
  - #12 Design next step for runs.py command interface
- completed internal prerequisites:
  - #10 Review saved git stashes
  - #11 Verify CLI modularization is complete
- current `.agents/` context files
- current repository structure and CLI state

## Expected outputs
- one Antigravity task file per active internal Stage 0 issue
- a clear execution order for the remaining internal work
- explicit acknowledgment that Stepbit integration is secondary to QuantLab’s core evolution
- a clean transition point from Stage 0 into later integration work

## Acceptance criteria
- Stage 0 is clearly documented as an internal QuantLab-first phase
- each remaining internal issue is mapped to a task file
- completed prerequisites are acknowledged and not duplicated unnecessarily
- the next executable internal task is obvious
- the separation between internal stabilization and later integration is explicit

## Constraints
- preserve QuantLab as a research-first, rigorous, auditable system
- prefer solidity over breadth
- do not let Stepbit integration overshadow internal architecture decisions
- do not mix Stage 0 work with later integration implementation
- keep the task system minimal, clear, and execution-oriented

## GitHub issues
- #19 meta: backlog consolidado QuantLab ↔ Stepbit
- #14 Define roadmap after CLI refactor
- #13 Clean architecture notes and documentation changes
- #12 Design next step for runs.py command interface

## Related completed prerequisites
- #10 Review saved git stashes
- #11 Verify CLI modularization is complete

## Planned child tasks
- `.agents/tasks/task-clean-architecture-docs.md`
- `.agents/tasks/task-define-post-cli-roadmap.md`
- `.agents/tasks/task-runs-cli-interface.md`

## Suggested next step
Execute `task-clean-architecture-docs.md` first if documentation/architecture fallout from the CLI refactor is still ambiguous; otherwise execute `task-define-post-cli-roadmap.md`.