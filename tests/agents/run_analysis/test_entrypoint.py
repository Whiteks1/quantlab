"""Tests for minimal run_analysis module entrypoint."""

from __future__ import annotations

from pathlib import Path

import quantlab.agents.run_analysis.__main__ as entrypoint


def test_entrypoint_without_args_fails_cleanly(capsys) -> None:
    exit_code = entrypoint.main([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Usage: python -m quantlab.agents.run_analysis <run_id>" in captured.err


def test_entrypoint_with_valid_run_id_executes_runner(monkeypatch) -> None:
    called: dict[str, str] = {}

    def _fake_run_analysis(*, run_id: str):
        called["run_id"] = run_id
        return object()

    monkeypatch.setattr(entrypoint, "run_analysis", _fake_run_analysis)

    exit_code = entrypoint.main(["run_001"])

    assert exit_code == 0
    assert called == {"run_id": "run_001"}


def test_entrypoint_does_not_introduce_console_scripts() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    pyproject = repo_root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert "[project.scripts]" in text
    scripts_block = text.split("[project.scripts]", maxsplit=1)[1].split(
        "\n[", maxsplit=1
    )[0]
    assert 'quantlab = "quantlab.app:main"' in scripts_block
    assert "run_analysis" not in scripts_block
