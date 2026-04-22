"""Minimal module entrypoint for run_analysis pilot."""

from __future__ import annotations

import sys

from .runner import run_analysis

USAGE = "Usage: python -m quantlab.agents.run_analysis <run_id>"


def main(argv: list[str] | None = None) -> int:
    """Run extractive analysis for one run_id using default roots."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 2

    run_analysis(run_id=args[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
