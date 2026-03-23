---
description: How to read context and plan the next step in QuantLab
---

# Read and Plan Workflow

Use this workflow at the **start of every Codex session** before making any implementation changes.

## Purpose
This workflow ensures that each session begins with the correct project context, follows the current roadmap and workflow rules, and avoids unnecessary or out-of-scope changes.

## Files to Read First
Read these files in order:

1. `.agents/project-brief.md`
2. `.agents/implementation-rules.md`
3. `.agents/current-state.md`
4. `.agents/session-log.md`
5. The active task file inside `.agents/tasks/`

## Required Behavior
Before implementing anything, Codex must:

- treat these files as the **source of truth** for the session
- identify the active task and summarize it in its own words
- distinguish between:
  - what is already implemented in the repository
  - what still needs to be built or changed
- identify the exact files that are likely to change
- propose a step-by-step implementation plan
- identify risks, uncertainties, or edge cases
- remain within the approved task scope

## Constraints
During the read-and-plan phase, Codex must **not**:

- implement changes
- edit files
- create files
- stage files
- commit changes
- push changes
- infer extra tasks beyond the approved scope

If file paths, task scope, or requirements are ambiguous, Codex must stop and report the ambiguity instead of guessing.

## Approval Gate
After presenting the plan, Codex must **wait for explicit approval** before proceeding to execution when:

- the user requested a plan-only response
- the requested change has non-obvious consequences
- the task scope is still ambiguous

If the user has already explicitly approved implementation and the task is clear, Codex may proceed after this read-and-plan pass.

## Expected Output Format
Codex should return the following sections:

1. **Task Understanding**  
   A concise summary of the active task in its own words.

2. **Repository State vs Missing Work**  
   Clearly separate:
   - what already exists in the repository
   - what still needs to be implemented

3. **Files Likely to Change**  
   List only the files that are expected to be modified or created.

4. **Implementation Plan**  
   Provide a step-by-step plan for the approved task.

5. **Risks / Edge Cases**  
   List any notable risks, edge cases, or possible blockers.

6. **First Recommended Step**  
   Suggest only the first execution step, without performing it.

## Guiding Principle
Read first. Plan second. Execute only after approval when approval is required.
