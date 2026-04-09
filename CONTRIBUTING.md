# Contributing to QuantLab

QuantLab works best with small, self-contained slices.

The preferred workflow is:

1. open or reuse one clear issue
2. choose one clear slice
3. work locally first
4. commit in a small battery of logical commits
5. push once the slice is coherent
6. open one focused PR linked to the issue
7. merge
8. let the branch be deleted after merge

## Recommended Slice Shape

Prefer one narrow intention per branch, for example:

- one broker lifecycle step
- one CLI consolidation step
- one UI slice
- one documentation alignment step

Rule of thumb:

- one branch = one technical story
- one PR = one dominant scope
- if a PR mixes core, desktop, docs, CI, or cleanup, that mix must be explicitly justified; otherwise it should be split

Avoid mixing:

- feature work
- large refactors
- unrelated docs cleanup
- roadmap changes not required by the slice

## Local-First Rule

For normal QuantLab work, prefer developing locally before the first push to `origin`.

Why:

- it reduces stale stacked remote branches
- it avoids noisy GitHub compare screens
- it keeps PRs cleaner
- it reduces repeated context reconstruction during the work

Recommended default:

- do not push after the first incomplete change
- push when the slice already has:
  - coherent code
  - focused validation
  - a usable PR body
  - an issue reference if the work is not an urgent exception

## Battery of Commits

The preferred commit pattern is a small battery of logical commits such as:

- `feat(...)` or `refactor(...)`
- `test(...)`
- `docs(...)`

This is not mandatory for every tiny change, but it is the default target because it keeps the local history easy to review before merge.

If local index state or conflict pressure makes that split too expensive, prefer one clean coherent commit over a messy history.

## When to Push Early

Push earlier than usual only when there is a good reason, such as:

- the work will span multiple sessions
- the branch is risky and needs remote backup
- the work is being reviewed collaboratively before it is complete
- the slice is intentionally stacked on top of another unmerged branch

If you push early, prefer opening a draft PR only when the remote branch is actually useful for review or coordination.

## Pull Request Rules

Use the repository PR template.

Keep PRs short and slice-oriented:

- `Summary`
- `Why`
- `Scope`
- `Validation`
- `Notes`

Prefer:

- short validation lists
- one issue closure per PR when possible
- integration PRs that summarize included slices instead of acting like changelogs
- PRs that clearly name the issue they close or continue
- PRs whose scope can be described without “and also”

Avoid:

- giant PR descriptions
- long lists of unrelated `Closes #...`
- raw shell-escaped text
- opening PRs from stale stacked branches after the real integration PR already exists
- multi-scope PRs without an explicit reason for why the work could not be kept slice-sized

## Merge Style

QuantLab generally benefits from `Squash and merge` for slice-sized PRs.

Why:

- `main` stays readable
- each merged PR remains one coherent unit
- the PR body carries the higher-level context

Use a different merge style only when preserving commit-by-commit history in `main` is clearly more valuable than a clean slice-level history.

## After Merge

After merge:

- let GitHub delete the remote branch automatically
- clean local branches that are already absorbed
- avoid leaving old stacked branches alive unless they are still active integration branches

## Core Principle

QuantLab prefers:

- issue-led, local-first slices
- explicit validation
- clean PR narratives
- minimal branch noise

The goal is not process overhead.
The goal is to keep the repo easy to reason about while the product surface grows.
