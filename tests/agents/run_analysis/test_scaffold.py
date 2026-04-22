"""Scaffold tests for QuantLab run_analysis agent package."""

import importlib


def test_agents_package_imports() -> None:
    module = importlib.import_module("quantlab.agents")
    assert module is not None


def test_run_analysis_package_imports() -> None:
    module = importlib.import_module("quantlab.agents.run_analysis")
    assert module is not None


def test_run_analysis_scaffold_exposes_no_runtime() -> None:
    module = importlib.import_module("quantlab.agents.run_analysis")
    assert not hasattr(module, "run")
    assert not hasattr(module, "main")

    runner_module = importlib.import_module("quantlab.agents.run_analysis.runner")
    assert hasattr(runner_module, "run_analysis")
    main_module = importlib.import_module("quantlab.agents.run_analysis.__main__")
    assert hasattr(main_module, "main")
