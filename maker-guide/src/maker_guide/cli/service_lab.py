"""Learner-only S8 faults, with durable attempts and retained displaced unit inodes.

Only the installed course unit or generated public_html directory is displaced.
Sources and the shared proxy are never changed. This is not an attestation boundary
against the same Unix account, which owns both the unit and the private attempt records.
"""

# Safety failures must reach the local recovery or diagnostic boundary, not escape it.
# ruff: noqa: TRY301

from __future__ import annotations

import contextlib
import ctypes
import fcntl
import os
import pwd
import re
import selectors
import shlex
import signal
import stat
import subprocess
import time
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import cast

from maker_guide.service_lab import (
    SERVICE_LAB_SCENARIOS,
    SERVICE_LAB_TIMEOUT_SECONDS,
    ServiceLabAction,
    ServiceLabError,
    ServiceLabReport,
    service_lab_action_payload,
)

_UNIT = "site.service"
_STATE = ".local/state/maker-guide/service-lab"
_FILE_LIMIT = 16384
_PAGE_LIMIT = 1024 * 1024
_WRONG_INDEX = b"<!doctype html><h1>Welcome to the Department of Unexpected Websites</h1>\n"
_OMITTED_EMPTY_ARRAYS = (
    "EnvironmentFiles",
    "ExecStartPre",
    "ExecStartPost",
    "ExecStop",
    "ExecStopPost",
    "ExecReload",
    "ExecCondition",
)
_EMPTY_PROPERTIES = (
    *_OMITTED_EMPTY_ARRAYS,
    "DropInPaths",
    "Environment",
    "PassEnvironment",
    "UnsetEnvironment",
    "RootDirectory",
    "RootImage",
    "User",
    "Group",
)
_PROPERTIES = (
    *_EMPTY_PROPERTIES,
    "Id",
    "Names",
    "LoadState",
    "FragmentPath",
    "NeedDaemonReload",
    "Transient",
    "Type",
    "Restart",
    "WorkingDirectory",
    "ExecStart",
    "ActiveState",
    "SubState",
    "Result",
    "MainPID",
    "ExecMainCode",
    "ExecMainStatus",
    "ExecMainStartTimestampMonotonic",
)


def _account() -> pwd.struct_passwd:
    if os.getuid() == 0 or os.getuid() != os.geteuid() or os.getgid() != os.getegid():
        raise ServiceLabError("unsafe-user")
    try:
        account = pwd.getpwuid(os.getuid())
    except KeyError:
        raise ServiceLabError("unsafe-user") from None
    if (
        account.pw_uid != os.getuid()
        or account.pw_name in {"maker-guide", "maker-guide-bot"}
        or account.pw_dir == "/var/lib/maker-guide"
        or not 10000 < 10000 + account.pw_uid <= 65535
        or re.fullmatch(r"/[A-Za-z0-9_./-]+", account.pw_dir) is None
        or Path(account.pw_dir).as_posix() != account.pw_dir
        or ".." in Path(account.pw_dir).parts
    ):
        raise ServiceLabError("unsafe-user")
    with contextlib.suppress(FileNotFoundError):
        if Path("/run/maker-guide/preexec.sock").stat().st_uid == account.pw_uid:
            raise ServiceLabError("unsafe-user")
    return account


@contextlib.contextmanager
def _directory(path: Path, *, create: bool = False, private: bool = False) -> Generator[int]:
    """Pin each directory without following links, including ancestor components."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for component in path.parts[1:]:
            if component in {".", ".."}:
                raise ServiceLabError("unsafe-path")
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                else:
                    os.fsync(descriptor)
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
            metadata = os.fstat(descriptor)
            if metadata.st_uid not in {0, os.getuid()} or (
                metadata.st_mode & 0o022
                and not (metadata.st_uid == 0 and metadata.st_mode & stat.S_ISVTX)
            ):
                raise ServiceLabError("unsafe-path")
        metadata = os.fstat(descriptor)
        if (
            metadata.st_uid != os.getuid()
            or metadata.st_mode & (0o077 if private else 0o022)
            or Path(f"/proc/self/fd/{descriptor}").resolve(strict=True) != path
        ):
            raise ServiceLabError("unsafe-path")
        yield descriptor
    finally:
        os.close(descriptor)


def _read(directory: int, name: str, limit: int = _FILE_LIMIT) -> bytes:
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory
    )
    with os.fdopen(descriptor, "rb") as source:
        metadata = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
            or metadata.st_mode & 0o7022
            or metadata.st_size > limit
        ):
            raise ServiceLabError("unsafe-path")
        content = source.read(limit + 1)
    if len(content) > limit:
        raise ServiceLabError("output-limit")
    return content


def _write(
    directory: int, name: str, content: bytes, mode: int = 0o600, *, exclusive: bool = False
) -> None:
    """Publish private runner metadata, never the installed learner unit."""
    temporary = f".write-{uuid.uuid4().hex}"
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        mode,
        dir_fd=directory,
    )
    try:
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(content)
            destination.flush()
            os.fchmod(destination.fileno(), mode)
            os.fsync(destination.fileno())
        if exclusive:
            _move_no_replace(directory, temporary, directory, name)
        else:
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=directory)


def _recover_publication(directory: int, attempt: int) -> None:  # noqa: C901 - keep crash recovery and inode cleanup together
    """Restore a displaced snapshot only into a missing name; keep the displaced inode."""
    try:
        publication = _read(attempt, "pending-unit").decode("ascii")
    except FileNotFoundError:
        return
    if re.fullmatch(r"[0-9a-f]{32}", publication) is None:
        raise ServiceLabError("attempt-mismatch")
    candidate = f"candidate-{publication}.service"
    displaced = f"displaced-{publication}.service"
    recovered = f"recovered-{publication}.service"
    try:
        os.stat(_UNIT, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        try:
            contents = _read(attempt, displaced)
        except FileNotFoundError:
            # The process may have stopped before the rename. Do not invent an old unit.
            pass
        else:
            try:
                staged_contents = _read(attempt, recovered)
            except FileNotFoundError:
                _write(
                    attempt,
                    recovered,
                    contents,
                    stat.S_IMODE(os.stat(displaced, dir_fd=attempt, follow_symlinks=False).st_mode),
                )
            else:
                if staged_contents != contents:
                    raise ServiceLabError("unit-changed")
            with contextlib.suppress(FileExistsError):
                os.link(
                    recovered,
                    _UNIT,
                    src_dir_fd=attempt,
                    dst_dir_fd=directory,
                    follow_symlinks=False,
                )
    # Either publication or recovery can stop between linking and unlinking its staging name.
    for staged_name in (candidate, recovered):
        with contextlib.suppress(FileNotFoundError):
            current = os.stat(_UNIT, dir_fd=directory, follow_symlinks=False)
            staged = os.stat(staged_name, dir_fd=attempt, follow_symlinks=False)
            if (staged.st_dev, staged.st_ino) == (current.st_dev, current.st_ino):
                os.unlink(staged_name, dir_fd=attempt)
    os.fsync(directory)
    os.unlink("pending-unit", dir_fd=attempt)
    os.fsync(attempt)


def _publish_unit(
    directory: int,
    attempt: int,
    expected: bytes,
    replacement: bytes,
    mode: int,
) -> None:
    """Retain the actual displaced inode, then publish without overwriting an editor's save."""
    publication = uuid.uuid4().hex
    candidate = f"candidate-{publication}.service"
    displaced = f"displaced-{publication}.service"
    _write(attempt, candidate, replacement, mode)
    _write(attempt, "pending-unit", publication.encode("ascii"))
    try:
        os.rename(_UNIT, displaced, src_dir_fd=directory, dst_dir_fd=attempt)
        os.fsync(attempt)
        os.fsync(directory)
        if _read(attempt, displaced) != expected:
            raise ServiceLabError("unit-changed")
        try:
            os.link(
                candidate,
                _UNIT,
                src_dir_fd=attempt,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
        except FileExistsError:
            raise ServiceLabError("unit-changed") from None
        os.unlink(candidate, dir_fd=attempt)
        os.fsync(directory)
        os.fsync(attempt)
        if _read(attempt, displaced) != expected or _read(directory, _UNIT) != replacement:
            raise ServiceLabError("unit-changed")
    except BaseException:
        _recover_publication(directory, attempt)
        raise
    os.unlink("pending-unit", dir_fd=attempt)
    os.fsync(attempt)


def _move_no_replace(
    source_directory: int, source: str, destination_directory: int, destination: str
) -> None:
    """Use Linux renameat2 for atomic no-clobber, including empty directories."""
    rename = ctypes.CDLL("libc.so.6", use_errno=True).renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if (
        cast(
            "int",
            rename(
                source_directory,
                os.fsencode(source),
                destination_directory,
                os.fsencode(destination),
                1,  # RENAME_NOREPLACE
            ),
        )
        != 0
    ):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    os.fsync(destination_directory)
    os.fsync(source_directory)


def _displace_site(home: Path, attempt: int) -> None:
    with _directory(home) as directory, _directory(home / "public_html") as published:
        metadata = os.fstat(published)
        publication = uuid.uuid4().hex
        _write(
            attempt,
            "pending-site",
            f"{publication}\n{metadata.st_dev}\n{metadata.st_ino}\n".encode("ascii"),
        )
        _move_no_replace(directory, "public_html", attempt, f"published-{publication}")
        displaced = os.stat(f"published-{publication}", dir_fd=attempt, follow_symlinks=False)
        if (displaced.st_dev, displaced.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise ServiceLabError("unit-changed")


def _restore_site(home: Path, attempt: int) -> None:
    """Restore only our snapshot; a rebuild, even an empty directory, always wins."""
    try:
        pending = _read(attempt, "pending-site").decode("ascii")
    except FileNotFoundError:
        return
    if re.fullmatch(r"[0-9a-f]{32}\n[0-9]+\n[0-9]+\n", pending) is None:
        raise ServiceLabError("attempt-mismatch")
    publication, device, inode = pending.splitlines()
    with _directory(home) as directory:
        try:
            displaced = os.stat(f"published-{publication}", dir_fd=attempt, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            # A publisher racing displacement leaves a different inode: retain, never install it.
            if (displaced.st_dev, displaced.st_ino) == (int(device), int(inode)) and stat.S_ISDIR(
                displaced.st_mode
            ):
                with contextlib.suppress(FileExistsError):
                    _move_no_replace(attempt, f"published-{publication}", directory, "public_html")
        os.fsync(directory)
        os.fsync(attempt)
        os.unlink("pending-site", dir_fd=attempt)
        os.fsync(attempt)


def _command(
    arguments: tuple[str, ...],
    environment: dict[str, str],
    deadline: float,
    limit: int = 32768,
) -> tuple[int, bytes]:
    """Bound time and captured bytes; argv and environment are exclusively local."""
    deadline = min(deadline, time.monotonic() + 2)
    if deadline <= time.monotonic():
        raise ServiceLabError("timeout")
    with subprocess.Popen(  # noqa: S603 - only fixed executable/argument call sites below
        arguments,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd="/",
        env=environment,
        close_fds=True,
        start_new_session=True,
    ) as process:
        output = bytearray()
        try:
            if process.stdout is None:
                raise ServiceLabError("runner-unavailable")
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ServiceLabError("timeout")
                    for selected, _events in selector.select(remaining):
                        chunk = os.read(selected.fd, 8192)
                        if not chunk:
                            selector.unregister(selected.fd)
                        elif len(output) + len(chunk) > limit:
                            raise ServiceLabError("output-limit")
                        else:
                            output.extend(chunk)
            return process.wait(timeout=max(0, deadline - time.monotonic())), bytes(output)
        except subprocess.TimeoutExpired:
            raise ServiceLabError("timeout") from None
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def _systemctl(arguments: tuple[str, ...], environment: dict[str, str], deadline: float) -> bytes:
    status, output = _command(
        ("/usr/bin/systemctl", "--user", "--no-pager", "--no-ask-password", *arguments),
        environment,
        deadline,
    )
    if status:
        raise ServiceLabError("runner-unavailable")
    return output


def _properties(environment: dict[str, str], deadline: float) -> dict[str, str]:
    properties: dict[str, str] = {}
    for line in (
        _systemctl(
            ("show", _UNIT, "--all", "--property=" + ",".join(_PROPERTIES)), environment, deadline
        )
        .decode("utf-8")
        .splitlines()
    ):
        name, separator, value = line.partition("=")
        if not separator or name in properties or name not in _PROPERTIES:
            raise ServiceLabError("unsafe-unit")
        properties[name] = value
    # systemctl's array printers emit no line for these empty arrays, even with --all.
    for name in _OMITTED_EMPTY_ARRAYS:
        properties.setdefault(name, "")
    return properties


def _manager_environment(environment: dict[str, str], deadline: float) -> None:
    """Allow normal login variables, not loader/Caddy overrides inherited on restart."""
    for line in (
        _systemctl(("show-environment",), environment, deadline).decode("utf-8").splitlines()
    ):
        name, separator, value = line.partition("=")
        if (
            not separator
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
            or name.startswith(("LD_", "CADDY_"))
            or name == "GCONV_PATH"
            or (name == "HOME" and shlex.split(value) != [environment["HOME"]])
        ):
            raise ServiceLabError("unsafe-unit")


def _unit_lines(source: bytes) -> Generator[tuple[str, str]]:
    """Keep physical spans for edits while joining systemd continuation lines for parsing."""
    physical: list[str] = []
    logical: list[str] = []
    for raw_line in source.decode("utf-8").splitlines(keepends=True):
        physical.append(raw_line)
        line = raw_line.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith(("#", ";")):
            if not logical:
                yield "".join(physical), ""
                physical.clear()
            continue
        if line.endswith("\\"):
            if not raw_line.endswith("\n") or "\\" in line[:-1]:
                raise ServiceLabError("unsafe-unit")
            logical.append(line[:-1])
            continue
        if "\\" in line:
            raise ServiceLabError("unsafe-unit")
        logical.append(line)
        yield "".join(physical), " ".join(logical)
        physical.clear()
        logical.clear()
    if logical:
        raise ServiceLabError("unsafe-unit")


def _settings(source: bytes) -> dict[str, str]:
    settings: dict[str, str] = {}
    section = ""
    sections: set[str] = set()
    for _physical, raw_line in _unit_lines(source):
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line in {"[Unit]", "[Service]", "[Install]"}:
            section = line
            if section in sections:
                raise ServiceLabError("unsafe-unit")
            sections.add(section)
            continue
        name, separator, value = line.partition("=")
        key = f"{section}{name.strip()}"
        if not separator or key in settings or "\x00" in line:
            raise ServiceLabError("unsafe-unit")
        settings[key] = value.strip()
    if (
        set(settings) - {"[Unit]Description"}
        != {
            "[Service]WorkingDirectory",
            "[Service]ExecStart",
            "[Service]Restart",
            "[Install]WantedBy",
        }
        or settings.get("[Service]Restart") != "on-failure"
        or settings.get("[Install]WantedBy") != "default.target"
    ):
        raise ServiceLabError("unsafe-unit")
    return settings


def _baseline(source: bytes, home: Path) -> bool:
    settings = _settings(source)
    return settings["[Service]WorkingDirectory"] in {"%h", str(home)} and " ".join(
        settings["[Service]ExecStart"].split()
    ) in {
        " ".join(
            (
                f"/usr/bin/caddy file-server --listen :{10000 + os.getuid()}",
                f"--root {root}/public_html --access-log",
            )
        )
        for root in ("%h", str(home))
    }


def _installed(source: bytes, home: Path, properties: dict[str, str]) -> None:
    if set(properties) != set(_PROPERTIES):
        raise ServiceLabError("unsafe-unit")
    settings = _settings(source)
    command = " ".join(settings["[Service]ExecStart"].replace("%h", str(home)).split())
    expected = {
        "Id": _UNIT,
        "Names": _UNIT,
        "LoadState": "loaded",
        "FragmentPath": str(home / ".config/systemd/user" / _UNIT),
        "NeedDaemonReload": "no",
        "Transient": "no",
        "Type": "simple",
        "Restart": "on-failure",
        "WorkingDirectory": settings["[Service]WorkingDirectory"].replace("%h", str(home)),
    }
    if (
        any(properties.get(name) != value for name, value in expected.items())
        or any(properties.get(name) != "" for name in _EMPTY_PROPERTIES)
        or re.fullmatch(
            re.escape(f"{{ path={command.split()[0]} ; argv[]={command} ; ignore_errors=no ; ")
            + r"start_time=[^;{}]* ; stop_time=[^;{}]* ; pid=[0-9]+ ; "
            + r"code=[^;{}]* ; status=[^;{}]* }",
            properties.get("ExecStart", ""),
        )
        is None
    ):
        raise ServiceLabError("unsafe-unit")


def _index(home: Path, *, missing_site: bool = False) -> bytes | None:
    try:
        with _directory(home / "public_html") as directory:
            return _read(directory, "index.html", _PAGE_LIMIT)
    except FileNotFoundError:
        if not missing_site or (home / "public_html").exists(follow_symlinks=False):
            raise
        return None


def _unit_source(home: Path, directory: int) -> bytes:
    if Path(f"/proc/self/fd/{directory}").resolve(strict=True) != home / ".config/systemd/user":
        raise ServiceLabError("unsafe-path")
    return _read(directory, _UNIT)


def _running_process(source: bytes, home: Path, properties: dict[str, str]) -> None:
    """Check the live process, since a reload can leave an older, different process alive."""
    process_id = properties["MainPID"]
    if re.fullmatch(r"[1-9][0-9]{0,9}", process_id) is None:
        raise ServiceLabError("unsafe-unit")
    process_path = Path("/proc") / process_id
    executable = Path("/usr/bin/caddy")
    metadata = executable.lstat()
    if (
        metadata.st_uid != 0
        or metadata.st_mode & 0o7022
        or not stat.S_ISREG(metadata.st_mode)
        or not os.access(executable, os.X_OK)
        or (process_path / "exe").resolve(strict=True) != executable.resolve(strict=True)
        or (process_path / "cwd").resolve(strict=True) != home
    ):
        raise ServiceLabError("unsafe-unit")
    with _directory(process_path) as process:
        if _read(process, "cmdline").split(b"\0") != [
            *(
                argument.encode("utf-8")
                for argument in _settings(source)["[Service]ExecStart"]
                .replace("%h", str(home))
                .split()
            ),
            b"",
        ]:
            raise ServiceLabError("unsafe-unit")


def _http(environment: dict[str, str], deadline: float) -> tuple[int | None, bytes]:
    status, output = _command(
        (
            "/usr/bin/curl",
            "-q",
            "--silent",
            "--max-time",
            "1",
            "--max-filesize",
            str(_PAGE_LIMIT),
            "--noproxy",
            "*",
            "--proto",
            "=http",
            "--max-redirs",
            "0",
            "--write-out",
            "\n%{http_code}",
            f"http://127.0.0.1:{10000 + os.getuid()}/",
        ),
        environment,
        deadline,
        _PAGE_LIMIT + 4,
    )
    body, separator, code = output.rpartition(b"\n")
    if status or not separator or re.fullmatch(rb"[1-5][0-9]{2}", code) is None:
        return None, b""
    return int(code), body


def _observe(  # noqa: PLR0913 - retain diagnostic evidence when a safety check fails
    home: Path,
    directory: int,
    environment: dict[str, str],
    deadline: float,
    injected: bytes | None = None,
    *,
    missing_site: bool = False,
) -> tuple[bytes, dict[str, str], int | None, bool, str | None, bytes]:
    """Collect read-only evidence even when the unit is not safe to mutate or credit."""
    source = _unit_source(home, directory)
    properties: dict[str, str] = {}
    http_status: int | None = None
    body = b""
    try:
        properties = _properties(environment, deadline)
        http_status, body = _http(environment, deadline)
        baseline = _baseline(source, home)
        if not baseline and source != injected:
            raise ServiceLabError("unsafe-unit")
        _installed(source, home, properties)
        if baseline and properties["ActiveState"] == "active":
            _running_process(source, home, properties)
        index = _index(home, missing_site=missing_site)
        if (
            _unit_source(home, directory) != source
            or _index(home, missing_site=missing_site) != index
        ):
            raise ServiceLabError("unit-changed")
        healthy = (
            baseline
            and properties["ActiveState"] == "active"
            and properties["SubState"] == "running"
            and http_status == 200
            and index is not None
            and body == index
        )
        if healthy:
            current_properties = _properties(environment, deadline)
            _installed(source, home, current_properties)
            healthy = all(
                current_properties[name] == properties[name]
                for name in (
                    "ActiveState",
                    "SubState",
                    "MainPID",
                    "ExecMainStartTimestampMonotonic",
                )
            )
    except ServiceLabError as failure:
        return source, properties, http_status, False, str(failure), body
    except UnicodeError:
        return source, properties, http_status, False, "unsafe-unit", body
    except OSError:
        return source, properties, http_status, False, "runner-unavailable", body
    return source, properties, http_status, healthy, None, body


def _wrong_root(action: ServiceLabAction) -> Path:
    return Path(f"/tmp/guide-{os.getuid()}-{action.run_id}")  # noqa: S108 - private per-run root


def _prepare_empty_site(home: Path, state: int) -> None:
    """Publish a recorded lab inode without adopting or removing a learner directory."""
    try:
        identity = _read(state, "empty-site-owner")
    except FileNotFoundError:
        with _directory(home / _STATE / "empty-site", create=True, private=True) as staged:
            metadata = os.fstat(staged)
            identity = f"{metadata.st_dev}\n{metadata.st_ino}\n".encode("ascii")
            _write(state, "empty-site-owner", identity, exclusive=True)
    with _directory(home) as directory:
        # The identity is durable before the rename, so interruption can safely resume.
        try:
            os.stat("empty-site", dir_fd=state, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            try:
                _move_no_replace(state, "empty-site", directory, "empty-site")
            except FileExistsError:
                raise ServiceLabError("unit-changed") from None
        with _directory(home / "empty-site", private=True) as empty_site:
            metadata = os.fstat(empty_site)
            if identity != f"{metadata.st_dev}\n{metadata.st_ino}\n".encode("ascii"):
                raise ServiceLabError("unit-changed")


def _fault(
    source: bytes, action: ServiceLabAction, attempt_path: Path, persisted: bytes = b""
) -> tuple[bytes, str | None]:
    """Return injected bytes and an exit status; None means an active HTTP fault."""
    settings = _settings(source)
    match action.scenario:
        case "missing-executable":
            name = "ExecStart"
            expected_status = "203"
            # Retain the executable of persisted attempts for exact inspection and recovery.
            value = settings["[Service]ExecStart"].replace(
                "/usr/bin/caddy",
                str(attempt_path / "missing-caddy")
                if persisted
                and _settings(persisted)["[Service]ExecStart"].split()[:1]
                == [str(attempt_path / "missing-caddy")]
                else "/usr/bin/cadddyyy",
                1,
            )
        case "invalid-argument":
            name = "ExecStart"
            expected_status = "1"
            value = settings["[Service]ExecStart"].replace("--access-log", "--access-logs", 1)
        case "missing-published-site":
            return source, None
        case "empty-root" | "wrong-content":
            name = "ExecStart"
            expected_status = None
            root = (
                _wrong_root(action)
                if action.scenario == "wrong-content"
                else attempt_path.parents[len(Path(_STATE).parts)] / "empty-site"
            )
            if (
                action.scenario == "empty-root"
                and persisted
                and str(attempt_path / "empty-root")
                in _settings(persisted)["[Service]ExecStart"].split()
            ):
                root = attempt_path / "empty-root"
            value = re.sub(
                r"--root\s+\S+",
                f"--root {root}",
                settings["[Service]ExecStart"],
                count=1,
            )
    lines: list[str] = []
    for physical, logical in _unit_lines(source):
        if logical.partition("=")[0].strip() == name:
            ending = physical[len(physical.rstrip("\r\n")) :]
            lines.append(f"{name}={value}{ending}")
        else:
            lines.append(physical)
    return "".join(lines).encode("utf-8"), expected_status


def _phase(directory: int, action: ServiceLabAction, phase: str) -> None:
    _write(directory, "attempt", f"{action.scenario}\n{phase}\n".encode("ascii"))


def _read_phase(directory: int, action: ServiceLabAction | None = None) -> str:
    lines = _read(directory, "attempt").decode("ascii").splitlines()
    if (
        len(lines) != 2
        or lines[0] not in SERVICE_LAB_SCENARIOS
        or lines[1] not in {"prepared", "active", "rolling-back", "aborted"}
        or (action is not None and lines[0] != action.scenario)
    ):
        raise ServiceLabError("attempt-mismatch")
    return lines[1]


def _restart(source: bytes, home: Path, environment: dict[str, str], deadline: float) -> None:
    _systemctl(("daemon-reload",), environment, deadline)
    _installed(source, home, _properties(environment, deadline))
    _manager_environment(environment, deadline)
    _systemctl(("reset-failed", _UNIT), environment, deadline)
    _systemctl(("--no-block", "restart", _UNIT), environment, deadline)


def _rollback(  # noqa: C901, PLR0913 - rollback needs both pinned directories and fault-specific recovery
    action: ServiceLabAction,
    home: Path,
    directory: int,
    attempt: int,
    environment: dict[str, str],
    deadline: float,
) -> None:
    if _read_phase(attempt, action) == "active":
        raise ServiceLabError("attempt-mismatch")
    original = _read(attempt, "original.service")
    injected = _read(attempt, "injected.service")
    if (
        not _baseline(original, home)
        or injected != _fault(original, action, home / _STATE / action.run_id, injected)[0]
    ):
        raise ServiceLabError("unsafe-unit")
    if action.scenario == "missing-published-site":
        _phase(attempt, action, "rolling-back")
        _restore_site(home, attempt)
        _phase(attempt, action, "aborted")
        return
    _recover_publication(directory, attempt)
    current = _unit_source(home, directory)
    if current not in {original, injected}:
        raise ServiceLabError("unit-changed")
    properties = _properties(environment, deadline)
    # Pending reload is expected after interruption, but unknown fragments/overrides are not.
    if (
        properties.get("FragmentPath") != str(home / ".config/systemd/user" / _UNIT)
        or properties.get("DropInPaths") != ""
    ):
        raise ServiceLabError("unsafe-unit")
    _phase(attempt, action, "rolling-back")
    if current == injected:
        if _unit_source(home, directory) != injected:
            raise ServiceLabError("unit-changed")
        _publish_unit(
            directory,
            attempt,
            injected,
            original,
            stat.S_IMODE(os.stat("original.service", dir_fd=attempt).st_mode),
        )
    if _unit_source(home, directory) != original:
        raise ServiceLabError("unit-changed")
    _restart(original, home, environment, deadline)
    while time.monotonic() < deadline:
        observation = _observe(home, directory, environment, deadline)
        if observation[4] is not None:
            raise ServiceLabError(observation[4])
        if observation[3]:
            _phase(attempt, action, "aborted")
            return
        time.sleep(0.1)
    raise ServiceLabError("rollback-failed")


def _excerpt(content: bytes) -> str:
    return "".join(
        character if character in "\n\t" or 32 <= ord(character) < 127 else "?"
        for character in content.decode("utf-8", errors="replace")[:2048]
    )


def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:  # noqa: C901, PLR0912, PLR0915 - transactional failure boundary
    """Start once or inspect live evidence, only as the learner owning this unit.

    A fresh start requires a healthy recognized baseline. Active attempts never
    reinject, including after repair or a lost reply. A rolled-back, aborted preparation
    may retry once per later start request, only from its exact original healthy unit
    and safe fault targets. Incomplete initialization resumes only on explicit start,
    reusing matching artifacts without replacing them. Inspection never retries.
    Prepared attempts recover without launching a fault in that request. Only a tentative
    machinery failure can roll back, and only while the displaced bytes still equal this
    attempt's own injection.
    Published output is moved without restarting Caddy; recovery never replaces a rebuild.
    Displaced inodes are retained privately, including edits racing with publication.
    Seven of the 25 seconds are reserved for failure recovery. A hard-killed attempt
    is recovered on the next request for that same run, without granting credit.
    """
    service_lab_action_payload(action)
    deadline = time.monotonic() + SERVICE_LAB_TIMEOUT_SECONDS
    work_deadline = deadline - 7
    started, healthy = False, False
    source, journal = b"", b""
    properties: dict[str, str] = {}
    http_status: int | None = None
    error: str | None = None
    try:
        account = _account()
        home = Path(account.pw_dir)
        environment = {
            "HOME": account.pw_dir,
            "USER": account.pw_name,
            "LOGNAME": account.pw_name,
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
            "SYSTEMD_COLORS": "0",
            "XDG_RUNTIME_DIR": f"/run/user/{account.pw_uid}",
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{account.pw_uid}/bus",
        }
        with (
            _directory(home),
            _directory(home / ".config/systemd/user") as directory,
            _directory(home / _STATE, create=True, private=True) as state,
            contextlib.ExitStack() as stack,
        ):
            lock = os.open(
                "lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=state,
            )
            stack.callback(os.close, lock)
            metadata = os.fstat(lock)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != account.pw_uid
                or metadata.st_nlink != 1
                or metadata.st_mode & 0o077
            ):
                raise ServiceLabError("unsafe-path")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ServiceLabError("attempt-busy") from None
            attempt_path = home / _STATE / action.run_id
            try:
                os.stat(action.run_id, dir_fd=state, follow_symlinks=False)
            except FileNotFoundError:
                exists = False
            else:
                exists = True
            phase: str | None = None
            attempt = (
                stack.enter_context(_directory(attempt_path, private=True)) if exists else None
            )
            if attempt is not None:
                try:
                    phase = _read_phase(attempt, action)
                except FileNotFoundError:
                    if action.operation == "inspect":
                        raise ServiceLabError("interrupted-attempt") from None
                if phase == "aborted" and action.operation == "inspect":
                    raise ServiceLabError("injection-failed")
            elif action.operation == "inspect":
                raise ServiceLabError("attempt-missing")
            previous = ""
            if phase != "active":
                with contextlib.suppress(FileNotFoundError):
                    previous = _read(state, "current").decode("ascii")
                if previous and previous != action.run_id:
                    if re.fullmatch(r"[0-9a-f]{32}", previous) is None:
                        raise ServiceLabError("attempt-mismatch")
                    # Existing attempts cannot reclaim ownership from a subsequent run.
                    if exists:
                        raise ServiceLabError("previous-unrecovered")
                    with _directory(home / _STATE / previous, private=True) as previous_attempt:
                        try:
                            if _read_phase(previous_attempt) in {"prepared", "rolling-back"}:
                                raise ServiceLabError("previous-unrecovered")
                        except FileNotFoundError:
                            raise ServiceLabError("previous-unrecovered") from None
            if attempt is not None and phase in {"prepared", "rolling-back"}:
                _write(state, "current", action.run_id.encode("ascii"))
                try:
                    _rollback(action, home, directory, attempt, environment, deadline)
                except (OSError, ValueError):
                    raise ServiceLabError("rollback-failed") from None
                raise ServiceLabError("interrupted-attempt")
            if attempt is not None and phase is not None:
                original = _read(attempt, "original.service")
                injected = _read(attempt, "injected.service")
                expected_injected, expected_status = _fault(
                    original, action, attempt_path, injected
                )
                if not _baseline(original, home) or injected != expected_injected:
                    raise ServiceLabError("attempt-mismatch")
                started = phase == "active"
                source, properties, http_status, healthy, error, _body = _observe(
                    home,
                    directory,
                    environment,
                    work_deadline,
                    injected,
                    missing_site=action.scenario == "missing-published-site",
                )
                if not started:
                    if source != original:
                        raise ServiceLabError("unit-changed")
                    if error is not None:
                        raise ServiceLabError(error)
                    if not healthy:
                        raise ServiceLabError("baseline-unhealthy")
                    _manager_environment(environment, work_deadline)
                    mode = stat.S_IMODE(
                        os.stat(_UNIT, dir_fd=directory, follow_symlinks=False).st_mode
                    )
                    if mode != stat.S_IMODE(os.stat("original.service", dir_fd=attempt).st_mode):
                        raise ServiceLabError("unit-changed")
            else:
                _manager_environment(environment, work_deadline)
                source, properties, http_status, healthy, error, _body = _observe(
                    home, directory, environment, work_deadline
                )
                if error is not None:
                    raise ServiceLabError(error)
                if not healthy:
                    raise ServiceLabError(
                        "previous-unrecovered" if previous else "baseline-unhealthy"
                    )
                mode = stat.S_IMODE(os.stat(_UNIT, dir_fd=directory, follow_symlinks=False).st_mode)
                if not mode & stat.S_IWUSR:
                    raise ServiceLabError("unsafe-path")
                # Claim before mkdir: any partial directory already belongs to this run.
                _write(state, "current", action.run_id.encode("ascii"))
                if attempt is None:
                    os.mkdir(action.run_id, mode=0o700, dir_fd=state)
                    os.fsync(state)
                    attempt = stack.enter_context(_directory(attempt_path, private=True))
                persisted = b""
                with contextlib.suppress(FileNotFoundError):
                    persisted = _read(attempt, "injected.service")
                injected, expected_status = _fault(source, action, attempt_path, persisted)
                for name, content, permissions in (
                    ("original.service", source, mode),
                    ("injected.service", injected, 0o600),
                ):
                    try:
                        saved = _read(attempt, name)
                    except FileNotFoundError:
                        _write(attempt, name, content, permissions, exclusive=True)
                    else:
                        if (
                            saved != content
                            or stat.S_IMODE(
                                os.stat(name, dir_fd=attempt, follow_symlinks=False).st_mode
                            )
                            != permissions
                        ):
                            raise ServiceLabError("unit-changed")
                if action.scenario == "empty-root" and str(attempt_path / "empty-root") in (
                    _settings(injected)["[Service]ExecStart"].split()
                ):
                    with contextlib.suppress(FileExistsError):
                        os.mkdir("empty-root", mode=0o700, dir_fd=attempt)
                    os.fsync(attempt)
                elif action.scenario == "wrong-content":
                    with contextlib.suppress(FileExistsError):
                        _wrong_root(action).mkdir(mode=0o700)
                    with (
                        _directory(_wrong_root(action), private=True) as wrong_root,
                        os.scandir(wrong_root) as entries,
                    ):
                        if {entry.name for entry in entries} - {"index.html"}:
                            raise ServiceLabError("unit-changed")
                        try:
                            index = _read(wrong_root, "index.html")
                        except FileNotFoundError:
                            _write(wrong_root, "index.html", _WRONG_INDEX, exclusive=True)
                        else:
                            if index != _WRONG_INDEX:
                                raise ServiceLabError("unit-changed")
            if not started:
                mode = stat.S_IMODE(os.stat("original.service", dir_fd=attempt).st_mode)
                if not mode & stat.S_IWUSR:
                    raise ServiceLabError("unsafe-path")
                if action.scenario == "missing-executable":
                    try:
                        Path(_settings(injected)["[Service]ExecStart"].split()[0]).lstat()
                    except FileNotFoundError:
                        pass
                    else:
                        raise ServiceLabError("unit-changed")
                if action.scenario == "empty-root":
                    command = _settings(injected)["[Service]ExecStart"].split()
                    root = Path(command[command.index("--root") + 1])
                    if root == home / "empty-site":
                        _prepare_empty_site(home, state)
                    with (
                        _directory(root, private=True) as empty_root,
                        os.scandir(empty_root) as entries,
                    ):
                        if next(entries, None) is not None:
                            raise ServiceLabError("unit-changed")
                elif action.scenario == "wrong-content":
                    with (
                        _directory(_wrong_root(action), private=True) as wrong_root,
                        os.scandir(wrong_root) as entries,
                    ):
                        if (
                            {entry.name for entry in entries} != {"index.html"}
                            or _read(wrong_root, "index.html") != _WRONG_INDEX
                            or _index(home) == _WRONG_INDEX
                        ):
                            raise ServiceLabError("unit-changed")
                if phase == "aborted":
                    _write(state, "current", action.run_id.encode("ascii"))
                _phase(attempt, action, "prepared")
                healthy = False
                try:
                    if _unit_source(home, directory) != source:
                        raise ServiceLabError("unit-changed")
                    _installed(source, home, _properties(environment, work_deadline))
                    previous_start = properties["ExecMainStartTimestampMonotonic"]
                    previous_process = properties["MainPID"]
                    if action.scenario == "missing-published-site":
                        _displace_site(home, attempt)
                    else:
                        _publish_unit(directory, attempt, source, injected, mode)
                        _restart(injected, home, environment, work_deadline)
                    while time.monotonic() < work_deadline:
                        (
                            source,
                            properties,
                            http_status,
                            _healthy,
                            observation_error,
                            body,
                        ) = _observe(
                            home,
                            directory,
                            environment,
                            work_deadline,
                            injected,
                            missing_site=action.scenario == "missing-published-site",
                        )
                        if observation_error is not None:
                            raise ServiceLabError(observation_error)
                        witnessed = (
                            properties["ActiveState"] == "active"
                            and (
                                http_status == 200 and body == _WRONG_INDEX and body != _index(home)
                                if action.scenario == "wrong-content"
                                else http_status == 404
                            )
                            if expected_status is None
                            else properties["ExecMainStatus"] == expected_status
                            and properties["ExecMainCode"] == "1"
                            and properties["Result"] == "exit-code"
                            and (
                                properties["ActiveState"] in {"failed", "inactive"}
                                or properties["SubState"] == "auto-restart"
                            )
                        )
                        if action.scenario == "missing-published-site":
                            witnessed = (
                                witnessed
                                and properties["SubState"] == "running"
                                and _index(home, missing_site=True) is None
                                and properties["MainPID"] == previous_process
                                and properties["ExecMainStartTimestampMonotonic"] == previous_start
                            )
                        else:
                            witnessed = (
                                witnessed
                                and properties["ExecMainStartTimestampMonotonic"] != previous_start
                            )
                        if witnessed and source == injected:
                            if expected_status is None:
                                _running_process(source, home, properties)
                            _phase(attempt, action, "active")
                            started = True
                            break
                        time.sleep(0.1)
                    if not started:
                        raise ServiceLabError("injection-failed")
                except (OSError, ValueError) as failure:
                    try:
                        _rollback(action, home, directory, attempt, environment, deadline)
                    except (OSError, ValueError):
                        raise ServiceLabError("rollback-failed") from None
                    if isinstance(failure, ServiceLabError) and str(failure) == "unit-changed":
                        raise ServiceLabError("unit-changed") from None
                    raise ServiceLabError("injection-failed") from None
            with contextlib.suppress(OSError, ServiceLabError):
                _status, journal = _command(
                    (
                        "/usr/bin/journalctl",
                        "--user",
                        "--unit=site.service",
                        "--no-pager",
                        "--lines=12",
                        "--output=cat",
                    ),
                    environment,
                    work_deadline,
                )
    except ServiceLabError as failure:
        error, healthy = str(failure), False
    except (OSError, ValueError):
        error, healthy = "runner-unavailable", False
    return ServiceLabReport(
        run_id=action.run_id,
        scenario=action.scenario,
        started=started,
        healthy=healthy,
        unit=_excerpt(source),
        status=_excerpt(
            "\n".join(
                f"{name}={properties[name]}"
                for name in (
                    "LoadState",
                    "NeedDaemonReload",
                    "ActiveState",
                    "SubState",
                    "Result",
                    "ExecMainCode",
                    "ExecMainStatus",
                )
                if name in properties
            ).encode("utf-8")
        ),
        journal=_excerpt(journal),
        http_status=http_status,
        error=error,
    )
