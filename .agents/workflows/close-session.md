---
description: How to close a session properly in QuantLab
---

# Close Session Workflow

Use this workflow at the end of a Codex session after implementation and verification are complete.

## Purpose
This workflow ensures that each session ends with clear project continuity, updated project state, and a documented summary of what was done.

## Close Session Steps
1. Ensure that all code changes relevant to the session have been verified by appropriate tests.
2. Update `.agents/current-state.md` to reflect the latest confirmed project status.
3. Add a concise session summary to `.agents/session-log.md`.
4. List any clear **Next Steps** for the user or for the next execution session.
5. Create a `walkthrough.md` artifact only if the session introduced a significant feature, workflow change, or implementation that would benefit from a guided explanation.
6. Do not commit or push unless the task explicitly includes those actions.

## Session Log Requirements
When updating `.agents/session-log.md`, include:

- session focus
- tasks completed
- key decisions
- next steps

The summary should be concise but sufficient to preserve continuity for the next session.

## Current State Requirements
When updating `.agents/current-state.md`, ensure that:

- the active stage is correct
- the latest completed or in-progress work is accurately reflected
- outdated status information is removed or updated
- the file remains aligned with the roadmap and task progression

## Walkthrough Guidance
Create a `walkthrough.md` artifact only when it adds real value, for example:

- a new feature with non-obvious usage
- a workflow that the user may need to repeat
- a stage closure with meaningful outputs or validation steps

Do not create walkthrough files for minor edits or routine documentation changes.

## Constraints
During session closure, Codex must not:

- introduce new implementation work
- expand scope beyond the completed session
- create unnecessary artifacts
- guess final status if verification is incomplete

If verification is incomplete, the session should be closed with a clear note that follow-up work is still required.

## Expected Output Format
Codex should provide:

1. **Session Summary**  
   What was completed in this session.

2. **Files Updated**  
   Which project memory or documentation files were updated.

3. **Verification Status**  
   What was tested or verified.

4. **Next Steps**  
   What should happen next.

5. **Walkthrough Created**  
   Whether a walkthrough artifact was created, and why.

## Guiding Principle
Close the session in a way that makes the next session easier, clearer, and safer to continue.
