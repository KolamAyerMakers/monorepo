"""Run S6 outcome fixtures locally, exclusively as the invoking learner.

Output matching uses page labels, headings, or URLs, not a prescribed layout.
Page records must show the observed HTTP code, or explain a transport failure
without claiming success. Report 404 needs positive advice to run maker-report.sh
and build-website; homepage 404 must not prompt report regeneration. Matching is
case-insensitive; diagnoses and advice can span lines and pages can appear in
either order. This recognizes simple observable output, not arbitrary prose.

The PATH shim preserves real curl option handling and redirects only the two
learner URLs on lf2607 or lf-dev to loopback fixtures. Observed fixture requests
are required for both pages. This is not a sandbox: scripts retain the learner's
permissions, and deliberate PATH bypasses are not prevented. Never invoke this
runner in the bot, as root, or remotely on behalf of a learner.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import pwd
import re
import selectors
import shlex
import signal
import socket
import subprocess
import tempfile
import time
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread, current_thread, main_thread
from types import FrameType
from typing import NoReturn, cast, override

from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SITE_CHECK_TIMEOUT_SECONDS,
    SiteCheckError,
    SiteCheckReport,
    read_site_check_source,
)

_OUTPUT_LIMIT = 64 * 1024
_CASE_TIMEOUT_SECONDS = 3.0
_STATUS = re.compile(r"\b(?:http\s*)?(?P<status>[1-5]\d\d)\b")
_SUCCESS = re.compile(
    r"(?<!not )(?<!no )\b(?:ok|success\w*|healthy|available|reachable|working|passed)\b"
)
_FAILURE = re.compile(
    r"\b(?:error\w*|fail\w*|connect\w*|dns|tls|timeout\w*|timed out|certificate|network)\b"
)
_NEGATIVE = re.compile(
    r"\b(?:missing|not found|not ok|error\w*|fail\w*|unavailable|unexpected|bad|timeout|"  # noqa: ISC003 - explicit concatenation required by Basedpyright
    + r"timed out|refused|unreachable)\b"
)
_ADVICE = re.compile(
    r"\b(?:run|use|generate|regenerate|rebuild|publish|build|try)\s|"  # noqa: ISC003 - explicit concatenation required by Basedpyright
    + r"^(?:bash\s+|sh\s+|~/|\./|/)|"
    + r"^(?:maker-report\.sh|build-website)(?:\s*[.!]?$|\s+[\"'])"
)
_CURL_SHIM = r"""#!/bin/bash
learner=ACTUAL_LEARNER
arguments=()
observed=0
report_requested=0
next_value=
operands_only=0
for argument in "$@"; do
    if [[ "$next_value" == data ]]; then
        arguments+=("$argument")
        next_value=
        continue
    fi
    prefix=
    value="$argument"
    if [[ "$next_value" != url && "$operands_only" == 0 ]]; then
        case "$argument" in
            --) operands_only=1; arguments+=("$argument"); continue ;;
            --url) next_value=url; arguments+=("$argument"); continue ;;
            --url=*) prefix=--url=; value="${argument#--url=}" ;;
            --write-out|--output|--header|--user-agent|--referer|--max-time|\
            --connect-timeout|--retry|--retry-delay|--retry-max-time|--request)
                next_value=data; arguments+=("$argument"); continue ;;
            --config|--config=*|--next) exit 2 ;;
            --*) arguments+=("$argument"); continue ;;
            -?*)
                # Only shield common option data; native curl still parses the options.
                [[ "$argument" =~ ^-[aBfgGiIjJklLMnNOpqRsSvV012346#]*[K:] ]] && exit 2
                if [[ "$argument" =~ ^-[aBfgGiIjJklLMnNOpqRsSvV012346#]*[woHAemX](.*)$ ]]; then
                    [[ -n "${BASH_REMATCH[1]}" ]] || next_value=data
                fi
                arguments+=("$argument"); continue ;;
        esac
    fi
    next_value=
    case "$value" in
        "https://lf2607.kolamayermakers.org/~$learner"|\
        "https://lf2607.kolamayermakers.org/~$learner/"|\
        "https://lf-dev.kolamayermakers.org/~$learner"|\
        "https://lf-dev.kolamayermakers.org/~$learner/")
            value=FIXTURE_ORIGIN/homepage
            observed=1
            ;;
        "https://lf2607.kolamayermakers.org/~$learner/maker-report.html"|\
        "https://lf-dev.kolamayermakers.org/~$learner/maker-report.html")
            value=FIXTURE_ORIGIN/report
            observed=1
            report_requested=1
            ;;
        *://*) exit 2 ;;
    esac
    arguments+=("$prefix$value")
done
[[ "$observed" == 1 ]] || exit 2
# Keep other operand forms on loopback too; their Host will not match the fixture.
/usr/bin/curl -q --proto '=http' --proto-redir '=http' \
    --noproxy '*' --connect-to FIXTURE_CONNECT "${arguments[@]}"
curl_status=$?
if [[ MISLEADING_STATUS == 1 && "$report_requested" == 1 ]]; then
    exit 28
fi
exit "$curl_status"
"""


class _FixtureServer(HTTPServer):
    def __init__(self, case: str) -> None:
        self.case: str = case
        self.observed: set[str] = set()
        self.unexpected: bool = False
        super().__init__(("127.0.0.1", 0), _FixtureHandler)

    @override
    def get_request(self) -> tuple[socket.socket, tuple[str, int]]:
        connection, address = cast("tuple[socket.socket, tuple[str, int]]", super().get_request())
        connection.settimeout(0.2)
        return connection, address

    @override
    def handle_error(self, request: object, client_address: object) -> None:
        # HTTPServer's default handler prints exception details to stderr.
        self.unexpected = True


class _FixtureHandler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self._respond()

    def do_GET(self) -> None:
        self._respond()

    def _respond(self) -> None:
        fixture = cast("_FixtureServer", self.server)
        page = self.path.removeprefix("/")
        if (
            page not in {"homepage", "report"}
            or self.headers.get("Host") != f"127.0.0.1:{fixture.server_port}"
        ):
            fixture.unexpected = True
            self.send_error(404)
            return
        fixture.observed.add(page)
        if fixture.case == f"{page}-connection-failed":
            self.close_connection = True
            return
        status = 200
        if fixture.case == f"{page}-missing":
            status = 404
        elif fixture.case == "http-error" and page == "report":
            status = 500
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    @override
    def log_message(self, format: str, *arguments: object) -> None:
        """Never expose request data or learner output through server logging."""


@contextlib.contextmanager
def _termination_cleanup() -> Generator[None]:
    """Turn supervisor termination into unwinding, then restore caller handlers."""
    if current_thread() is not main_thread():
        raise SiteCheckError("runner-unavailable")
    previous = {
        received_signal: signal.getsignal(received_signal)
        for received_signal in (signal.SIGTERM, signal.SIGHUP)
    }

    def terminate(received_signal: int, _frame: FrameType | None) -> NoReturn:
        # A second termination request must not interrupt process-group cleanup.
        for termination_signal in previous:
            signal.signal(termination_signal, signal.SIG_IGN)
        raise SystemExit(128 + received_signal)

    try:
        for received_signal in previous:
            signal.signal(received_signal, terminate)
        yield
    finally:
        for received_signal, handler in previous.items():
            signal.signal(received_signal, handler)


def _learner_account() -> pwd.struct_passwd:
    if os.getuid() == 0 or os.getuid() != os.geteuid():
        raise SiteCheckError("unsafe-user")
    try:
        account = pwd.getpwuid(os.getuid())
    except KeyError:
        raise SiteCheckError("unsafe-user") from None
    if (
        account.pw_uid != os.getuid()
        or account.pw_name in {"maker-guide", "maker-guide-bot"}
        or account.pw_dir == "/var/lib/maker-guide"
    ):
        raise SiteCheckError("unsafe-user")
    with contextlib.suppress(OSError):
        if Path("/run/maker-guide/preexec.sock").stat().st_uid == account.pw_uid:
            raise SiteCheckError("unsafe-user")
    return account


def _run_bash(
    source_descriptor: int,
    directory: Path,
    environment: dict[str, str],
    deadline: float,
    *,
    syntax_only: bool = False,
) -> tuple[int, str]:
    """Drain bounded output in memory and kill the child group while unwinding."""
    _learner_account()
    os.lseek(source_descriptor, 0, os.SEEK_SET)
    with subprocess.Popen(  # noqa: S603 - intentional learner-owned script execution
        ["/bin/bash", *(["-n"] if syntax_only else []), f"/proc/self/fd/{source_descriptor}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=directory,
        env=environment,
        close_fds=True,
        pass_fds=(source_descriptor,),
        start_new_session=True,
    ) as process:
        output = bytearray()
        try:
            if process.stdout is None:
                raise SiteCheckError("runner-unavailable")
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise SiteCheckError("timeout")
                    for selected, _events in selector.select(remaining):
                        chunk = os.read(selected.fd, 8192)
                        if not chunk:
                            selector.unregister(selected.fd)
                            continue
                        if len(output) + len(chunk) > _OUTPUT_LIMIT:
                            raise SiteCheckError("output-limit")
                        output.extend(chunk)
                try:
                    exit_status = process.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    raise SiteCheckError("timeout") from None
        finally:
            # Even a completed parent can leave children holding pipes or running.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    return exit_status, output.decode("utf-8", errors="replace")


def _passed_output(output: str, case: str, handle: str) -> bool:  # noqa: C901, PLR0912
    diagnoses: dict[str, list[str]] = {"homepage": [], "report": []}
    repairs: dict[str, set[str]] = {"homepage": set(), "report": set()}
    current_page: str | None = None
    for record in re.split(r"[\n;]|&&", output.lower()):
        line = record.strip()
        if line.startswith("curl:"):
            continue
        label = re.match(
            r"(?:(?:ok|missing|check|connection failed|error)\s*:\s*)?"  # noqa: ISC003 - explicit concatenation required by Basedpyright
            + r"(?P<page>home(?:\s*page)?|report|maker-report\.html)\b[:\s]*",
            line,
        )
        page_url = re.search(
            "".join(
                (
                    r"https://(?:lf2607|lf-dev)\.kolamayermakers\.org/",
                    rf"~{re.escape(handle.lower())}(?P<page>/maker-report\.html|/?)",
                    r"(?=[\s:),\]\"']|$)",
                )
            ),
            line,
        )
        if label is not None:
            current_page = "homepage" if label["page"].startswith("home") else "report"
            line = line[label.end() :]
        elif page_url is not None:
            current_page = "report" if page_url["page"] == "/maker-report.html" else "homepage"
        if page_url is not None:
            line = line.replace(page_url[0], "")
        commands = {command for command in ("maker-report.sh", "build-website") if command in line}
        advice = _ADVICE.search(line) if commands else None
        if advice is not None:
            if current_page is not None and not re.search(
                r"\b(?:do not|don't|never|not)\s+"  # noqa: ISC003 - explicit concatenation required by Basedpyright
                + r"(?:run|use|generate|regenerate|rebuild|publish|build|try)\b",
                line,
            ):
                repairs[current_page].update(commands)
            line = line[: advice.start()]
            if not (_STATUS.search(line) or _FAILURE.search(line)):
                continue
        if label is None and page_url is None and (_STATUS.search(line) or _FAILURE.search(line)):
            mention = re.search(r"\b(?P<page>home(?:\s*page)?|report)\b", line)
            if mention is not None:
                current_page = "homepage" if mention["page"].startswith("home") else "report"
        if current_page is not None:
            diagnoses[current_page].append(line)
    for page, lines in diagnoses.items():
        text = re.sub(
            r"\b(?:no|without)\s+(?:errors?|failures?|problems?)\b",
            "",
            "\n".join(lines),
        )
        text = re.sub(
            r"\b(?:http\s*)?200\s+(?:ignored|disregarded)\b|"  # noqa: ISC003 - explicit concatenation required by Basedpyright
            + r"\b(?:ignore|ignored|disregard|not)\s+(?:http\s*)?200\b",
            "",
            text,
        )
        statuses = set(_STATUS.findall(text))
        transport_failure = case == f"{page}-connection-failed" or (
            case == "misleading-status" and page == "report"
        )
        success_claim = _SUCCESS.search(text) is not None or "200" in statuses
        if transport_failure:
            if _FAILURE.search(text) is None or success_claim:
                return False
        elif case == f"{page}-missing" or (case == "http-error" and page == "report"):
            status = "500" if case == "http-error" else "404"
            if status not in statuses or success_claim:
                return False
        elif statuses != {"200"} or _NEGATIVE.search(text):
            return False
    if case == "report-missing":
        return {"maker-report.sh", "build-website"} <= repairs["report"]
    return case != "homepage-missing" or not any(
        "maker-report.sh" in commands for commands in repairs.values()
    )


def run_site_check(expected_digest: str) -> SiteCheckReport:  # noqa: C901, PLR0912, PLR0915
    """Run the fixed local suite, returning only booleans and static failures.

    Bash parses and executes the same unlinked, read-only source snapshot, with
    no script arguments. This does not attest against same-learner tampering.
    An unhealthy script exit status is not itself failure.
    The 25-second suite budget includes a three-second limit for each subprocess.
    Main-thread execution is required for temporary SIGTERM/SIGHUP cleanup.
    """
    if re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None:
        raise SiteCheckError("invalid-report")
    results = dict.fromkeys(SITE_CHECK_CASES, False)
    error: str | None = None
    source: bytes | None = None
    account: pwd.struct_passwd | None = None
    deadline = time.monotonic() + SITE_CHECK_TIMEOUT_SECONDS
    try:
        account = _learner_account()
        if not all(os.access(executable, os.X_OK) for executable in ("/bin/bash", "/usr/bin/curl")):
            raise SiteCheckError("runner-unavailable")  # noqa: TRY301 - report suite failure here
        try:
            source = read_site_check_source(account.pw_name)
        except SiteCheckError:
            raise SiteCheckError("unreadable-script") from None
        if hashlib.sha256(source).hexdigest() != expected_digest:
            raise SiteCheckError("script-changed")  # noqa: TRY301 - report suite failure here
        with (
            _termination_cleanup(),
            tempfile.TemporaryDirectory(prefix="site-check-") as temporary_directory,
        ):
            directory = Path(temporary_directory)
            environment = {
                "HOME": account.pw_dir,
                "USER": account.pw_name,
                "LOGNAME": account.pw_name,
                "PATH": f"{directory}:/usr/bin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
            }
            snapshot = directory / "source.sh"
            snapshot.write_bytes(source)
            snapshot.chmod(0o400)
            source_descriptor = os.open(snapshot, os.O_RDONLY | os.O_CLOEXEC)
            try:
                snapshot.unlink()
                status, _output = _run_bash(
                    source_descriptor,
                    directory,
                    environment,
                    min(deadline, time.monotonic() + _CASE_TIMEOUT_SECONDS),
                    syntax_only=True,
                )
                if status:
                    raise SiteCheckError("syntax-error")
                for case in SITE_CHECK_CASES:
                    with _FixtureServer(case) as fixture:
                        (directory / "curl").write_text(
                            _CURL_SHIM.replace(
                                "FIXTURE_ORIGIN",
                                shlex.quote(f"http://127.0.0.1:{fixture.server_port}"),
                            )
                            .replace("ACTUAL_LEARNER", shlex.quote(account.pw_name))
                            .replace("FIXTURE_CONNECT", f"::127.0.0.1:{fixture.server_port}")
                            .replace(
                                "MISLEADING_STATUS", "1" if case == "misleading-status" else "0"
                            ),
                            encoding="utf-8",
                        )
                        (directory / "curl").chmod(0o700)
                        worker = Thread(
                            target=fixture.serve_forever,
                            kwargs={"poll_interval": 0.01},
                            daemon=True,
                        )
                        worker.start()
                        try:
                            _status, output = _run_bash(
                                source_descriptor,
                                directory,
                                environment,
                                min(deadline, time.monotonic() + _CASE_TIMEOUT_SECONDS),
                            )
                        finally:
                            fixture.shutdown()
                            worker.join()
                        results[case] = (
                            fixture.observed == {"homepage", "report"}
                            and not fixture.unexpected
                            and _passed_output(output, case, account.pw_name)
                        )
            finally:
                os.close(source_descriptor)
    except SiteCheckError as failure:
        error = str(failure)
    except (OSError, ValueError):
        error = "runner-unavailable"
    if source is not None and account is not None:
        try:
            if read_site_check_source(account.pw_name) != source:
                error = "script-changed"
        except SiteCheckError:
            error = "script-changed"
    return SiteCheckReport(
        source_sha256=expected_digest,
        cases=tuple(results.items()),
        error=error,
    )
