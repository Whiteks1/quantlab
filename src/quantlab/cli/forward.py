from __future__ import annotations

from typing import Any, Callable


def handle_forward_commands(
    args,
    *,
    run_forward_mode: Callable[[Any], None],
) -> bool:
    """
    Handle forward-evaluation related CLI modes.

    Returns True if a forward command was executed and the caller
    should exit early.
    Returns False otherwise.
    """
    if args.forward_eval or args.resume_forward:
        run_forward_mode(args)
        return True

    return False