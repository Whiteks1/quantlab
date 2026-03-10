# QuantLab

QuantLab is a personal quantitative research laboratory designed to explore, validate, and evolve trading strategies through a modular and research-focused architecture.

## What is QuantLab

QuantLab is built as a **CLI-first system** focused on:

- market data ingestion and caching
- technical indicators
- modular trading strategies
- backtesting with performance metrics
- portfolio-level analysis
- future evolution toward paper trading and controlled execution

The project is intended as a **quantitative experimentation environment** where strategies can be developed, tested, compared, and improved through reproducible workflows.

## Project Goal

QuantLab begins as a **personal research laboratory** focused on strategy research, reproducible experimentation, and portfolio-level reasoning.

The current priority is not building a SaaS platform or a complex service layer.  
Instead, the goal is to establish a strong research core that can later evolve toward automation, broker integration, or broader capabilities if the project justifies it.

## Requirements

- Windows 11
- Python 3.10+ (recommended 3.11 / 3.12)
- Git
- VS Code

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .