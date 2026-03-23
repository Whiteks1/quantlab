---
description: How to review a completed stage in QuantLab
---

# Review Stage Workflow

Use this workflow when a stage or approved task is considered complete and needs final verification before closure.

## Purpose
This workflow ensures that a stage is reviewed consistently, that required artifacts are present and correct, and that closure only happens after validation against the original task requirements.

## Review Steps
1. Verify that all required artifacts for the stage are present under `outputs/`, if applicable.
2. Review `outputs/report.md` and `outputs/report.json` for correctness, consistency, and completeness.
3. Review test results and confirm that relevant checks pass.
4. Compare the implemented outcome against the original technical requirements defined in the active task file.
5. Identify any missing items, deviations, or unresolved issues.
6. Summarize the review outcome clearly.
7. Request explicit user sign-off before considering the stage closed.

## Validation Criteria
During review, confirm that:

- the implementation matches the approved scope
- required artifacts exist and are readable
- Markdown and JSON reporting remain aligned
- tests relevant to the stage pass
- no known issue blocks stage closure
- the outcome is consistent with the task definition

## If Problems Are Found
If the review detects missing artifacts, incorrect outputs, failing tests, or scope deviations:

- do not mark the stage as closed
- describe the issue clearly
- identify what still needs to be fixed
- recommend the next corrective step

## Expected Output Format
Codex should return the following sections:

1. **Artifacts Check**  
   Which expected outputs are present or missing.

2. **Report Validation**  
   Whether `report.md` and `report.json` are correct and aligned.

3. **Test Status**  
   Which tests were reviewed or executed, and whether they passed.

4. **Requirements Match**  
   Whether the implementation satisfies the task file requirements.

5. **Open Issues**  
   Any remaining problems, deviations, or risks.

6. **Stage Recommendation**  
   One of:
   - ready for sign-off
   - needs fixes before sign-off

## Guiding Principle
A stage is not closed because work was attempted. A stage is closed only when outputs, tests, and requirements all align.
