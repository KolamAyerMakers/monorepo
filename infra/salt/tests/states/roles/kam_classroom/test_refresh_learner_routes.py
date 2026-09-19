"""Behavioral regressions for the transactional learner-route refresh."""

from __future__ import annotations

import json
import shlex
import stat
import subprocess
from pathlib import Path

import pytest

from tests.states.roles.test_kam_classroom import (
    _environment,  # pyright: ignore[reportPrivateUsage]
)


def _write_command(path: Path, body: str) -> None:
    _ = path.write_text(f"#!/bin/sh\nset -eu\n{body}\n", encoding="utf-8")
    path.chmod(0o700)


def _prepare(directory: Path) -> str:
    _ = (directory / "routes").write_text("old routes\n", encoding="utf-8")
    (directory / "routes").chmod(0o640)
    _ = (directory / "original").write_text("old routes\n", encoding="utf-8")
    _ = (directory / "desired").write_text("new routes\n", encoding="utf-8")
    _write_command(
        directory / "renderer",
        "printf 'render\\n' >> calls\n/usr/bin/cat desired\ntest ! -e fail-render",
    )
    for command, action, arguments, output in (
        ("caddy", "validate", "validate --config Caddyfile", "Valid configuration"),
        ("systemctl", "reload", "reload caddy", "Reloaded caddy.service."),
    ):
        _write_command(
            directory / command,
            f'test "$*" = "{arguments}"\n'
            "/usr/bin/cmp desired routes\n"
            "/usr/bin/cmp original routes.pending\n"
            f"printf '{action}\\n' >> calls\n"
            f"if [ -e fail-{action} ]; then\n"
            f"    printf '{action} failed\\n'\n"
            f"    : > {action}-failed\n"
            "    exit 1\n"
            "fi\n"
            f"printf '{output}\\n'",
        )
    script = (
        _environment()
        .get_template(
            "roles/kam-classroom/caddy/templates/refresh-learner-routes.sh.j2"
        )
        .render(
            learner_routes_file=shlex.quote(str(directory / "routes")),
            database_path="state.db",
            domain="classroom.example",
            configuration_file="Caddyfile",
        )
    )
    for production_path, command in (
        ("/usr/local/bin/maker-guide-render-learner-routes", "renderer"),
        ("/usr/bin/caddy", "caddy"),
        ("/usr/bin/systemctl", "systemctl"),
    ):
        # Fail closed if a fixed command path changes; never invoke host services.
        assert production_path in script
        script = script.replace(production_path, shlex.quote(str(directory / command)))
    return script


def _run(script: str, directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


@pytest.mark.parametrize(
    ("scenario", "expected_calls"),
    [
        ("success", ["render", "validate", "reload"]),
        ("unchanged", ["render"]),
        ("render", ["render"]),
        ("validate", ["render", "validate"]),
        ("reload", ["render", "validate", "reload"]),
    ],
)
def test_refresh_is_transactional_and_retry_safe(
    tmp_path: Path, scenario: str, expected_calls: list[str]
) -> None:
    """Failures retain the old routes; retries publish and then become no-ops."""
    script = _prepare(tmp_path)
    routes = tmp_path / "routes"
    original_status = routes.stat()
    failure = tmp_path / f"fail-{scenario}"
    failed = scenario in {"render", "validate", "reload"}
    if failed:
        failure.touch()
    if scenario == "unchanged":
        _ = (tmp_path / "desired").write_text("old routes\n", encoding="utf-8")

    result = _run(script, tmp_path)

    assert result.returncode == (1 if failed else 0), result.stderr
    assert (tmp_path / "calls").read_text().splitlines() == expected_calls
    assert routes.read_text() == (
        "new routes\n" if scenario == "success" else "old routes\n"
    )
    assert stat.S_IMODE(routes.stat().st_mode) == (
        0o644 if scenario == "success" else 0o640
    )
    assert routes.stat().st_uid == original_status.st_uid
    assert routes.stat().st_gid == original_status.st_gid
    if scenario in {"validate", "reload"}:
        assert (tmp_path / "routes.pending").read_text() == "old routes\n"
        assert stat.S_IMODE((tmp_path / "routes.pending").stat().st_mode) == 0o640
        assert set(tmp_path.glob("routes.*")) == {
            tmp_path / "routes.lock",
            tmp_path / "routes.pending",
        }
        assert f"{scenario} failed\n" in result.stderr
    else:
        assert list(tmp_path.glob("routes.*")) == [tmp_path / "routes.lock"]
    if scenario in {"unchanged", "render"}:
        assert routes.stat().st_ino == original_status.st_ino
        assert routes.stat().st_mtime_ns == original_status.st_mtime_ns
    if failed:
        assert result.stdout == ""
        failure.unlink()
        _ = (tmp_path / "calls").write_text("", encoding="utf-8")
        result = _run(script, tmp_path)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "calls").read_text().splitlines() == [
            "render",
            "validate",
            "reload",
        ]
        assert routes.read_text() == "new routes\n"
        assert stat.S_IMODE(routes.stat().st_mode) == 0o644
    assert json.loads(result.stdout) == {
        "changed": scenario != "unchanged",
        "comment": (
            "Learner routes unchanged"
            if scenario == "unchanged"
            else "Learner routes refreshed"
        ),
    }
    if scenario != "unchanged":
        assert "Valid configuration\n" in result.stderr
        assert "Reloaded caddy.service.\n" in result.stderr
    assert list(tmp_path.glob("routes.*")) == [tmp_path / "routes.lock"]

    published_status = routes.stat()
    lock_status = (tmp_path / "routes.lock").stat()
    _ = (tmp_path / "calls").write_text("", encoding="utf-8")
    result = _run(script, tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "changed": False,
        "comment": "Learner routes unchanged",
    }
    assert (tmp_path / "calls").read_text().splitlines() == ["render"]
    assert result.stderr == ""
    assert routes.stat().st_ino == published_status.st_ino
    assert routes.stat().st_mtime_ns == published_status.st_mtime_ns
    assert routes.stat().st_mode == published_status.st_mode
    assert (tmp_path / "routes.lock").stat().st_ino == lock_status.st_ino
    assert list(tmp_path.glob("routes.*")) == [tmp_path / "routes.lock"]


def test_rendering_holds_the_stable_lock_across_publications(tmp_path: Path) -> None:
    """A competing flock during rendering must fail, without scheduling sleeps."""
    script = _prepare(tmp_path)
    _write_command(
        tmp_path / "renderer",
        "if /usr/bin/flock --nonblock --conflict-exit-code 73 "
        "routes.lock /usr/bin/true; then\n"
        "    exit 91\n"
        "else\n"
        '    test "$?" -eq 73\n'
        "fi\n"
        "printf 'locked-render\\n' >> calls\n"
        "/usr/bin/cat desired",
    )
    (tmp_path / "routes.lock").touch()
    lock_status = (tmp_path / "routes.lock").stat()
    for content in ("first routes\n", "second routes\n"):
        _ = (tmp_path / "original").write_text(
            (tmp_path / "routes").read_text(), encoding="utf-8"
        )
        _ = (tmp_path / "desired").write_text(content, encoding="utf-8")
        result = _run(script, tmp_path)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["changed"] is True
        assert (tmp_path / "routes").read_text() == content
        assert (tmp_path / "routes.lock").stat().st_ino == lock_status.st_ino
    assert (tmp_path / "calls").read_text().splitlines() == [
        "locked-render",
        "validate",
        "reload",
    ] * 2


@pytest.mark.parametrize("scenario", ["interrupted", "failed-restoration"])
def test_matching_routes_with_pending_backup_reload_on_retry(
    tmp_path: Path, scenario: str
) -> None:
    """Matching disk content cannot skip reload while recovery is still pending."""
    script = _prepare(tmp_path)
    pending = tmp_path / "routes.pending"
    (tmp_path / "routes.lock").touch()
    if scenario == "interrupted":
        _ = pending.write_text("old routes\n", encoding="utf-8")
        pending.chmod(0o640)
        _ = (tmp_path / "routes").write_text("new routes\n", encoding="utf-8")
        (tmp_path / "routes").chmod(0o644)
    else:
        _write_command(
            tmp_path / "move",
            'test ! -e reload-failed || exit 74\nexec /usr/bin/mv "$@"',
        )
        script = script.replace("/usr/bin/mv", shlex.quote(str(tmp_path / "move")))
        (tmp_path / "fail-reload").touch()
        result = _run(script, tmp_path)
        assert result.returncode == 74, result.stderr
        assert result.stdout == ""
        assert "Valid configuration\n" in result.stderr
        assert "reload failed\n" in result.stderr
        assert (tmp_path / "calls").read_text().splitlines() == [
            "render",
            "validate",
            "reload",
        ]
        (tmp_path / "fail-reload").unlink()
        (tmp_path / "reload-failed").unlink()

    assert (tmp_path / "routes").read_text() == (tmp_path / "desired").read_text()
    assert pending.read_text() == "old routes\n"
    assert stat.S_IMODE(pending.stat().st_mode) == 0o640
    assert set(tmp_path.glob("routes.*")) == {tmp_path / "routes.lock", pending}
    _ = (tmp_path / "calls").write_text("", encoding="utf-8")

    result = _run(script, tmp_path)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "changed": True,
        "comment": "Learner routes refreshed",
    }
    assert "Valid configuration\n" in result.stderr
    assert "Reloaded caddy.service.\n" in result.stderr
    assert (tmp_path / "calls").read_text().splitlines() == [
        "render",
        "validate",
        "reload",
    ]
    assert (tmp_path / "routes").read_text() == "new routes\n"
    assert list(tmp_path.glob("routes.*")) == [tmp_path / "routes.lock"]
