# Desktop Candidates / Shortlist v1

Status: plan-only  
Issue: #196  
Branch: `codex/desktop-candidates-shortlist-v1`  
Date: 2026-03-28

## Goal

Add the smallest possible native decision layer to QuantLab Desktop so the shell can support:

`launch -> inspect -> compare -> decide`

without turning into a tagging system, portfolio manager, or AI ranking surface.

## Product Intent

This slice exists to solve one problem:

QuantLab Desktop can already open and inspect work, but it still lacks a minimal place to decide which runs deserve to stay alive.

Candidates / Shortlist v1 should introduce:

- memory of promising runs
- a single baseline marker
- a compact shortlist surface
- fast handoff into compare and artifacts

It should not try to solve broader workflow orchestration yet.

## Entities

### Candidate

A run that the operator marks as worth keeping visible.

Required fields:

- `run_id`
- `note`
- `added_at`

### Shortlist

A subset of candidates currently under active consideration.

Required fields:

- ordered list of `run_id`

### Baseline

One run used as the current reference point.

Required fields:

- `run_id`
- `marked_at`

## Persistence

Use a simple local JSON store inside QuantLab outputs or desktop state.

Suggested shape:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-03-28T00:00:00Z",
  "baseline_run_id": "20260327_...",
  "candidates": [
    {
      "run_id": "20260327_...",
      "note": "promising risk-adjusted result",
      "added_at": "2026-03-28T00:00:00Z",
      "shortlisted": true
    }
  ]
}
```

Suggested location:

- `outputs/desktop/candidates_shortlist.json`

Requirements:

- explicit linkage to `run_id`
- versionable and local-first
- safe to read even if missing
- no database and no sync layer

## Scope v1

### In

- mark or unmark a run as candidate
- add or remove a candidate from shortlist
- mark exactly one run as baseline
- store a short optional note
- show candidate list and shortlist in the shell
- open compare from selected shortlist entries
- open artifacts from candidate rows

### Out

- AI scoring
- ranking heuristics
- Stepbit integration
- shared multi-user state
- candidate workflow states beyond candidate / shortlisted / baseline
- portfolio or promotion engine behavior

## UI Slice

Keep the UI native to the shell and small.

### New shell surface

Add one native tab or panel:

- `Candidates`

### Minimal layout

Top summary:

- total candidates
- shortlist count
- current baseline

Main body:

- candidate rows
- shortlist badge
- baseline badge
- note preview
- quick actions

Row actions:

- mark shortlist
- remove shortlist
- mark baseline
- open run
- open artifacts
- add to compare selection

## Interaction Rules

- candidate state should only apply to runs that exist in the current registry
- if a stored `run_id` no longer exists, show it as missing but do not crash
- baseline must be unique
- shortlist can contain multiple entries
- note is optional and short; no rich text

## Desktop Integration

This slice should fit current shell structure:

- sidebar entry for `Candidates`
- command palette action for `Open Candidates`
- deterministic chat actions later, but not required in v1 implementation

Suggested future chat hooks, not required for first patch:

- `mark latest run as candidate`
- `set baseline to <run_id>`
- `open shortlist`

## Technical Plan

### 1. Add local store helpers

- read store
- write store
- normalize defaults
- guard missing file

### 2. Expose shell-side state management

- load candidates with snapshot refresh
- map stored `run_id`s back to current run registry
- handle missing runs explicitly

### 3. Add native Candidates surface

- summary strip
- candidate list
- shortlist toggles
- baseline toggle
- note editing surface kept minimal

### 4. Connect shell actions

- open compare from shortlist selection
- open artifacts from candidate row
- open run detail from candidate row

### 5. Validate

- shell JS checks
- existing `research_ui` server tests
- small manual workflow check in desktop shell

## Risks

### Scope creep

Main risk:

Candidates turns into a generic tagging or ranking subsystem.

Mitigation:

- only three concepts: candidate, shortlist, baseline
- no scoring
- no automation
- no recommendation logic

### Persistence drift

Risk:

stored `run_id`s may point to missing runs.

Mitigation:

- show missing state explicitly
- never crash on absent run

## Acceptance Criteria

- an operator can mark a run as candidate from the shell
- an operator can maintain a shortlist
- one run can be marked as baseline
- candidates can open compare and artifacts quickly
- state survives shell restarts through a local store
- the feature stays small and decision-focused

## Implementation Note

This branch should remain plan-only until the next explicit implementation step.
