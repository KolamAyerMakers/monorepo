"""Control the root-owned learner registration availability marker."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from rich.console import Console

from maker_guide.deployment import REGISTRATION_STATE_FILE


def main(arguments: Sequence[str] | None = None) -> int:
    """Open, close, or report learner registration."""
    parser = argparse.ArgumentParser(description="Control Maker Guide learner registration.")
    _ = parser.add_argument("action", choices=("check", "open", "close", "status"))
    action = cast("str", parser.parse_args(arguments).action)
    state_file = Path(REGISTRATION_STATE_FILE)
    if action == "check":
        if registration_is_open(state_file):
            return 0
        Console(stderr=True).print("Registration is closed.")
        return 1
    if action == "open":
        open_registration(state_file)
    elif action == "close":
        close_registration(state_file)
    Console().print(f"Registration is {'open' if registration_is_open(state_file) else 'closed'}.")
    return 0


def registration_is_open(state_file: Path) -> bool:
    """Return whether registration has been explicitly opened."""
    return state_file.is_file()


def open_registration(state_file: Path) -> None:
    """Mark registration as open."""
    state_file.touch(mode=0o600, exist_ok=True)


def close_registration(state_file: Path) -> None:
    """Mark registration as closed."""
    state_file.unlink(missing_ok=True)
