# QuantLab

QuantLab is a **CLI-first personal quantitative research laboratory** built for building and testing evolutionary trading systems.

## Core Features
- Data ingestion and caching
- Technical indicators and signals
- Layered modular strategies
- High-fidelity backtesting with advanced metrics
- Forward evaluation (Paper Trading) and Portfolio Aggregation

## Development Workflow
QuantLab follows a structured development process to ensure research reproducibility:
1. **Design**: Architectural changes and roadmaps are planned by the Architect (ChatGPT).
2. **Implementation**: Specific tasks are executed by the Execution Agent (Antigravity).
3. **Branching**: All work is done in dedicated branches (e.g., `feat/`, `fix/`, `docs/`).
4. **Stable Main**: The `main` branch is kept stable and reflects the current verified state of the lab.
5. **Research Focused**: QuantLab exists to investigate strategies with rigor, clarity, and control.

## Installation
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Requisitos
- Windows 11
- Python 3.10+ (recomendado 3.11/3.12)
- Git
- VS Code

## Workflows
For more information on the development standards, see the [workflows](.agents/workflows/) directory.