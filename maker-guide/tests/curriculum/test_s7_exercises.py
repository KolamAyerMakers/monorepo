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
