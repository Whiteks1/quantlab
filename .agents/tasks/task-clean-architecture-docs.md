

# Task: Clean architecture notes and documentation changes

## Goal
Review the documentation and architecture notes modified during the CLI refactor and decide what should be kept, moved, rewritten, or discarded.

## Why
After refactors, documentation often becomes partially correct but structurally messy. QuantLab needs a coherent internal architecture record before adding more layers of work.

## Scope
- inspect architecture-related docs changed during the refactor
- decide which changes should remain
- identify outdated notes
- normalize docs so they reflect the current repo structure
- reduce duplication where possible

## Non-goals
- writing a full product spec
- adding integration docs for Stepbit yet
- redesigning the entire documentation system

## Inputs
- architecture notes
- refactor-touched docs
- current CLI structure
- issue #13 or equivalent

## Expected outputs
- cleaned architecture/documentation set
- explicit keep/move/discard decisions
- reduced duplication
- docs aligned with current repo reality

## Acceptance criteria
- modified docs are reviewed one by one
- outdated or misleading notes are removed or corrected
- architecture docs reflect the current CLI structure accurately
- no major refactor-era ambiguity remains in the docs

## Constraints
- keep changes tightly scoped to refactor fallout
- do not turn this into an endless docs cleanup
- prioritize clarity over documentation volume

## GitHub issue
- #13 Clean architecture notes and documentation changes

## Suggested next step
List the documentation files touched by the refactor and classify each one as keep, rewrite, move, or discard.