"""Protect the source boundary and the source-free report wire contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SiteCheckError,
    SiteCheckReport,
    parse_site_check_report,
    read_site_check_source,
    site_check_failure_messages,
    site_check_report_payload,
)
from maker_guide.validation_paths import UnixAccount

_DIGEST = "a" * 64
_SENTINEL = "private-source-sentinel"


@pytest.mark.parametrize(
    "replacement",
    [
        {"version": True},
        {"version": 1.0},
        {"source_sha256": "A" * 64},
        {"source_sha256": "b" * 64},
        {"source_sha256": _SENTINEL},
        {"cases": {}},
        {"cases": dict.fromkeys(SITE_CHECK_CASES, 1)},
        {"cases": dict.fromkeys((*SITE_CHECK_CASES, _SENTINEL), True)},
        {"cases": []},
        {"error": _SENTINEL},
        {"error": []},
        {_SENTINEL: True},
    ],
)
def test_report_rejects_untrusted_values_without_echoing_them(
    replacement: dict[str, object],
) -> None:
    """Only exact schema values can cross the learner-to-bot boundary."""
    payload: dict[str, object] = {
        "version": 1,
        "source_sha256": _DIGEST,
        "cases": dict.fromkeys(SITE_CHECK_CASES, True),
        "error": None,
    }
    with pytest.raises(SiteCheckError, match=r"^invalid-report$") as failure:
        parse_site_check_report(payload | replacement, _DIGEST)
    assert _SENTINEL not in str(failure.value)


@pytest.mark.parametrize("value", [None, [], "private-source-sentinel", {"version": 1}])
def test_report_requires_the_complete_object(value: object) -> None:
    """Missing fields and non-objects fail closed."""
    with pytest.raises(SiteCheckError, match=r"^invalid-report$"):
        parse_site_check_report(value, _DIGEST)


def test_report_round_trip_and_feedback_never_carry_source() -> None:
    """Fixed feedback survives serialization without output or source fields."""
    report = SiteCheckReport(
        source_sha256=_DIGEST,
        cases=tuple((case, case == "both-ok") for case in SITE_CHECK_CASES),
    )
    assert parse_site_check_report(site_check_report_payload(report), _DIGEST) == report
    assert len(site_check_failure_messages(report)) == len(SITE_CHECK_CASES) - 1
    assert _SENTINEL not in str(SiteCheckError(_SENTINEL))
    assert _SENTINEL not in " ".join(
        site_check_failure_messages(
            SiteCheckReport(source_sha256=_DIGEST, cases=report.cases, error=_SENTINEL)
        )
    )


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("missing", "missing-path"),
        ("directory", "not-regular-file"),
        ("fifo", "not-regular-file"),
        ("escape", "path-escapes-scope"),
        ("binary", "read-error"),
        ("invalid-utf8", "read-error"),
        ("oversized", "read-error"),
    ],
)
def test_source_rejects_unsafe_or_unbounded_files(tmp_path: Path, kind: str, reason: str) -> None:
    """The fixed script path inherits descriptor protections and a text bound."""
    home = tmp_path / "learner"
    (home / "scripts").mkdir(parents=True)
    script = home / "scripts/site-check.sh"
    match kind:
        case "directory":
            script.mkdir()
        case "fifo":
            os.mkfifo(script)
        case "escape":
            outside = tmp_path / "outside.sh"
            outside.write_text(_SENTINEL, encoding="utf-8")
            script.symlink_to(outside)
        case "binary":
            script.write_bytes(b"\0" + _SENTINEL.encode())
        case "invalid-utf8":
            script.write_bytes(b"\xff" + _SENTINEL.encode())
        case "oversized":
            script.write_bytes(b"#" * (1024 * 1024 + 1))
        case _:
            pass
    with pytest.raises(SiteCheckError, match=f"^{reason}$") as failure:
        read_site_check_source(
            "learner",
            account_lookup=lambda handle: UnixAccount(
                handle=handle, user_id=4242, home_directory=home
            ),
        )
    assert _SENTINEL not in str(failure.value)


def test_source_accepts_in_home_symlink_and_exact_limit(tmp_path: Path) -> None:
    """A safe symlink remains supported and the byte limit is inclusive."""
    (tmp_path / "scripts").mkdir()
    source = b"#" * (1024 * 1024)
    (tmp_path / "checker.sh").write_bytes(source)
    (tmp_path / "scripts/site-check.sh").symlink_to(tmp_path / "checker.sh")
    assert (
        read_site_check_source(
            "learner",
            account_lookup=lambda handle: UnixAccount(
                handle=handle, user_id=4242, home_directory=tmp_path
            ),
        )
        == source
    )
