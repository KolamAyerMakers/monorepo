"""Exercise S7 shell activities without opening a network connection."""

from __future__ import annotations

import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("document_name", "port"),
    [
        ("sessions/S07/slides.md", "11234"),
        ("sessions/S07/self-study.md", "11234"),
        ("commands/nc.md", "8000"),
    ],
)
def test_raw_http_request_preserves_framing_and_bounded_loopback_target(
    temporary_path: Path,
    document_name: str,
    port: str,
) -> None:
    """Run the documented printf pipeline through a byte-preserving fake nc."""
    bash_path = shutil.which("bash")
    assert bash_path is not None
    cat_path = shutil.which("cat")
    assert cat_path is not None
    command_match = re.search(
        (
            r"(?m)^(?P<command>printf '%s\\r\\n'[^\n]*(?:\n[ \t]+[^\n]*)*"
            r"\n[ \t]+timeout[^\n]*)$"
        ),
        files("maker_guide.curriculum")
        .joinpath(f"content/lf2607/{document_name}")
        .read_text(encoding="utf-8"),
    )
    assert command_match is not None
    completed_process = subprocess.run(
        [
            bash_path,
            "--noprofile",
            "--norc",
            "-c",
            r"""timeout() {
    printf '%s\n' "$@" >&2
    shift
    "$@"
}
nc() {
    printf '%s\n' "$@" >&2
    "$CAT"
}
"""
            + command_match["command"],
        ],
        cwd=temporary_path,
        env={"PATH": str(temporary_path), "CAT": cat_path, "PORT": port},
        capture_output=True,
        check=False,
        timeout=5,
    )
    assert completed_process.returncode == 0, completed_process.stderr
    assert completed_process.stderr == (
        f"5s\nnc\n-N\n-w\n3\n127.0.0.1\n{port}\n-N\n-w\n3\n127.0.0.1\n{port}\n".encode()
    )
    assert completed_process.stdout == (
        f"GET / HTTP/1.1\r\nHost: localhost:{port}\r\n\r\n".encode()
    )


@pytest.mark.parametrize(
    ("document_name", "input_paths"),
    [
        ("compare-source-and-output.md", ("src/pages/index.md", "public_html/index.html")),
        (
            "compare-page-fetches.md",
            ("playground/home-fetch.html", "playground/report-fetch.html"),
        ),
    ],
)
@pytest.mark.parametrize(
    "second_content",
    ["same\n", "different\n", None],
    ids=("identical", "different", "missing"),
)
def test_documented_diff_commands_accept_differences_but_preserve_errors(
    temporary_path: Path,
    document_name: str,
    input_paths: tuple[str, str],
    second_content: str | None,
) -> None:
    """Accept diff status 1 for observation without swallowing file-reading errors."""
    bash_path = shutil.which("bash")
    assert bash_path is not None
    diff_path = shutil.which("diff")
    assert diff_path is not None
    temporary_path.joinpath("diff").symlink_to(diff_path)
    first_path = temporary_path / input_paths[0]
    second_path = temporary_path / input_paths[1]
    first_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("same\n", encoding="utf-8")
    if second_content is not None:
        second_path.write_text(second_content, encoding="utf-8")
    completed_process = subprocess.run(
        [
            bash_path,
            "--noprofile",
            "--norc",
            "-c",
            next(
                line
                for line in (
                    files("maker_guide.curriculum")
                    .joinpath(f"content/lf2607/quests/{document_name}")
                    .read_text(encoding="utf-8")
                    .splitlines()
                )
                if line.startswith("diff ")
            ),
        ],
        cwd=temporary_path,
        env={"HOME": str(temporary_path), "PATH": str(temporary_path)},
        capture_output=True,
        check=False,
        timeout=5,
    )
    if second_content is None:
        assert completed_process.returncode != 0, completed_process.stderr
    else:
        assert completed_process.returncode == 0, completed_process.stderr
