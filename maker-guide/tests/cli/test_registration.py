"""Tests for learner registration availability control."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from maker_guide.cli import registration
from maker_guide.cli.registration import close_registration, open_registration, registration_is_open
from maker_guide.registration import cli as registration_cli

if TYPE_CHECKING:
    import pytest


def test_open_and_close_registration(temporary_path: Path) -> None:
    """The marker enables registration only while present."""
    state_file = temporary_path / "registration-open"
    assert not registration_is_open(state_file)
    open_registration(state_file)
    assert registration_is_open(state_file)
    close_registration(state_file)
    assert not registration_is_open(state_file)


def test_configure_logging_uses_authpriv_syslog(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registration lifecycle events are tagged for journalctl lookup."""
    registration_logger = logging.getLogger("maker_guide.registration")

    def add_handler(handler: logging.Handler) -> None:
        assert isinstance(handler, registration_cli.SysLogHandler)
        assert handler.address == "/dev/log"
        assert handler.facility == registration_cli.SysLogHandler.LOG_AUTHPRIV
        assert handler.ident == "maker-guide-registration: "

    monkeypatch.setattr(registration_logger, "addHandler", add_handler)

    registration_cli.configure_logging()

    assert registration_logger.level == logging.INFO


def test_check_registration_returns_nonzero_when_closed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The SSH gate rejects registration before interactive prompts start."""
    monkeypatch.setattr(registration, "registration_is_open", _registration_is_closed)

    assert registration.main(["check"]) == 1
    assert capsys.readouterr().err == "Registration is closed.\n"


def _registration_is_closed(_state_file: Path) -> bool:
    return False
