## Summary

- Describe the slice in one or two bullets.
- Mention the user-facing or boundary change.

## Issue

- Closes #

## Why

- Explain why this slice belongs now.
- State the concrete benefit.

## Scope

This PR does not:
- Add unrelated feature work.
- Expand scope beyond the slice.
- Introduce a second source of truth for the same content or behavior.

## Validation

Validated with:
- `npm run typecheck`
- `npm run smoke:fallback`
- [ ] React runtime tested manually (`QUANTLAB_DESKTOP_RENDERER=react`)
- [ ] Legacy runtime not regressed (`npm run start`)

## Desktop migration checklist (skip if not applicable)

- [ ] No new `dangerouslySetInnerHTML` added.
- [ ] No new positional `openTab(type, ...)` calls (use object form `openTab({ kind, ... })`).
- [ ] New tab kinds added to `MainContent.jsx` switch/dispatch.
- [ ] New tab kinds included in `TabType` discriminated union.
- [ ] `assertNever` exhaustiveness guard not broken.
- [ ] Suppressed type errors reference an issue number and a TODO comment.

## Duplication Check

- [ ] I searched for existing docs, surfaces, or contracts covering the same idea.
- [ ] I removed or replaced stale copies instead of keeping both versions.
- [ ] I did not introduce alternate lockfiles, package managers, or build paths.

## Compatibility / Risk

- Note any compatibility impact, if any.
- Note any operational or behavioral risk, if any.
- For desktop: note if legacy runtime behavior changes.
- For desktop: note if research_ui API surface changes.

## Notes

- Keep this section short.
- For stacked or integration PRs, summarize the included slices instead of writing a changelog.
- Prefer one issue closure per PR when possible.
- If this PR only aligns docs or contracts, say so explicitly.
- If multiple agents touched the repo, note the file ownership boundaries.
- For React migration slices: confirm which runtime (legacy / React / both) was tested.
