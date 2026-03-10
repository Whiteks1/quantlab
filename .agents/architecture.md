# Architecture - QuantLab

## Purpose
This document describes the current architectural structure of QuantLab and its intended evolution.

## System Orientation
QuantLab is a CLI-first quantitative research laboratory focused on:
- reproducible experimentation
- backtesting
- forward evaluation
- portfolio-level analysis
- structured reporting

## Architectural Principles
- layered architecture
- separation of concerns
- research-first design
- deterministic outputs where possible
- modular evolution over premature platform complexity

## Current Layered Structure
data -> indicators -> strategies -> backtest -> execution -> reporting -> portfolio

## High-Level Components

### data/
Responsible for data acquisition, normalization, and OHLC handling.

### features/ or indicators/
Responsible for indicator computation and feature generation.

### strategies/
Responsible for signal generation and strategy logic.

### backtest/
Responsible for historical simulation and performance evaluation.

### execution/
Responsible for paper execution and forward evaluation workflows.

### reporting/
Responsible for Markdown, JSON, CSV, and chart outputs.

### portfolio/
Responsible for portfolio aggregation, position logic, allocation, and selection layers.

## Project Memory Layer
The `.agents/` directory acts as the project memory and workflow coordination layer.

Key files:
- `project-brief.md`
- `current-state.md`
- `implementation-rules.md`
- `session-log.md`

## Workflow Layer
Development is coordinated through:
- `read-and-plan.md`
- `execute-task.md`
- `review-stage.md`
- `close-session.md`

## Current Architectural Focus
Current work is focused on Stage M.x portfolio evolution:
- aggregation
- hygiene
- allocation
- selection
- mode comparison

## Future Architectural Direction
Possible future extensions may include:
- broker integrations
- paper trading extensions
- research automation
- API or service layers
- broader user-facing workflows

These remain future possibilities, not current priorities.

## Guiding Principle
QuantLab should remain small enough to stay clear, but modular enough to evolve.