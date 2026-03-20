#  QuantLab

QuantLab is a personal quantitative research laboratory designed to explore, validate, and evolve trading strategies through a modular, reproducible, and research-focused architecture.

## What is QuantLab

QuantLab is a **CLI-first quantitative research system** focused on:

- market data ingestion and caching
- technical indicators and feature preparation
- modular trading strategies
- backtesting with performance metrics
- forward validation workflows
- report generation and research artifacts
- portfolio-oriented comparison and analysis

The project is intended as a **quantitative experimentation environment** where strategies can be developed, tested, compared, and refined through structured and reproducible workflows.

## Project Goal

QuantLab begins as a **personal research laboratory** focused on strategy research, reproducible experimentation, and portfolio-level reasoning.

The current priority is not building a SaaS platform or a complex service layer.  
The goal is to establish a strong research core first, then evolve toward higher-level automation, broker integration, and broader execution capabilities only if the project maturity justifies it.

## Current Direction

QuantLab is being developed with a strong emphasis on:

- modular boundaries
- reproducible runs
- contract-driven outputs
- research traceability
- clean CLI workflows
- future extensibility without compromising the core design

This means the repository is not just a collection of scripts, but an evolving research engine with clear architectural intent.

## QuantLab × Stepbit

QuantLab and Stepbit operate at different but complementary layers.

- **QuantLab** provides the quantitative engine: backtesting, forward validation, reporting, and research artifacts.
- **Stepbit / stepbit-core** provides the orchestration layer: pipelines, reasoning graphs, scheduling, event automation, and observability.

The goal of the integration is not to merge responsibilities, but to connect them cleanly:

- **Stepbit acts as the control plane**
- **QuantLab acts as the execution engine**

This makes it possible to run quantitative research as a structured, local-first workflow: reproducible, traceable, automatable, and grounded in objective metrics.

## Current Status

QuantLab is currently in an active architecture and research-core development stage.

The project is centered on establishing a reliable foundation for:

- backtesting
- forward validation
- research reporting
- portfolio comparison
- stable execution contracts

Higher-level automation and orchestration are planned to grow on top of this foundation rather than being mixed into the core prematurely.

## Requirements

- Windows 11 or Ubuntu
- Python 3.10+ (recommended 3.11 / 3.12)
- Git

## Installation

```bash
python -m venv .venv
Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -e .
Linux / macOS
source .venv/bin/activate
pip install -e .

## Usage

Example entrypoint:

python main.py --help 
```

Depending on the current stage of the repository, available commands may include research execution, reporting, forward validation, and portfolio-related workflows.
## Design Principles

QuantLab is being built around a few core principles:

research first over productization

modularity over monolithic growth

reproducibility over ad hoc experimentation

clear contracts over implicit behavior

extensibility without collapsing architectural boundaries

## License

Licensed under the Apache License, Version 2.0.
