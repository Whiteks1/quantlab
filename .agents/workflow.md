# Project Workflow — QuantLab

This document defines the internal execution complement to the public workflow.

The public operating guide now lives in:

- `docs/workflow-operativo-codex.md`

Use this file to keep agent behavior aligned with that public guide without duplicating its full contents.

## 1. Branching Strategy

QuantLab follows a strict **Issue-Branch-PR** workflow:

1. **Issue**: Every task or bug should be represented by a GitHub Issue.
2. **Branch**: Create a dedicated branch for each issue.
3. **Pull Request**: All changes should be integrated via PR. Direct commits to `main` should be avoided.

Codex-created branches should use the `codex/` prefix.

### Mandatory collaboration contract

This workflow is mandatory for any external collaborator, including senior contributors and Codex-based execution agents.

QuantLab is not an open-ended sandbox. It is a repo with active contracts, ownership boundaries, and safety-sensitive surfaces.

Minimum non-negotiable rules:

- the canonical repository and `origin/main` are the source of truth
- no direct pushes to `main`
- `1 issue = 1 branch = 1 PR` by default
- one branch must carry one dominant technical story
- no work from stale, orphaned, or `gone` branches
- if a branch upstream disappears, new work restarts from `origin/main`
- the collaborator may propose architecture, but may not redefine roadmap, priorities, or ownership boundaries without explicit repository-owner approval

High-control surfaces requiring explicit preflight and narrow ownership:

- `src/quantlab/brokers/hyperliquid.py`
- `src/quantlab/cli/hyperliquid_submit_sessions.py`
- `report.json.machine_contract`
- `--json-request`
- `desktop/main.js`
- `desktop/scripts/smoke.js`
- `.github/workflows/ci.yml`

---

## 2. Agent Collaboration Model

When working with Codex or another execution-focused AI assistant, follow this protocol:

### Codex Chat Ownership Policy

Use separate Codex chats only when they map to a real technical boundary. Chats are reasoning contexts, not merge boundaries.

Default unit of work:

**Default: 1 issue = 1 branch = 1 PR.**
Deviate only when the issue is purely tracking and the implementation is intentionally split into reviewable slices.

If a task crosses boundaries, assign a single owner chat for that slice.

#### Canonical split for current QuantLab work

##### Engine owner chat
Owns QuantLab engine, contracts, CLI, reporting, paper/run/sweep logic, broker safety, and architecture/state docs tied to the execution engine.

Typical ownership:
- `main.py` only when acting as bootstrap or routing for engine-side behavior
- `src/quantlab/**`
- `tests/**`
- canonical artifact and report contracts
- CLI contract surfaces
- reporting and portfolio logic
- broker preflight, safety, and readiness on the engine side
- `.agents/**` when tied to architecture, contracts, roadmap, or engine workflow

Out of scope by default:
- `desktop/renderer/**`
- desktop visual system
- desktop shell chrome
- desktop-only smoke or readiness work
- evidence screenshots and desktop presentation surfaces

##### Desktop/UI owner chat
Owns the QuantLab desktop operational shell and its validation boundary.

Canonical ownership for the current desktop tranche:
- `Desktop runtime / bootstrap`
  Owner of `desktop/main.js`, `desktop/preload.js`, and the IPC contract necessary for the shell to start decoupled from `research_ui`.
- `Desktop smoke / readiness`
  Owner of `desktop/scripts/smoke.js`, shell readiness, local fallback readiness, and real desktop startup validation.
- `research_ui bootstrap validation from the shell boundary`
  Owner of validating that `research_ui` is available when required, without re-coupling the shell to that boot path.
- `Desktop CI tied to real smoke`
  Owner of the desktop-specific CI coverage related to real smoke and the local fallback scenario.
- `Desktop renderer shell`
  Owner of `desktop/renderer/app.js`, `desktop/renderer/index.html`, and the overall shell hierarchy.
- `Desktop workstation surfaces`
  Owner of `desktop/renderer/modules/tab-renderers.js` and the `Runs`, `Run Detail`, `Compare`, `Candidates`, `System`, `Paper Ops`, and `Launch review` surfaces.
- `Desktop chrome / visual system`
  Owner of `desktop/renderer/styles.css`, `desktop/renderer/modules/shell-chrome.js`, and the workstation-first visual language of the desktop.
- `Desktop renderer primitives / hardening`
  Owner of `desktop/renderer/modules/view-primitives.js` and renderer hardening work needed so redesign is not built on unnecessary debt.

Short form:
- Desktop/UI owner across runtime bootstrap, smoke readiness, `research_ui` availability validation from the shell boundary, desktop-specific CI smoke coverage, renderer shell, workstation surfaces, chrome visual system, and renderer hardening.

Out of scope by default:
- `src/quantlab/**`
- engine-side contracts unless strictly required by the shell boundary
- broker safety logic
- canonical reporting semantics
- CLI or product logic not specific to desktop behavior

#### Boundary rules

##### A chat may work only inside its owned slice
Before implementation, define:
- `Issue`
- `Target branch`
- `Owner chat`
- `Allowed paths`
- `Out-of-scope paths`

Recommended preflight block:

```text
Issue: #<number>
Target branch: <branch-name>
Owner: Engine owner chat / Desktop/UI owner chat

Allowed paths:
- <paths>

Out of scope:
- <paths>

Rules:
- keep scope narrow
- do not touch files outside allowed paths
- if a required change crosses boundary, stop and report it
- plan first, implement second
```

##### Shared-boundary files requiring special care
The following files or surfaces are boundary-sensitive and must not be changed in parallel by both chats:

- `main.py`
- `.github/workflows/ci.yml`
- canonical JSON and report contracts
- `desktop/main.js`
- `desktop/scripts/smoke.js`
- docs defining canonical behavior
- tests validating shell to engine contract behavior

If a task requires changes across these boundaries, assign one single owner chat for the slice. Do not split the same slice across both chats.

##### Source-of-truth rule
If there is a conflict between:

- a stale local checkout
- an old branch
- a forked workspace
- or undocumented assumptions

the source of truth is:

1. repository state in `origin/main`
2. current issue and merged PR history
3. `.agents/current-state.md`
4. public docs

Do not continue implementation from a branch that no longer reflects the canonical repository state.

##### No ownership by file name alone
Ownership is determined by dominant concern, not by file name alone.

A change touching a desktop file does not automatically belong to the Desktop/UI owner chat if it redefines canonical engine behavior, contracts, or reporting semantics.

A change touching engine-side files does not automatically belong to the Engine owner chat if it is strictly about shell behavior, readiness, presentation, or desktop validation.

##### No silent cross-boundary edits
If implementation reveals required changes outside the declared slice:

- document the needed cross-boundary change explicitly
- stop and report it, or
- open a new dedicated slice

Do not silently absorb cross-boundary edits into the current slice.

##### Ownership rule for mixed tasks
If a task crosses desktop and engine boundaries, assign ownership by dominant concern:

- contractual, canonical, or engine behavior -> Engine owner chat
- shell, presentation, readiness, smoke, or renderer behavior -> Desktop/UI owner chat

Do not run both chats in parallel on the same mixed slice.

### /read-and-plan
When starting a new issue or session:
- Confirm the task category and the correct repository before changing files.
- Read the relevant `.agents/` context files.
- Read the task file in scope.
- Restate the current understanding and exact scope.
- Propose the smallest viable implementation or cleanup plan, including touched files, assumptions, and non-obvious risks for substantial work.
- Escalate only when scope, ownership, or risk is unclear.

If the user has already approved execution and the scope is clear, Codex may proceed after reading the required context.

### /execute-task
During implementation:
- Execute one well-defined step at a time.
- Keep changes tightly scoped to the approved task.
- Prioritize broken public surface first, then internal state, then public contract and docs.
- Avoid opportunistic cleanup outside the declared slice.
- Log relevant continuity in `.agents/session-log.md` when appropriate.

### /close-session
When finishing work:
- Summarize what was completed.
- Note any important continuity for the next session.
- Record the validation actually run in the issue, PR, or `.agents/session-log.md`.
- Leave the branch in a reviewable state for PR preparation.

---

## 3. Task Management (`.agents/tasks/`)

Active work is tracked in task files under `.agents/tasks/`.

- **Purpose**: Maintain a persistent record of the current objective and sub-tasks.
- **Use**: Tasks help preserve continuity across sessions and keep implementation aligned with issue scope.

---

## 4. Documentation First

- Public workflow and repository-facing guidance should live in `docs/`.
- Architecture changes must be reflected in `.agents/architecture.md`.
- File placement rules must be reflected in `.agents/code-map.md`.
- Artifact or output contract changes must be reflected in `.agents/artifact-contracts.md`.
- Codex-specific operating guidance belongs in `.agents/prompts/codex-master-prompt.md`.

---

## 5. Workflow Rule

Before changing files, confirm:
- why those files are the correct place for the change
- that the task scope is still respected
- that unrelated files remain untouched
- that stray files are not being pulled into the change without an explicit decision

Before implementing, confirm the target branch and verify that the current diff matches the intended slice.

Suggested checks:

```bash
git status
git diff --stat
git diff -- <paths>
```

If the working tree is already dirty, verify that the existing diff belongs to the intended slice before continuing.

When a slice touches runtime code, contracts, CLI, or test-bearing behavior, run the relevant validation and record what actually ran in the issue, PR, or `.agents/session-log.md`.

### Post-merge closeout

After a PR merges, the closeout is not optional. The expected finish is:

1. confirm the linked issue is closed or explicitly close it
2. delete the remote branch
3. delete or clean the local branch
4. remove or clean the associated worktree when one was used
5. fetch with prune so the local repo stops tracking merged remote branches
6. return to a valid base before starting the next slice

Do not leave merged work hanging around as active local context unless it is an intentional integration branch.

### Authoritative local working-copy posture

The repository should always have one unambiguous local starting point.

Required local posture:

- the primary worktree should be the canonical checkout
- that canonical checkout should sit on local `main`
- local `main` should fast-forward to `origin/main` before new slice work starts
- new slices should start from dedicated worktrees or branches created from `origin/main`

Keep an extra worktree only when all of the following are true:

- it still belongs to an active issue or active PR
- it still carries unique local work or intentional unmerged context
- it is not merely a stale mirror of already-merged history

Close a worktree when any of the following becomes true:

- its branch has no unique commits versus `origin/main`
- its upstream remote branch is gone and the work is already merged or superseded
- the linked issue and PR are already closed
- it no longer represents a valid starting point for the next session

If a worktree is dirty but still active, keep it and mark it explicitly as the one remaining live exception.
