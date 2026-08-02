"""Tests for Debian MOTD cleanup state."""

from __future__ import annotations

import importlib
from typing import Protocol, cast

from tests.support.paths import SALTSTACK_DIRECTORY


class _YamlModule(Protocol):
    def safe_load(self, value: str) -> object:
        """Load YAML."""
        ...


def _load_state(template_name: str) -> dict[str, object]:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    return cast(
        dict[str, object],
        yaml_module.safe_load(
            (SALTSTACK_DIRECTORY / "states" / template_name).read_text(encoding="utf-8")
        ),
    )


def test_debian_motd_cleanup_removes_uname_hook() -> None:
    """Test Debian MOTD cleanup low state."""
    assert _load_state("debian_motd_cleanup/init.sls") == {
        "/etc/update-motd.d/10-uname": {"file.absent": []},
    }
