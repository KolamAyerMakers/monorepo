"""Exercise private admin access and rendered reload wiring with real Caddy."""

from __future__ import annotations

import http.client
import json
import os
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import cast

from tests.states.roles.test_kam_classroom import (
    _caddy_pillar,  # pyright: ignore[reportPrivateUsage]
    _environment,  # pyright: ignore[reportPrivateUsage]
    _load_state,  # pyright: ignore[reportPrivateUsage]
    _state_arguments,  # pyright: ignore[reportPrivateUsage]
)


def test_caddy_admin_is_private_and_reload_uses_its_socket() -> None:
    """Simulate unit permissions as the test user, without invoking systemd."""
    binary = shutil.which("caddy")
    assert binary is not None, "This behavioral regression requires real Caddy on PATH"
    # Keep AF_UNIX paths below Linux's limit, regardless of pytest's temp root.
    with tempfile.TemporaryDirectory(prefix="caddy-", dir="/tmp") as temporary:
        directory = Path(temporary)
        runtime = directory / "caddy"
        admin_socket = runtime / "admin.sock"
        admin_address = f"unix/{admin_socket}"
        configuration = directory / "Caddyfile"
        routes = directory / "routes.caddy"
        _ = routes.write_text("# No learner routes.\n", encoding="utf-8")
        pillar = _caddy_pillar()
        caddy = cast(dict[str, object], pillar["caddy"])
        caddy.update(
            domain="http://127.0.0.1:0",
            local_certs=False,
            admin_address=admin_address,
            configuration_file=str(configuration),
            learner_routes_file=str(routes),
        )
        context = _state_arguments(
            _load_state("roles/kam-classroom/caddy/config.sls", pillar)[
                str(configuration)
            ],
            "file.managed",
        )
        environment = _environment()
        _ = configuration.write_text(
            environment.get_template(
                "roles/kam-classroom/caddy/templates/Caddyfile.j2"
            ).render(**cast(dict[str, object], context["context"])),
            encoding="utf-8",
        )
        unit_lines = (
            environment.get_template(
                "roles/kam-classroom/caddy/templates/service-override.conf.j2"
            )
            .render(caddy=caddy)
            .splitlines()
        )
        unit = dict(line.split("=", 1) for line in unit_lines if "=" in line)
        assert unit["RuntimeDirectory"] == runtime.name
        assert [line for line in unit_lines if line.startswith("ExecReload=")] == [
            "ExecReload=",
            f"ExecReload={unit['ExecReload']}",
        ]
        reload_command = shlex.split(unit["ExecReload"])
        # Fail closed before executing: never fall back to a host admin endpoint.
        assert reload_command == [
            "/usr/bin/caddy",
            "reload",
            "--config",
            str(configuration),
            "--address",
            admin_address,
        ]
        reload_command[0] = binary
        runtime.mkdir(mode=int(unit["RuntimeDirectoryMode"], 8))
        runtime.chmod(int(unit["RuntimeDirectoryMode"], 8))
        service_umask = int(unit["UMask"], 8)
        process_environment = {
            "HOME": temporary,
            "XDG_CONFIG_HOME": str(directory / "config"),
            "XDG_DATA_HOME": str(directory / "data"),
            "XDG_CACHE_HOME": str(directory / "cache"),
            "XDG_RUNTIME_DIR": str(runtime),
        }
        log_path = directory / "caddy.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                [binary, "run", "--config", str(configuration)],
                cwd=directory,
                env=process_environment,
                umask=service_umask,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 10
                while not admin_socket.is_socket():
                    assert process.poll() is None, log_path.read_text()
                    assert time.monotonic() < deadline, log_path.read_text()
                    time.sleep(0.05)
                for path in (runtime, admin_socket):
                    status = path.stat()
                    assert status.st_mode & 0o077 == 0
                    assert (status.st_uid, status.st_gid) == (
                        os.geteuid(),
                        os.getegid(),
                    )
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                    connection.settimeout(5)
                    connection.connect(str(admin_socket))
                    connection.sendall(
                        b"GET /config/ HTTP/1.1\r\nHost:\r\nConnection: close\r\n\r\n"
                    )
                    with http.client.HTTPResponse(connection) as response:
                        response.begin()
                        assert response.status == 200
                        assert (
                            json.loads(response.read())["admin"]["listen"]
                            == admin_address
                        )
                result = subprocess.run(
                    reload_command,
                    cwd=directory,
                    env=process_environment,
                    umask=service_umask,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                assert result.returncode == 0, result.stdout + result.stderr
            finally:
                process.terminate()
                try:
                    _ = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    _ = process.wait(timeout=5)
