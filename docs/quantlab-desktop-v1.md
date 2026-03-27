# QuantLab Desktop v1

Status: draft  
Date: 2026-03-27

## Product Sentence

QuantLab Desktop is the single operator workspace for quantitative research, execution review, and bounded AI assistance.

It is not a collection of local UIs.
It is the main work surface of the laboratory.

## Core Goal

Create a single desktop shell that lets an operator:

- define work
- launch work
- inspect results
- compare alternatives
- decide what deserves to advance
- supervise runtime surfaces

without juggling browser tabs, manual terminals, and disconnected tools.

## Problem

Today the system has useful pieces:

- QuantLab run and artifact surfaces
- Stepbit chat and orchestration capabilities
- `meta_trade` pre-trade planning
- operational views such as paper, broker, and venue health

But it does not yet have a single primary surface that imposes order on those capabilities.

The result is:

- too many local entry points
- context switching
- weak continuity across the research cycle
- friction between action, review, and decision

## Non-Goals

- do not rewrite QuantLab from scratch
- do not make Stepbit the control plane of QuantLab
- do not embed every existing web UI unchanged
- do not move QuantLab authority into chat
- do not make `meta_trade` part of QuantLab internals

## Product Principles

- one app, one main entry point
- chat is central, but not the only interaction surface
- tabs are contextual and task-driven
- actions should be explicit and auditable
- the shell must supervise local services instead of assuming they are healthy
- QuantLab remains sovereign
- Stepbit remains optional and augmentative

## Authority Model

### QuantLab owns

- run execution
- run history
- artifact truth
- research state
- paper and execution boundaries
- promotion and safety semantics

### Stepbit owns

- reasoning assistance
- tool orchestration
- goal execution
- optional automation
- optional cognitive workflows

### `meta_trade` owns

- pre-trade planning
- upstream handoff semantics
- calculator-specific workbench logic

## Primary Entities

### Workspace

The desktop shell state for one operator session.
It knows:

- open tabs
- selected run context
- recent commands
- runtime status

### Experiment

A reusable research intent or prepared configuration.

### Run

A concrete execution with config, status, metrics, timestamps, and artifacts.

### Sweep

A grouped set of related runs created to explore parameter or strategy variants.

### Comparison

A focused side-by-side decision surface for selected runs.

### Artifact

Any canonical output used to inspect, explain, or justify results.

### PaperSession

A runtime session that moves beyond pure research into supervised operational behavior.

### ChatTask

A user-issued command or request handled through the QuantLab assistant.

## Interaction Model

QuantLab Desktop v1 should not be "chat only".

It should combine four interaction modes:

### 1. Specialized QuantLab Chat

The main conversational surface.

Use it for:

- launch requests
- summaries
- failure explanations
- run lookup
- artifact lookup
- comparisons
- next-step suggestions

The chat should speak QuantLab objects, not generic assistant language.

Example intents:

- launch a run for ETH-USD with the latest baseline config
- compare the last three completed runs
- explain why the latest run failed
- open the report for the best sharpe candidate
- prepare a paper-ready summary for this run

### 2. Command Palette

The fast path for repeatable explicit actions.

Use it for:

- launch run
- launch sweep
- open latest failed run
- compare selected runs
- open artifacts
- open paper ops
- open Stepbit tools

This is better than chat for deterministic operator actions.

### 3. Action Panels

Short, structured forms for tasks where ambiguity is costly.

Initial panels:

- Launch Run
- Launch Sweep
- Compare Runs
- Prepare Paper

These should be compact and safe, not giant workflows.

### 4. Context Tabs

Tabs are where focused work happens after the user triggers an action.

The chat and palette should open tabs rather than new windows.

## Tabs v1

Keep v1 small.

### Chat

The main command and reasoning surface.

### Run

Detailed run view with:

- summary
- metrics
- config
- artifacts
- failure state if applicable

### Compare

Side-by-side comparison for 2 to 4 runs.

### Artifacts

Focused artifact explorer for reports, configs, logs, and machine-readable outputs.

### Paper Ops

Operational view for paper-related state, runtime visibility, and session supervision.

## Optional Tabs After v1

- Candidates
- Sweep Inspector
- Stepbit Tools
- Pre-Trade Intake

These should only be added once the core workflow is solid.

## Why Not Make It Chat-Only

Chat is good for:

- flexible intent
- summarization
- natural-language retrieval
- explanation

Chat is weak for:

- high-precision structured input
- dense side-by-side comparison
- audit-friendly operational monitoring
- repeated actions with low ambiguity

Therefore v1 should be chat-centered, not chat-exclusive.

## What To Reuse From Stepbit

QuantLab should reuse Stepbit as an engine layer, not as the visible product shell.

### Reuse directly

- `stepbit-core` goals and reasoning endpoints
- MCP tool execution
- pipeline execution
- chat-completion and streaming runtime
- optional automation primitives

### Reuse selectively

- session persistence patterns from `stepbit-app`
- streaming message protocol patterns
- execution-history ideas

### Do not reuse as-is

- the full Stepbit UI as the main QuantLab desktop surface
- Stepbit-owned product navigation
- Stepbit provider/model UX as the primary QuantLab interaction model

## Recommended Chat Architecture

The right v1 approach is:

```text
QuantLab Desktop Chat UI
    -> QuantLab Assistant Adapter
        -> Stepbit engine capabilities
        -> QuantLab contracts and tools
```

### QuantLab Desktop Chat UI

Owns:

- conversation surface
- prompts and actions framed in QuantLab language
- tab opening
- local workspace context

### QuantLab Assistant Adapter

Owns:

- command routing
- context assembly from QuantLab state
- mapping user intent to Stepbit goals, tool calls, or direct QuantLab actions
- producing structured action results for the desktop shell

### Stepbit engine capabilities

Provide:

- reasoning
- tool execution
- goal decomposition
- optional pipelines
- summarization

## Runtime Services Managed By The Shell

The desktop shell should supervise local services explicitly.

Initial runtime set:

- QuantLab local backend / execution entrypoints
- artifact and output surfaces already used by QuantLab
- Stepbit backend and frontend if enabled
- Stepbit core if enabled

The shell should show:

- up
- starting
- degraded
- down

for each runtime piece.

## Suggested Desktop Layout

### Sidebar

Stable navigation:

- Chat
- Launch
- Compare
- Artifacts
- Paper Ops

### Main Area

Tabbed work surface.

### Topbar

Minimal.
Useful items only:

- global search or quick jump
- command palette trigger
- runtime summary

### Bottom or Side Runtime Strip

Shows live status for:

- QuantLab
- Stepbit App
- Stepbit Core
- paper surfaces if available

## First Real User Flow

### Launch and Evaluate

1. Open the desktop app.
2. Ask chat to launch a run, or use the Launch panel.
3. Watch runtime and job state.
4. Open the resulting run tab.
5. Inspect metrics and artifacts.
6. Add the run to Compare.
7. Compare against prior candidates.
8. Decide whether to keep, discard, or prepare for paper.

### Failure Review

1. Ask chat for the latest failed run.
2. Open the run.
3. Ask chat to explain the likely failure cause.
4. Open the relevant artifact or log tab.
5. Decide whether to relaunch or archive the result.

## What Is Viable In v1

### Viable now

- desktop shell
- runtime manager
- chat tab
- launch panel
- run tabs fed by current QuantLab outputs
- compare tab over existing runs
- artifact inspection
- paper ops read-only or lightly interactive surfaces

### Not required for v1

- full experiment manager
- full candidate promotion workflow
- full Stepbit UI embedded inside the shell
- full `meta_trade` workbench integration inside the main loop

## Technology Direction

For a first shell, Electron is acceptable because it reduces friction around:

- process management
- local services
- multiple local runtimes
- web-based rendering reuse

This is a pragmatic v1 choice, not a permanent dogma.

## Migration Strategy

### Phase 1

Define contracts:

- chat intents
- tab types
- runtime states
- QuantLab assistant adapter responsibilities

### Phase 2

Build a minimal desktop shell with:

- sidebar
- chat
- tabs
- runtime status

### Phase 3

Connect real capabilities:

- launch run
- launch sweep
- open run
- compare runs
- inspect artifacts
- view paper ops

### Phase 4

Add bounded Stepbit augmentation:

- richer summaries
- command suggestions
- optional automation

## Acceptance Criteria For v1

- the operator opens one desktop app instead of several browser tools
- chat can trigger real QuantLab work through stable contracts
- repeated actions are available through palette or panels, not only chat
- runs, comparisons, and artifacts open in tabs
- runtime health is visible and honest
- Stepbit improves the experience without becoming the product shell

## Summary

QuantLab Desktop v1 should be:

- a single work surface
- centered on a QuantLab-specialized chat
- supported by palette, panels, and tabs
- powered by Stepbit where useful
- governed by QuantLab's own authority and contracts

This makes the desktop shell a layer of order over the current system, not a repackaging of existing fragmentation.
