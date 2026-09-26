"""Protect publication swaps and the optional read-only shell functions."""

from __future__ import annotations

import re
import shlex
import shutil
import socket
import subprocess
import time
from contextlib import closing
from http.client import HTTPConnection
from importlib.resources import files
from pathlib import Path
from typing import cast

import pytest

from maker_guide.repositories.helpers import load_json


def test_invalid_caddy_argument_is_an_application_failure(temporary_path: Path) -> None:
    """A real executable rejects the faulty flag with exit 1, not systemd's EXEC failure."""
    caddy_path = shutil.which("caddy")
    assert caddy_path is not None, "Install Caddy before running pytest."
    result = subprocess.run(
        [
            caddy_path,
            "file-server",
            "--listen",
            "127.0.0.1:0",
            "--root",
            str(temporary_path),
            "--access-logs",
        ],
        cwd=temporary_path,
        env={"HOME": str(temporary_path)},
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 1
    assert "unknown flag: --access-logs" in result.stdout + result.stderr


@pytest.mark.parametrize("root_missing", [False, True])
def test_service_serves_replaced_public_directory_without_restart(
    temporary_path: Path, root_missing: bool
) -> None:
    """Real Caddy survives empty or absent output and serves a rebuild without restarting."""
    caddy_path = shutil.which("caddy")
    assert caddy_path is not None, (
        "Install Caddy before running pytest; this test needs real Caddy."
    )
    command_match = re.search(
        r"(?m)^ExecStart=(?P<command>/usr/bin/caddy file-server .+)$",
        files("maker_guide.curriculum")
        .joinpath("content/lf2607/sessions/S08/self-study.md")
        .read_text(encoding="utf-8")
        .replace("\\\n", " "),
    )
    assert command_match is not None
    arguments = [
        argument.replace("%h", str(temporary_path))
        for argument in shlex.split(command_match["command"])
    ]
    assert arguments[arguments.index("--listen") + 1] == ":12345"
    arguments[0] = caddy_path
    public_directory = temporary_path / "public_html"
    public_directory.mkdir()
    public_directory.joinpath("index.html").write_text("before publication", encoding="utf-8")
    log_path = temporary_path / "caddy.log"
    with log_path.open("w", encoding="utf-8") as log_output:
        # ponytail: release the allocated port immediately before spawn; fail on a bind race.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = cast("tuple[str, int]", listener.getsockname())[1]
            # Keep CI isolated without relying on the classroom firewall.
            arguments[arguments.index("--listen") + 1] = f"127.0.0.1:{port}"
        server = subprocess.Popen(
            arguments,
            cwd=temporary_path,
            env={
                "HOME": str(temporary_path),
                "XDG_CONFIG_HOME": str(temporary_path / ".config"),
                "XDG_DATA_HOME": str(temporary_path / ".local" / "share"),
                "XDG_CACHE_HOME": str(temporary_path / ".cache"),
            },
            stdout=log_output,
            stderr=subprocess.STDOUT,
        )
        try:
            _wait_for_server(server, port, log_path)
            for uri, expected_body in (
                ("/", b"before publication"),
                ("/", None),
                ("/", b"after publication"),
                ("/missing.html", None),
            ):
                with closing(HTTPConnection("127.0.0.1", port, timeout=5)) as connection:
                    connection.request("GET", uri)
                    response = connection.getresponse()
                    assert response.status == (200 if expected_body is not None else 404)
                    response_body = response.read()
                    if expected_body is not None:
                        assert response_body == expected_body
                assert server.poll() is None, log_path.read_text(encoding="utf-8")
                if expected_body == b"before publication":
                    public_directory.rename(temporary_path / "old-public-html")
                    if not root_missing:
                        public_directory.mkdir()
                elif uri == "/" and expected_body is None:
                    public_directory.mkdir(exist_ok=True)
                    public_directory.joinpath("index.html").write_text(
                        "after publication", encoding="utf-8"
                    )
                    shutil.rmtree(temporary_path / "old-public-html")
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
    records = [
        load_json(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("{")
    ]
    for uri, status in (("/", 200), ("/", 404), ("/missing.html", 404)):
        assert any(
            record.get("status") == status
            and isinstance(record.get("ts"), (int, float))
            and {"method": "GET", "uri": uri}.items()
            <= cast("dict[str, object]", record.get("request", {})).items()
            for record in records
        ), records


def _wait_for_server(server: subprocess.Popen[bytes], port: int, log_path: Path) -> None:
    """Wait for Caddy to accept connections or fail with its startup log."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and server.poll() is None:
        with socket.socket() as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    pytest.fail(f"Caddy failed to start:\n{log_path.read_text(encoding='utf-8')}")


@pytest.mark.parametrize(
    ("function_name", "command_name", "arguments", "exit_status"),
    [
        ("site_status", "systemctl", "--user\nstatus\nsite.service\n", 0),
        ("site_status", "systemctl", "--user\nstatus\nsite.service\n", 3),
        ("site_logs", "journalctl", "--user\n-u\nsite.service\n--since\n5 minutes ago\n", 0),
    ],
)
def test_sourced_helper_calls_only_read_only_commands(
    temporary_path: Path,
    function_name: str,
    command_name: str,
    arguments: str,
    exit_status: int,
) -> None:
    """Sourcing defines functions; invoking one preserves arguments and an inactive status."""
    helper_match = re.search(
        r"(?ms)^(?P<helper>site_status\(\) \{.*?^\}\n\nsite_logs\(\) \{.*?^\})$",
        files("maker_guide.curriculum")
        .joinpath("content/lf2607/quests/write-site-helper-functions.md")
        .read_text(encoding="utf-8"),
    )
    assert helper_match is not None
    bash_path = shutil.which("bash")
    assert bash_path is not None
    helper_path = temporary_path / "site functions.sh"
    helper_path.write_text(helper_match["helper"], encoding="utf-8")
    command_path = temporary_path / command_name
    command_path.write_text(
        f"#!{bash_path}\nprintf '%s\\n' \"$@\"\nexit {exit_status}\n", encoding="utf-8"
    )
    command_path.chmod(0o755)
    completed_process = subprocess.run(
        [
            bash_path,
            "--noprofile",
            "--norc",
            "-c",
            'source "$1"\nprintf \'loaded\\n\'\n"$2"',
            "helper-test",
            str(helper_path),
            function_name,
        ],
        cwd=temporary_path,
        env={"PATH": str(temporary_path)},
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert completed_process.returncode == exit_status, completed_process.stderr
    assert completed_process.stderr == ""
    assert completed_process.stdout == f"loaded\n{arguments}"
