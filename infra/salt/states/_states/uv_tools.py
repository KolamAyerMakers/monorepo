"""Custom state module for Python tool management via uv.

Provides an ``installed`` state that uses ``uv tool install`` to manage
Python CLI tools in isolated virtualenvs under ``/opt/uv_tools/``.

Entry-point scripts are placed in ``/opt/uv_tools/bin/`` which should
be added to the system PATH.

When a *checksum* is provided, the wheel is downloaded from PyPI,
verified against the expected hash, then installed from the local
file — ensuring supply-chain integrity.

Requires ``uv`` to be available on the system (installed via the ``uv``
Salt state).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypedDict

    class Result(TypedDict):
        """Salt state return mapping used by this module."""

        name: str
        result: bool | None
        changes: dict[str, object]
        comment: str


__opts__: dict[str, object]

BASE_DIRECTORY = "/opt/uv_tools"
BIN_DIRECTORY = "/opt/uv_tools/bin"
_CACHE_DIRECTORY = "/var/cache/salt/uv_tools"


def _no_changes(name: str, comment: str) -> "Result":
    return {"name": name, "result": True, "changes": {}, "comment": comment}


def _error(name: str, comment: str) -> "Result":
    return {"name": name, "result": False, "changes": {}, "comment": comment}


def _uv_environment() -> dict[str, str]:
    return {
        "UV_TOOL_DIR": BASE_DIRECTORY,
        "UV_TOOL_BIN_DIR": BIN_DIRECTORY,
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    }


def _installed_version(package: str) -> str | None:
    """Return the currently installed version, or None."""
    environment = _uv_environment()
    try:
        output = subprocess.check_output(
            ["uv", "tool", "list"],
            env=environment,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    # uv tool list output: "kea-exporter v0.7.0"
    for line in output.splitlines():
        if line.startswith(package + " "):
            return line.split(" v", 1)[-1].strip()
    return None


def _sha256_file(path: str) -> str:
    """Compute the SHA-256 hex digest of a file."""
    file_hash = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(65536):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def _find_wheel_url(package: str, version: str) -> tuple[str | None, str]:
    """Query PyPI JSON API for the wheel URL.

    Returns ``(url, "")`` on success or ``(None, error_message)`` on failure.
    """
    api_url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(api_url, timeout=30) as response:
            data = json.loads(response.read())
    except Exception as error:  # noqa: BLE001
        return None, f"PyPI API request failed: {error}"
    for entry in data.get("urls", []):
        if entry.get("packagetype") == "bdist_wheel":
            url: str = entry["url"]
            return url, ""
    return None, f"no wheel found on PyPI for {package}=={version}"


def _download_wheel(package: str, version: str) -> tuple[str | None, str]:
    """Download a wheel from PyPI to the local cache.

    Returns ``(path, "")`` on success or ``(None, error_message)`` on failure.
    """
    wheel_url, error = _find_wheel_url(package, version)
    if wheel_url is None:
        return None, error
    filename = os.path.basename(wheel_url.split("?")[0])
    download_directory = os.path.join(_CACHE_DIRECTORY, package, version)
    os.makedirs(download_directory, exist_ok=True)
    destination = os.path.join(download_directory, filename)
    try:
        _ = urllib.request.urlretrieve(wheel_url, destination)  # noqa: S310
    except Exception as download_error:  # noqa: BLE001
        return None, f"download failed: {download_error}"
    return destination, ""


def installed(
    name: str,
    version: str | None = None,
    package: str | None = None,
    checksum: str | None = None,
) -> "Result":
    """Ensure a Python tool is installed via ``uv tool install``.

    The tool is installed into an isolated virtualenv under
    ``/opt/uv_tools/<package>/`` with entry-point scripts in
    ``/opt/uv_tools/bin/``.

    name
        State ID.  Used as the package name if *package* is not set.

    version
        Required version string (e.g. ``"0.7.0"``).

    package
        PyPI package name.  Defaults to *name*.

    checksum
        Expected SHA-256 hex digest of the wheel.  When set, the wheel
        is downloaded from PyPI, verified against this hash, then
        installed from the local copy.
    """
    package = package or name
    if not version:
        return _error(name, "version is required")

    current_version = _installed_version(package)
    if current_version == version:
        return _no_changes(name, f"{package} {version} is already installed")

    is_test = bool(__opts__.get("test", False))
    if is_test:
        if current_version:
            comment = f"{package} would be upgraded: {current_version} -> {version}"
        else:
            comment = f"{package} {version} would be installed"
        return {"name": name, "result": None, "changes": {}, "comment": comment}

    # Download, verify, and determine the install target
    install_target: str
    if checksum:
        wheel_path, download_error = _download_wheel(package, version)
        if wheel_path is None:
            return _error(name, f"download {package}=={version}: {download_error}")
        actual_hash = _sha256_file(wheel_path)
        expected_hash = checksum.removeprefix("sha256=")
        if actual_hash != expected_hash:
            os.remove(wheel_path)
            return _error(
                name,
                f"checksum mismatch: expected {expected_hash}, got {actual_hash}",
            )
        install_target = wheel_path
    else:
        install_target = f"{package}=={version}"

    environment = _uv_environment()
    command = ["uv", "tool", "install", install_target]
    if current_version:
        command.append("--force")

    try:
        _ = subprocess.check_output(
            command,
            env=environment,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as error:
        return _error(name, f"uv tool install failed: {error.output}")

    changes: dict[str, object] = {"installed": f"{package}=={version}"}
    if current_version:
        changes["previous"] = current_version

    return {
        "name": name,
        "result": True,
        "changes": changes,
        "comment": f"{package} {version} installed",
    }
