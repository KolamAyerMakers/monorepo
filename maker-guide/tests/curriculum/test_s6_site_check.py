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
    "pages",
    [
        ("", "maker-report.html"),
        ("maker-report.html", ""),
        ("",),
        ("maker-report.html",),
        ("not-a-page.html",),
        ("other/nested-page.html", "", "maker-report.html"),
        (),
    ],
)
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
def test_reference_checker_diagnoses_supplied_pages(  # noqa: C901, PLR0912, PLR0915 - page matrix
    temporary_path: Path,
    script_path: str,
    homepage_curl_exit_status: int,
    pages: tuple[str, ...],
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
            'if [[ "${!#}" != "https://lf2607.kolamayermakers.org/~s6-learner/" ]]; then\n'
            "  printf '404'\n"
            "  exit 0\n"
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
        [bash_path, "-c", reference_script, "site-check.sh", *pages],
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
    if not pages:
        assert completed_process.returncode == 2
        assert "usage:" in (completed_process.stdout + completed_process.stderr).lower()
        assert "PAGE" in completed_process.stdout + completed_process.stderr
        assert not temporary_path.joinpath("calls.txt").exists()
        return
    assert completed_process.returncode == 0, completed_process.stderr
    output_lines = iter(completed_process.stdout.splitlines())
    expected_errors = ""
    for page in pages:
        diagnosis = next(output_lines)
        if page == "maker-report.html":
            assert "maker-report.html" in diagnosis
            assert diagnosis.startswith(expected_message)
            if curl_exit_status:
                assert "returned HTTP" not in diagnosis
                expected_errors += "simulated curl failure\n"
                next(output_lines)
            else:
                assert f"HTTP {http_status}" in diagnosis
                if expected_message == "MISSING:":
                    repair_message = next(output_lines)
                    assert repair_message.index("maker-report.sh") < repair_message.index(
                        "build-website"
                    )
                elif expected_message == "CHECK:":
                    next(output_lines)
        else:
            assert f"https://lf2607.kolamayermakers.org/~s6-learner/{page}" in diagnosis
            if page:
                assert diagnosis.startswith("CHECK:")
                assert "HTTP 404" in diagnosis
                assert "maker-report.sh" not in next(output_lines)
            elif homepage_curl_exit_status:
                assert diagnosis.startswith("CONNECTION FAILED:")
                assert "returned HTTP" not in diagnosis
                expected_errors += "simulated homepage failure\n"
                next(output_lines)
            else:
                assert diagnosis.startswith("OK:")
                assert "HTTP 200" in diagnosis
    assert list(output_lines) == []
    assert completed_process.stderr == expected_errors
    if "maker-report.html" not in pages or expected_message != "MISSING:":
        assert "maker-report.sh" not in completed_process.stdout
    assert temporary_path.joinpath("calls.txt").read_text(encoding="utf-8").splitlines() == [
        argument
        for page in pages
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
