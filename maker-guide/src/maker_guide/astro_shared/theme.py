"""Shared Astro theme resources."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path


def copy_site_theme(destination: Path) -> None:
    """Copy the shared Astro site stylesheet."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with resources.as_file(
        resources.files("maker_guide.astro_shared").joinpath("site.css")
    ) as stylesheet:
        shutil.copy2(stylesheet, destination)
