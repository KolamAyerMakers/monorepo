"""Exercise real curl fixtures only under the real, unprivileged test UID."""

from __future__ import annotations

import contextlib
import hashlib
import json
import multiprocessing
import os
import pwd
import signal
import time
from functools import partial
from importlib.resources import files
from pathlib import Path

import pytest

from maker_guide.cli import site_check as runner
from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SiteCheckError,
    read_site_check_source,
    site_check_failure_messages,
    site_check_report_payload,
)
from maker_guide.validation_paths import UnixAccount

_SENTINEL = "private-output-sentinel"
_EQUIVALENT_SCRIPT = r"""set -uo pipefail
root="https://lf-dev.kolamayermakers.org/~$(id -un)"
probe() {
    local endpoint="$1" label="$2" observed outcome=0
    observed=$(curl --url "$endpoint" --write-out '%{http_code}' --output /dev/null \
        --silent --show-error --head --max-time 2) || outcome=$?
    if (( outcome != 0 )); then
        printf '%s: connection failure\n' "$label"
        return 1
    elif [[ "$observed" == 200 ]]; then
        printf '%s: hTtP 200 sUcCeSs\n' "$label"
    elif [[ "$observed" == 404 ]]; then
        printf '%s: not found, HTTP 404\n' "$label"
        if [[ "${label,,}" == report ]]; then
            printf 'Generate with maker-report.sh, then publish with build-website\n'
        fi
        return 1
    else
        printf '%s: unexpected HTTP %s\n' "$label" "$observed"
        return 1
    fi
}
failed=0
probe "$root/maker-report.html" RePoRt || failed=1
probe "$root/" HoMePaGe || failed=1
exit "$failed"
"""
_URL_WRITEOUT_SCRIPT = r"""set -uo pipefail
for page in maker-report.html ""; do
    url="https://lf-dev.kolamayermakers.org/~$USER/$page"
    capture_file="$HOME/$url.headers"
    mkdir -p "$(dirname "$capture_file")"
    outcome=0
    result=$(curl CURL_OPTIONS --max-time 2 "$url") || outcome=$?
    if (( outcome != 0 )); then
        printf '%s: connection refused; HTTP200 ignored\n' "$url"
    elif [[ "$result" == *HTTP200 ]]; then
        printf '%s OK, no errors\n' "$result"
    else
        printf '%s\n' "$result"
        printf 'Missing page or server error\n'
        if [[ "$page" == maker-report.html && "$result" == *HTTP404 ]]; then
            printf 'Run maker-report.sh then build-website to bring the report back up\n'
        fi
    fi
done
"""


@pytest.fixture
def learner_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep real UID checks intact; redirect only the account's test home."""
    try:
        account = runner._learner_account()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    except SiteCheckError:
        pytest.skip("Native script tests require a real non-root, non-bot learner UID")
    if not Path("/usr/bin/curl").is_file():
        pytest.skip("Native fixture tests require /usr/bin/curl")
    test_account = pwd.struct_passwd(
        (
            account.pw_name,
            account.pw_passwd,
            account.pw_uid,
            account.pw_gid,
            account.pw_gecos,
            str(tmp_path),
            account.pw_shell,
        )
    )

    def learner_account_lookup(_user_id: int) -> pwd.struct_passwd:
        return test_account

    monkeypatch.setattr(runner.pwd, "getpwuid", learner_account_lookup)
    monkeypatch.setattr(
        runner,
        "read_site_check_source",
        partial(
            read_site_check_source,
            account_lookup=lambda handle: UnixAccount(
                handle=handle, user_id=account.pw_uid, home_directory=tmp_path
            ),
        ),
    )
    (tmp_path / "scripts").mkdir()
    return tmp_path / "scripts/site-check.sh"


@pytest.mark.parametrize(
    "variant",
    [
        "reference",
        "renamed-report-first",
        "head-pipeline",
        "positional-url",
        "url-writeout",
        "url-writeout-long",
        "url-writeout-combined",
    ],
)
def test_equivalent_checkers_pass_all_outcomes(learner_script: Path, variant: str) -> None:
    """Variable names, functions, letter case, page/flag order and HEAD parsing may vary."""
    source = _EQUIVALENT_SCRIPT
    if variant == "reference":
        source = (
            files("maker_guide.curriculum")
            .joinpath("content/lf2607/mentors/s06-solutions/site-check.sh")
            .read_text(encoding="utf-8")
        )
    elif variant == "head-pipeline":
        source = source.replace(
            "curl --url \"$endpoint\" --write-out '%{http_code}' --output /dev/null \\\n"  # noqa: ISC003 - explicit concatenation required by Basedpyright
            + "        --silent --show-error --head --max-time 2",
            "curl \"$endpoint\" --max-time 2 -sSI | awk 'NR == 1 {print $2}'",
        )
    elif variant == "positional-url":
        source = source.replace('--url "$endpoint"', '"$endpoint"').replace(
            "Generate with maker-report.sh, then publish with build-website",
            "Before build-website, regenerate with maker-report.sh",
        )
    elif variant.startswith("url-writeout"):
        source = _URL_WRITEOUT_SCRIPT.replace(
            "CURL_OPTIONS",
            {
                "url-writeout": (
                    '-sSI -w "$url HTTP%{http_code}" -o "$capture_file" '
                    '-H "Link: <$url>" -A "$url" -e "$url"'
                ),
                "url-writeout-long": (
                    '--silent --show-error --head --write-out "$url HTTP%{http_code}" '
                    '--output "$capture_file" --header "Link: <$url>" '
                    '--user-agent "$url" --referer "$url"'
                ),
                "url-writeout-combined": (
                    '-4sSIw"$url HTTP%{http_code}" -o"$capture_file" '
                    '-H"Link: <$url>" -A"$url" -e"$url"'
                ),
            }[variant],
        )
    learner_script.write_text(source, encoding="utf-8")
    report = runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
    assert report.error is None
    assert dict(report.cases) == dict.fromkeys(SITE_CHECK_CASES, True)


@pytest.mark.parametrize(
    ("variant", "failed_case"),
    [
        ("one-page", "report-missing"),
        ("unconditional", "report-missing"),
        ("abort-first", "report-missing"),
        ("bypass", "report-missing"),
        ("wrong-user", "report-missing"),
        ("extra-url", "both-ok"),
        ("bare-extra-url", "both-ok"),
        ("ignore-exit", "misleading-status"),
    ],
)
def test_incomplete_or_unobserved_checks_fail(
    learner_script: Path, variant: str, failed_case: str
) -> None:
    """Checking source-like text or one page cannot substitute for actual outcomes."""
    source = _EQUIVALENT_SCRIPT
    match variant:
        case "one-page":
            source = source.replace('probe "$root/" HoMePaGe || failed=1', "")
        case "unconditional":
            source = r"""for page in "" maker-report.html; do
    curl -sSI -o /dev/null "https://lf2607.kolamayermakers.org/~$USER/$page"
    printf 'SUCCESS: https://lf2607.kolamayermakers.org/~%s/%s HTTP 200\n' "$USER" "$page"
done
"""
        case "abort-first":
            source = "set -e\n" + source.replace(" || failed=1", "")
        case "bypass":
            source = "curl() { printf 200; }\n" + source
        case "wrong-user":
            source = source.replace("~$(id -un)", "~not-the-actual-learner")
        case "extra-url" | "bare-extra-url":
            source = source.replace(
                'curl --url "$endpoint"',
                'curl --url "$endpoint" '
                + ("http://" if variant == "extra-url" else "")
                + "127.0.0.1:9/homepage",
            )
        case "ignore-exit":
            source = source.replace(
                "if (( outcome != 0 )); then", 'if [[ "$observed" == 000 ]]; then'
            )
        case _:
            raise AssertionError(variant)
    learner_script.write_text(source, encoding="utf-8")
    report = runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
    assert report.error is None
    assert not dict(report.cases)[failed_case]
    if variant in {"unconditional", "abort-first", "ignore-exit"}:
        assert dict(report.cases)["both-ok"]
    else:
        assert not any(passed for _case, passed in report.cases)


@pytest.mark.parametrize(
    ("ending", "expected_error"),
    [
        ("wait", "timeout"),
        (f"while :; do printf '{_SENTINEL}\\n'; done", "output-limit"),
        ("exit 0", None),
        ("SIGTERM", None),
        ("SIGHUP", None),
    ],
)
def test_output_bounds_and_descendant_cleanup(
    learner_script: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    ending: str,
    expected_error: str | None,
) -> None:
    """Bounds and supervisor termination leave no live children or leaked output."""
    termination_signal = {"SIGTERM": signal.SIGTERM, "SIGHUP": signal.SIGHUP}.get(ending)
    monkeypatch.setattr(runner, "_CASE_TIMEOUT_SECONDS", 10 if termination_signal else 0.5)
    source = (
        'printf \'%s\\n\' "$$" >> "$HOME/groups"\n'
        'sleep 30 >/dev/null 2>&1 &\nprintf \'%s\\n\' "$!" >> "$HOME/children"\n'
        f"printf '{_SENTINEL}\\n'\nprintf '{_SENTINEL}\\n' >&2\n"
        f"{'wait' if termination_signal else ending}\n"
    )
    learner_script.write_text(source, encoding="utf-8")
    children = learner_script.parent.parent / "children"
    previous_handlers = {
        received_signal: signal.getsignal(received_signal)
        for received_signal in (signal.SIGTERM, signal.SIGHUP)
    }
    serialized_report = ""
    if termination_signal is not None:
        restored = learner_script.parent.parent / "handlers-restored"

        def supervised_run() -> None:
            try:
                runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
            finally:
                restored.write_text(
                    str(
                        all(
                            signal.getsignal(received_signal) == handler
                            for received_signal, handler in previous_handlers.items()
                        )
                    ),
                    encoding="utf-8",
                )

        supervisor = multiprocessing.get_context("fork").Process(target=supervised_run)
        supervisor.start()
        try:
            deadline = time.monotonic() + 5
            while not children.exists() or not children.read_text(encoding="utf-8").endswith("\n"):
                assert time.monotonic() < deadline, "Learner child did not start"
                time.sleep(0.01)
            assert supervisor.pid is not None
            os.kill(supervisor.pid, termination_signal)
            supervisor.join(timeout=5)
            assert supervisor.exitcode == 128 + termination_signal
            assert restored.read_text(encoding="utf-8") == "True"
            _assert_children_stopped(children)
        finally:
            if supervisor.is_alive():
                supervisor.kill()
            supervisor.join(timeout=5)
            # Clean up even when a regression has orphaned a learner process group.
            groups = learner_script.parent.parent / "groups"
            if groups.exists():
                for process_id in groups.read_text(encoding="utf-8").splitlines():
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(int(process_id), signal.SIGKILL)
    else:
        report = runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
        assert report.error == expected_error
        _assert_children_stopped(children)
        serialized_report = (
            json.dumps(site_check_report_payload(report))
            + str(report)
            + " ".join(site_check_failure_messages(report))
        )
    assert all(
        signal.getsignal(received_signal) == handler
        for received_signal, handler in previous_handlers.items()
    )
    captured = capfd.readouterr()
    assert _SENTINEL not in serialized_report + captured.out + captured.err


def _assert_children_stopped(children: Path) -> None:
    for process_id in children.read_text(encoding="utf-8").splitlines():
        process_status = Path(f"/proc/{process_id}/stat")
        deadline = time.monotonic() + 1
        while process_status.exists():
            try:
                state = process_status.read_text(encoding="utf-8").split()[2]
            except FileNotFoundError:
                break
            if state == "Z":
                break
            assert time.monotonic() < deadline, "Fixture child survived process-group cleanup"
            time.sleep(0.01)


def test_clean_environment_and_no_script_arguments(
    learner_script: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Caller startup hooks, credentials and identity variables are not inherited."""
    for name in ("BASH_ENV", "PYTHONPATH", "API_TOKEN", "USER", "LOGNAME", "HOME"):
        monkeypatch.setenv(name, _SENTINEL)
    source = (
        r"""[[ $# == 0 && "$USER" == "$(id -un)" && "$LOGNAME" == "$USER" ]] || exit 90
[[ -z ${BASH_ENV+x} && -z ${PYTHONPATH+x} && -z ${API_TOKEN+x} ]] || exit 91
[[ -d "$HOME/scripts" ]] || exit 92
[[ $(stat -c %a .) == 700 && $(stat -Lc %a "$0") == 400 ]] || exit 93
[[ $(stat -Lc %h "$0") == 0 && $(stat -Lc %u "$0") == "$(id -u)" ]] || exit 94
"""
        + _EQUIVALENT_SCRIPT
    )
    learner_script.write_text(source, encoding="utf-8")
    report = runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
    assert report.error is None
    assert all(passed for _case, passed in report.cases)


@pytest.mark.parametrize(
    ("source", "expected_error"),
    [
        ("if\n", "syntax-error"),
        (
            'printf "exit 0\\n" > "$HOME/scripts/site-check.sh"; printf run >> "$HOME/runs"\n',
            "script-changed",
        ),
    ],
)
def test_syntax_and_source_changes_fail_closed(
    learner_script: Path, source: str, expected_error: str
) -> None:
    """Execution uses the validated snapshot, and later edits invalidate the report."""
    learner_script.write_text(source, encoding="utf-8")
    report = runner.run_site_check(hashlib.sha256(source.encode()).hexdigest())
    assert report.error == expected_error
    if expected_error == "script-changed":
        assert (learner_script.parent.parent / "runs").read_text(encoding="utf-8") == "run" * len(
            SITE_CHECK_CASES
        )


def test_stale_digest_prevents_subprocess_execution(
    learner_script: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A report cannot certify a different script than the requested digest."""
    learner_script.write_text(_EQUIVALENT_SCRIPT, encoding="utf-8")

    def unexpected_execution(*_arguments: object, **_keywords: object) -> None:
        raise AssertionError("A stale source must not execute")

    monkeypatch.setattr(runner, "_run_bash", unexpected_execution)
    assert runner.run_site_check("0" * 64).error == "script-changed"


@pytest.mark.parametrize("identity", ["root", "uid-mismatch", "bot"])
def test_unsafe_identity_never_starts_a_subprocess(
    monkeypatch: pytest.MonkeyPatch, identity: str
) -> None:
    """These mocked-identity tests must refuse before any native execution."""
    monkeypatch.setattr(runner.os, "getuid", lambda: 0 if identity == "root" else 4242)
    monkeypatch.setattr(runner.os, "geteuid", lambda: 4343 if identity == "uid-mismatch" else 4242)

    def bot_account_lookup(_user_id: int) -> pwd.struct_passwd:
        return pwd.struct_passwd(
            ("maker-guide", "x", 4242, 4242, "", "/var/lib/maker-guide", "/bin/bash")
        )

    monkeypatch.setattr(runner.pwd, "getpwuid", bot_account_lookup)

    def unexpected_execution(*_arguments: object, **_keywords: object) -> None:
        raise AssertionError("Unsafe identity reached subprocess execution")

    monkeypatch.setattr(runner.subprocess, "Popen", unexpected_execution)
    assert runner.run_site_check("0" * 64).error == "unsafe-user"


def test_url_identity_does_not_confuse_page_attribution() -> None:
    """Words in a learner handle must not decide which page a URL identifies."""
    assert runner._passed_output(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        """https://lf2607.kolamayermakers.org/~report-home-user/ HTTP 200
https://lf2607.kolamayermakers.org/~report-home-user/maker-report.html HTTP 200
""",
        "both-ok",
        "report-home-user",
    )


@pytest.mark.parametrize(
    ("case", "output", "passed"),
    [
        (
            "both-ok",
            "Homepage: HTTP200 OK, no errors\nReport: HTTP200 OK, no errors\n",
            True,
        ),
        (
            "homepage-missing",
            "Homepage: HTTP404 missing; the report is unaffected\nReport: HTTP200\n",
            True,
        ),
        ("http-error", "Homepage\n200\nReport\nHTTP500\nServer error\n", True),
        (
            "report-missing",
            """Homepage: 200
Report: 404
Run maker-report.sh then build-website to bring the report back up
""",
            True,
        ),
        (
            "misleading-status",
            "Homepage: 200\nReport: connection refused; HTTP200 ignored\n",
            True,
        ),
        (
            "report-connection-failed",
            "Homepage: HTTP200\ncurl: (52) Empty reply from server\nReport: connection failed\n",
            True,
        ),
        (
            "http-error",
            """Homepage: HTTP200
curl: (22) The requested URL returned error: 500
Report: HTTP500
""",
            True,
        ),
        (
            "homepage-missing",
            "Homepage: 404\nReport: 200\nmaker-report.sh output is published\n",
            True,
        ),
        (
            "report-missing",
            "Homepage: 200\nReport: 404\nDo not run maker-report.sh or build-website\n",
            False,
        ),
        (
            "report-missing",
            "Homepage: 200\nRun maker-report.sh then build-website\nReport: 404\n",
            False,
        ),
        (
            "homepage-missing",
            "Homepage: 404\nDo not run maker-report.sh\nReport: 200\n",
            True,
        ),
        (
            "homepage-missing",
            "Homepage: 404\nRun maker-report.sh then build-website\nReport: 200\n",
            False,
        ),
        ("both-ok", "Homepage: HTTP200 OK\nConnection failed\nReport: 200\n", False),
        (
            "misleading-status",
            "Homepage: 200\nReport: connection failed; HTTP200 SUCCESS\n",
            False,
        ),
        ("report-missing", "Homepage: 200\nReport: 404\n", False),
        (
            "report-missing",
            "Homepage: 200\nReport: 404\n~/scripts/maker-report.sh 'Report'\nbuild-website\n",
            True,
        ),
        (
            "report-missing",
            "Homepage: 200\nReport: HTTP404. Run maker-report.sh then build-website\n",
            True,
        ),
    ],
)
def test_page_records_accept_simple_outputs_without_copying_layout(
    case: str, output: str, passed: bool
) -> None:
    """Page evidence, positive repair advice and contradictory outcomes stay distinct."""
    assert (
        runner._passed_output(output, case, "learner")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        is passed
    )
