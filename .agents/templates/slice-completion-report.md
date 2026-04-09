# QuantLab Slice Completion Report

Use this template after finishing one scoped slice in QuantLab.
Keep it factual, short, and tied to the actual repo boundary.

## Workflow Status

- Issue created: `[#<issue_number>](<issue_url>) <issue_title>` or `N/A`
- Branch created from `origin/main`: `<branch_name>` or `N/A`
- Push to remote: `done` / `not done` / `N/A`
- PR opened: `[#<pr_number>](<pr_url>)` or `N/A`
- PR merged into `main`: `done` / `not done` / `N/A`
- Issue closed: `done` / `not done` / `N/A`
- Merge commit on `main`: `<commit_sha> <commit_title>` or `N/A`

## Roadmap Stage

- Stage affected: `<roadmap stage or boundary>`
- Boundary preserved: `<core / cli / paper / broker / landing / docs / stepbit>`

## Exact Files Changed

- `<path/to/file>`
- `<path/to/file>`
- `<path/to/file>`

## Scope Statement

This slice does:

- <thing 1>
- <thing 2>

This slice does not:

- touch unrelated runtime
- mix docs, workflow, and core logic unless the slice explicitly requires it
- change generated artifacts by hand
- continue work on top of unrelated dirty changes

## Validation Run

Mark only the checks that were actually relevant to the slice.

- `git diff --check`
- `python -m pytest -q <test_path_or_suite>`
- `python main.py --check`
- `python main.py --version`
- `<repo CLI command>`
- `<landing/web command if landing changed>`

## Compact Summary

<2-5 lines explaining what changed, which contract or behavior was reinforced, and what was intentionally left alone.>

## Residual Limitations

- <limitation 1>
- <limitation 2>
- <limitation 3>

## Next Logical Slice

Open a new issue and a new branch only for:

- `<slice_name>`

Likely files:

- `<path/to/file>`
- `<path/to/file>`
- `<path/to/file>`

Likely validation:

- `git diff --check`
- `python -m pytest -q <test_path_or_suite>`
- `<repo CLI command>`

## Workflow Notes

- If the worktree is dirty, do not mix unrelated changes into the slice.
- Create the branch from `origin/main`.
- Keep the commit as small and atomic as possible.
- Prefer one issue and one PR per slice when the work goes through GitHub.
- If this slice only changed docs or governance, say so explicitly.
- If this slice touched landing/web, mention the landing governance doc and the public brand guide.

