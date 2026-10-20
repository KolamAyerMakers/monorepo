"""Protect independent practice and preservation of the last useful publication."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path
from textwrap import dedent
from typing import cast
from zipfile import ZipFile

import pytest

from maker_guide import self_study_pack
from maker_guide.repositories.helpers import load_json


def test_practice_site_has_no_classroom_runtime_dependency(temporary_path: Path) -> None:
    """The shipped site builds without class aliases, projections, or Codex/TeX tools."""
    destination = temporary_path / "practice.zip"
    self_study_pack.write_practice_kit(destination)
    with ZipFile(destination) as archive:
        prefix = "linux-foundations-practice/site/"
        names = archive.namelist()
        assert not any("node_modules" in name or "/.git/" in name for name in names)
        manifest = load_json(archive.read(prefix + "package.json").decode("utf-8"))
        scripts = cast("dict[str, str]", manifest["scripts"])
        assert "maker-guide-" not in scripts["build"]
        layout = archive.read(prefix + "app/layouts/SiteLayout.astro")
        build = archive.read(prefix + "scripts/build.mjs")
        assert b"learnerProgress" not in layout
        assert b"/makers" not in layout
        assert b"buildCodex" not in build
        assert b"userInfo" not in archive.read(prefix + "astro.config.mjs")
        assert prefix + "scripts/publish.mjs" in names
        assert prefix + "app/content.config.ts" in names
        assert prefix + "app/styles/site.css" in names


def test_pdf_links_preserve_code_examples(temporary_path: Path) -> None:
    """Cross-document links change format without altering literal Markdown being taught."""
    document = temporary_path / "guide.md"
    target = temporary_path / "target.md"
    _ = document.write_text(
        "[Read more](target.md#example)\n\n```markdown\n[Example syntax](target.md#example)\n```\n",
        encoding="utf-8",
    )
    result = self_study_pack._pdf_markdown(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        document, {target}
    )
    assert "[Read more](target.pdf#example)" in result
    assert "[Example syntax](target.md#example)" in result


@pytest.mark.parametrize("failure", ["none", "download", "null"])
def test_bulletin_reference_preserves_previous_page_on_failure(
    temporary_path: Path, failure: str
) -> None:
    """Fixture-backed downloads reject failures/missing fields without losing good Markdown."""
    bash = shutil.which("bash")
    jq = shutil.which("jq")
    assert bash is not None
    if jq is None:
        pytest.skip("jq is not installed")
    pages = temporary_path / "src/pages"
    pages.mkdir(parents=True)
    page = pages / "today.md"
    _ = page.write_text("Previous good bulletin\n", encoding="utf-8")
    weather = {
        "daily": {
            "time": ["2026-10-10"],
            "temperature_2m_max": [None if failure == "null" else 31.5],
            "precipitation_probability_max": [20],
            "sunrise": ["2026-10-10T06:54"],
            "sunset": ["2026-10-10T18:58"],
        }
    }
    air = {"current": {"time": "2026-10-10T09:00", "pm2_5": 4.2}}
    binary_directory = temporary_path / "bin"
    binary_directory.mkdir()
    fake_curl = binary_directory / "curl"
    _ = fake_curl.write_text(
        dedent(f"""\
            #!/usr/bin/python3
            import pathlib, sys
            arguments = sys.argv[1:]
            url = arguments[arguments.index('--max-time') + 2]
            weather = {json.dumps(json.dumps(weather))}
            air = {json.dumps(json.dumps(air))}
            failure = {failure!r}
            destination = pathlib.Path(arguments[arguments.index('-o') + 1])
            destination.write_text(weather if '/forecast?' in url else air)
            sys.exit(22 if failure == 'download' else 0)
            """),
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    script = files("maker_guide.curriculum").joinpath("content/lf2607/guides/resources/today.sh")
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-c", script.read_text(encoding="utf-8")],
        env=os.environ
        | {
            "HOME": str(temporary_path),
            "PATH": f"{binary_directory}:{Path(jq).parent}:/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if failure != "none":
        assert result.returncode != 0
        assert page.read_text(encoding="utf-8") == "Previous good bulletin\n"
    else:
        assert result.returncode == 0, result.stderr
        bulletin = page.read_text(encoding="utf-8")
        assert "31.5 °C" in bulletin
        assert "20%" in bulletin
        assert "4.2 μg/m³" in bulletin
        assert "2026-10-10T09:00" in bulletin
        assert "modelled" in bulletin
        assert "CAMS" in bulletin
