"""Bounded source reads and the source-free S6 outcome report contract.

Reports contain only a source digest, fixed case identifiers, booleans, and a
fixed error token. JSON transports must reject duplicate keys before parsing.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import cast

from maker_guide.validation_paths import (
    UnixAccountLookup,
    lookup_unix_account,
    open_validation_file,
)

SITE_CHECK_CASES = (
    "both-ok",
    "report-missing",
    "homepage-missing",
    "http-error",
    "homepage-connection-failed",
    "report-connection-failed",
    "misleading-status",
)
SITE_CHECK_TIMEOUT_SECONDS = 25.0
_SOURCE_LIMIT = 1024 * 1024
_ERROR_FEEDBACK = {
    "syntax-error": "Fix the Bash syntax in ~/scripts/site-check.sh (use bash -n).",
    "timeout": "Make site-check.sh finish promptly, with bounded curl requests.",
    "output-limit": "Reduce site-check.sh output to brief diagnoses for both pages.",
    "script-changed": "The script changed during checking; rerun the check.",
    "unsafe-user": "Run the check from your own learner account, without sudo.",
    "runner-unavailable": "The local checker is unavailable; ask a mentor for help.",
    "unreadable-script": "Keep ~/scripts/site-check.sh readable, plain text, and at most 1 MiB.",
}
_CASE_FEEDBACK = {
    "both-ok": "Check both pages without arguments and identify each HTTP 200 success.",
    "report-missing": (
        "Handle a missing report. The test makes maker-report.html return HTTP 404. "
        "Print that it is missing and advise running `maker-report.sh`, then `build-website`. "
        "See S6 Exercise 4; do not delete your real report."
    ),
    "homepage-missing": (
        "Handle a missing homepage. The test returns HTTP 404 for the homepage, not the report. "
        "Identify the failed page without advising report regeneration."
    ),
    "http-error": (
        "Handle a server error. The test returns HTTP 500 for the report. "
        "Print that status without reporting success."
    ),
    "homepage-connection-failed": (
        "Handle a failed homepage request without stopping the script. "
        "Print a connection-failure message, then still check the report. See S6 Exercise 5."
    ),
    "report-connection-failed": (
        "Handle a failed report request: print a connection-failure message and make sure "
        "the homepage is checked too. See S6 Exercise 5."
    ),
    "misleading-status": (
        "Check curl's exit status before reporting success. This test prints 200 but makes "
        "curl exit nonzero, so the request must be reported as failed. See S6 Exercise 5."
    ),
}


@dataclass(frozen=True, kw_only=True, slots=True)
class SiteCheckReport:
    """Source-bound, source-free results of the learner-side fixture suite."""

    source_sha256: str
    cases: tuple[tuple[str, bool], ...]
    error: str | None = None


class SiteCheckError(ValueError):
    """A fixed failure reason, never source text or an untrusted report value."""

    def __init__(self, reason: str = "invalid-report") -> None:
        if reason not in _ERROR_FEEDBACK and reason not in {
            "invalid-report",
            "unknown-user",
            "unsafe-path",
            "path-escapes-scope",
            "missing-path",
            "broken-symlink",
            "symlink-loop",
            "permission-denied",
            "read-error",
            "not-regular-file",
        }:
            reason = "invalid-report"
        super().__init__(reason)


def read_site_check_source(
    handle: str,
    *,
    account_lookup: UnixAccountLookup = lookup_unix_account,
) -> bytes:
    """Read at most 1 MiB of regular UTF-8 text within the learner's home.

    Path failures retain the existing validation-path reason. Oversized or
    non-text content uses ``read-error``; source bytes never enter an error.
    """
    opened_file = open_validation_file(
        handle, "~/scripts/site-check.sh", account_lookup=account_lookup
    )
    if opened_file.failure_reason is not None:
        raise SiteCheckError(opened_file.failure_reason)
    if opened_file.file_descriptor is None:
        raise SiteCheckError("read-error")
    try:
        with os.fdopen(opened_file.file_descriptor, "rb") as source_file:
            source = source_file.read(_SOURCE_LIMIT + 1)
        if len(source) > _SOURCE_LIMIT or any(
            character < 32 and character not in b"\t\n\r" for character in source
        ):
            raise SiteCheckError("read-error")
        source.decode("utf-8")
    except (OSError, UnicodeError):
        raise SiteCheckError("read-error") from None
    return source


def parse_site_check_report(value: object, expected_digest: str) -> SiteCheckReport:
    """Strictly validate a decoded wire report without quoting rejected values."""
    if not isinstance(value, dict):
        raise SiteCheckError("invalid-report")
    payload = cast("dict[object, object]", value)
    if set(payload) != {"version", "source_sha256", "cases", "error"}:
        raise SiteCheckError("invalid-report")
    if type(payload["version"]) is not int or payload["version"] != 1:
        raise SiteCheckError("invalid-report")
    digest = payload["source_sha256"]
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or digest != expected_digest
    ):
        raise SiteCheckError("invalid-report")
    if not isinstance(payload["cases"], dict):
        raise SiteCheckError("invalid-report")
    cases = cast("dict[object, object]", payload["cases"])
    if set(cases) != set(SITE_CHECK_CASES) or any(
        type(result) is not bool for result in cases.values()
    ):
        raise SiteCheckError("invalid-report")
    error = payload["error"]
    if error is not None and (not isinstance(error, str) or error not in _ERROR_FEEDBACK):
        raise SiteCheckError("invalid-report")
    return SiteCheckReport(
        source_sha256=digest,
        cases=tuple((case, cast("bool", cases[case])) for case in SITE_CHECK_CASES),
        error=error,
    )


def site_check_report_payload(report: SiteCheckReport) -> dict[str, object]:
    """Serialize the fixed report schema, never captured source or output."""
    payload: dict[str, object] = {
        "version": 1,
        "source_sha256": report.source_sha256,
        "cases": dict(report.cases),
        "error": report.error,
    }
    if len(report.cases) != len(SITE_CHECK_CASES):
        raise SiteCheckError("invalid-report")
    parse_site_check_report(payload, report.source_sha256)
    return payload


def site_check_failure_messages(report: SiteCheckReport) -> tuple[str, ...]:
    """Return only fixed, actionable feedback, with runner errors taking priority."""
    if report.error is not None:
        return (_ERROR_FEEDBACK.get(report.error, _ERROR_FEEDBACK["runner-unavailable"]),)
    return tuple(
        _CASE_FEEDBACK.get(case, _ERROR_FEEDBACK["runner-unavailable"])
        for case, passed in report.cases
        if not passed
    )
