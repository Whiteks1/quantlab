

# Task: Review saved git stashes

## Goal
Inspect any saved stashes created during the CLI refactor period and decide explicitly whether each one should be applied, moved into a branch, or discarded.

## Why
Ambiguous stash state creates uncertainty, duplicate work, and accidental regression risk. QuantLab needs a clean working baseline before internal stabilization or Stepbit integration proceeds.

## Scope
- inspect existing git stashes
- identify what changes each stash contains
- classify each stash as keep/apply, move-to-branch, or discard
- document the decision clearly

## Non-goals
- broad refactoring
- new feature implementation
- Stepbit-side integration work

## Inputs
- current git stash list
- current CLI refactor state
- open internal issues related to CLI stabilization

## Expected outputs
- stash inventory with decisions
- any recovered work moved into the correct branch if needed
- discarded obsolete stash entries
- short written note of decisions

## Acceptance criteria
- every existing stash has an explicit decision
- no unknown stashes remain
- any valuable stash content is preserved safely
- obsolete stash content is removed intentionally

## Constraints
- do not merge unrelated stash content into a single task
- do not apply a stash blindly without reviewing its diff
- preserve clean issue-to-branch boundaries

## GitHub issue
- #10 Review saved git stashes

## Suggested next step
List all current stashes and inspect the diff of each one before deciding what survives.