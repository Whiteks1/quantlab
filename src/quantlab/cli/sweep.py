from __future__ import annotations

from typing import Any, Callable


def handle_sweep_command(
    args,
    *,
    run_sweep: Callable[..., Any],
) -> bool:
    """
    Handle sweep-related CLI mode.

    Returns True if sweep mode was executed and the caller
    should exit early.
    Returns False otherwise.
    """
    if args.sweep:
        out_dir = args.sweep_outdir or args.outdir
        run_sweep(args.sweep, out_dir=out_dir)
        return True

    return False