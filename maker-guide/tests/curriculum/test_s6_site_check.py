"""Exercise the taught S6 checker without contacting any network service."""

from __future__ import annotations

import os
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "script_path",
    ["mentors/s06-solutions/site-check.sh", "sessions/S06/self-study.md"],
)
@pytest.mark.parametrize("homepage_curl_exit_status", [0, 6])
@pytest.mark.parametrize(
    "report_response",
    [
        ("200", 0, "OK:"),
        ("404", 0, "MISSING:"),
        ("302", 0, "CHECK:"),
        ("403", 0, "CHECK:"),
        ("500", 0, "CHECK:"),
        ("502", 0, "CHECK:"),
        ("000", 6, "CONNECTION FAILED:"),
        ("200", 28, "CONNECTION FAILED:"),
    ],
)
def test_reference_checker_diagnoses_both_pages(
    temporary_path: Path,
    script_path: str,
    homepage_curl_exit_status: int,
    report_response: tuple[str, int, str],
) -> None:
    """A response code is interpreted only after a successful curl invocation."""
    http_status, curl_exit_status, expected_message = report_response
    reference_script = (
        files("maker_guide.curriculum")
        .joinpath("content/lf2607", script_path)
        .read_text(encoding="utf-8")
    )
    if script_path.endswith(".md"):
        reference_script = reference_script.split("````bash\n", 1)[1].split("\n````", 1)[0]
    bash_path = shutil.which("bash")
    assert bash_path is not None
    temporary_path.joinpath("curl").write_text(
        (
            f"#!{bash_path}\n"
            'printf \'%s\\n\' "$@" >> "$CURL_CALLS"\n'
            'if [[ "${!#}" == */maker-report.html ]]; then\n'
            "  printf '%s' \"$TEST_HTTP_STATUS\"\n"
            '  if [[ "$TEST_CURL_EXIT" != "0" ]]; then\n'
            "    printf 'simulated curl failure\\n' >&2\n"
            "  fi\n"
            '  exit "$TEST_CURL_EXIT"\n'
            "fi\n"
            'if [[ "$TEST_HOMEPAGE_CURL_EXIT" != "0" ]]; then\n'
            "  printf '000'\n"
            "  printf 'simulated homepage failure\\n' >&2\n"
            '  exit "$TEST_HOMEPAGE_CURL_EXIT"\n'
            "fi\n"
            "printf '200'\n"
        ),
        encoding="utf-8",
    )
    temporary_path.joinpath("curl").chmod(0o755)
    completed_process = subprocess.run(
        [bash_path, "-c", reference_script],
        cwd=temporary_path,
        env=os.environ
        | {
            "PATH": str(temporary_path),
            "USER": "s6-learner",
            "CURL_CALLS": str(temporary_path / "calls.txt"),
            "TEST_HOMEPAGE_CURL_EXIT": str(homepage_curl_exit_status),
            "TEST_HTTP_STATUS": http_status,
            "TEST_CURL_EXIT": str(curl_exit_status),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert completed_process.returncode == 0, completed_process.stderr
    output_lines = completed_process.stdout.splitlines()
    assert "https://lf2607.kolamayermakers.org/~s6-learner/" in output_lines[0]
    if homepage_curl_exit_status:
        assert output_lines[0].startswith("CONNECTION FAILED:")
        assert "returned HTTP" not in output_lines[0]
    else:
        assert output_lines[0].startswith("OK:")
        assert "HTTP 200" in output_lines[0]
    report_line_index = 2 if homepage_curl_exit_status else 1
    assert output_lines[report_line_index].startswith(expected_message)
    assert completed_process.stderr == (
        ("simulated homepage failure\n" if homepage_curl_exit_status else "")
        + ("simulated curl failure\n" if curl_exit_status else "")
    )
    if curl_exit_status:
        assert "returned HTTP" not in output_lines[report_line_index]
    else:
        assert f"HTTP {http_status}" in output_lines[report_line_index]
    if expected_message == "MISSING:":
        repair_message = output_lines[report_line_index + 1]
        assert repair_message.index("maker-report.sh") < repair_message.index("build-website")
    assert temporary_path.joinpath("calls.txt").read_text(encoding="utf-8").splitlines() == [
        argument
        for page in ("", "maker-report.html")
        for argument in (
            "-sS",
            "-I",
            "--max-time",
            "10",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            f"https://lf2607.kolamayermakers.org/~s6-learner/{page}",
        )
    ]
