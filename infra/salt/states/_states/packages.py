"""Custom state module for binary package management.

Provides a ``binary_package`` state that handles the full lifecycle:
archive extraction, binary symlinks, optional manpage/completion symlinks.

Supports two scopes:
- system: Installs to /opt/packages/<tool>/ and symlinks to /usr/local/bin/
- user: Installs to ~/.local/packages/<tool>/ and symlinks to ~/.local/bin/
"""

from __future__ import annotations

import os
import shlex
import stat
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import NotRequired, Required, TypedDict

    class Result(TypedDict):
        """Salt state return mapping used by this module."""

        name: str
        result: bool | None
        changes: dict[str, object]
        comment: str

    class ArchEntry(TypedDict, total=False):
        """Package download metadata for one architecture variant."""

        url: Required[str]
        checksum: Required[str]
        libc: str

    class PackagePillar(TypedDict, total=False):
        """Pillar schema for one managed binary package."""

        version: Required[str]
        arch: Required[dict[str, ArchEntry]]
        checksum: str
        strip_components: int
        binaries: list[str] | dict[str, str] | bool
        bin_subdir: str
        manpages: dict[str, str] | bool
        completions: dict[str, str]
        raw_binary: bool
        command_download: bool
        scope: str
        package_dir: NotRequired[str]


__grains__: dict[str, str | dict[str, object]]
__opts__: dict[str, object]
__salt__: dict[str, Callable[..., object]]
__states__: dict[str, Callable[..., "Result"]]


SYSTEM_PACKAGE_DIR = "/opt/packages"
SYSTEM_BIN_DIR = "/usr/local/bin"
SYSTEM_MAN_DIR = "/usr/local/share/man"
SYSTEM_COMPLETION_DIR = "/usr/share/bash-completion/completions"
COMPRESSED_MANPAGE_EXTENSIONS = (".gz", ".bz2", ".xz")


def _no_changes(name: str, comment: str) -> "Result":
    return {"name": name, "result": True, "changes": {}, "comment": comment}


def _error(name: str, comment: str) -> "Result":
    return {"name": name, "result": False, "changes": {}, "comment": comment}


def _resolve_arch_entry(pillar: "PackagePillar") -> "ArchEntry | None":
    cpuarch = __grains__["cpuarch"]
    if not isinstance(cpuarch, str):
        return None
    arch_map = pillar["arch"]
    return arch_map.get(cpuarch) or arch_map.get("any")


def _resolve_url(pillar: "PackagePillar") -> str:
    version = str(pillar["version"])
    entry = _resolve_arch_entry(pillar)
    if entry is None:
        return ""
    return str(entry["url"]).format(version=version)


def _resolve_checksum(pillar: "PackagePillar") -> str:
    entry = _resolve_arch_entry(pillar)
    if entry is None:
        bare = pillar.get("checksum")
        return str(bare) if bare else ""
    checksum = entry.get("checksum")
    return str(checksum) if checksum else ""


VERSION_FILE = ".pkg_version"


def _read_installed_version(package_dir: str) -> str | None:
    version_path = os.path.join(package_dir, VERSION_FILE)
    if os.path.isfile(version_path):
        with open(version_path) as handle:
            return handle.read().strip()
    return None


def _write_installed_version(
    package_dir: str, version: str, user: str | None = None
) -> None:
    version_path = os.path.join(package_dir, VERSION_FILE)
    if not os.path.isdir(package_dir):
        return
    with open(version_path, "w") as handle:
        _ = handle.write(f"{version}\n")
    if user:
        _ = os.chown(version_path, _get_uid(user), _get_gid(user))


def _get_uid(name: str) -> int:
    from pwd import getpwnam

    return getpwnam(name).pw_uid


def _get_gid(name: str) -> int:
    from grp import getgrnam

    return getgrnam(name).gr_gid


def _clean_package_dir(package_dir: str) -> None:
    if os.path.isdir(package_dir):
        _ = __salt__["cmd.run"](
            f"find {package_dir} -mindepth 1 -delete", python_shell=True
        )


def _call_salt_string(function_name: str, *args: object) -> str:
    result = __salt__[function_name](*args)
    if not isinstance(result, str):
        raise TypeError(f"{function_name} must return str, got {type(result).__name__}")
    return result


def _is_test_mode() -> bool:
    return bool(__opts__.get("test", False))


def _get_package_pillar(pillar_prefix: str) -> dict[str, object] | None:
    pillar_result = __salt__["pillar.get"](f"packages:{pillar_prefix}", {}, unmask=True)
    if not isinstance(pillar_result, dict) or not pillar_result:
        return None
    return cast("dict[str, object]", pillar_result)


ARCHIVE_EXTENSIONS = (".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz", ".zip")
PACKAGE_SOURCE_ATTEMPTS = 6
PACKAGE_SOURCE_RETRY_SECONDS = 5
PACKAGE_SOURCE_CONNECT_TIMEOUT_SECONDS = 30
PACKAGE_SOURCE_MAX_TIME_SECONDS = 300


def _is_archive_url(url: str) -> bool:
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in ARCHIVE_EXTENSIONS)


def _download_binary(
    package_dir: str,
    url: str,
    checksum: str,
    user: str | None,
    tool_name: str,
) -> "Result":
    target_path = os.path.join(package_dir, tool_name)
    kwargs: dict[str, object] = {
        "name": target_path,
        "source": url,
        "source_hash": checksum,
        "mode": "0755",
        "makedirs": True,
    }
    if user:
        kwargs["user"] = user
        kwargs["group"] = user
    return __states__["file.managed"](**kwargs)


def _extract_archive(
    package_dir: str,
    url: str,
    checksum: str,
    user: str | None,
    strip_components: int,
) -> "Result":
    kwargs: dict[str, object] = {
        "name": package_dir,
        "source": url,
        "source_hash": checksum,
        "enforce_toplevel": False,
        "force": True,
    }
    if strip_components:
        kwargs["options"] = f"--strip-components={strip_components}"
    if user:
        kwargs["user"] = user
        kwargs["group"] = user
    return __states__["archive.extracted"](**kwargs)


def _tar_option(url: str) -> str:
    path = url.lower().split("?")[0]
    if path.endswith((".tar.gz", ".tgz")):
        return "-xzf"
    if path.endswith((".tar.xz", ".txz")):
        return "-xJf"
    if path.endswith((".tar.bz2", ".tbz2")):
        return "-xjf"
    raise ValueError(f"unsupported command_download archive: {url}")


def _extract_archive_with_command(
    package_dir: str,
    url: str,
    checksum: str,
    user: str | None,
    strip_components: int,
) -> "Result":
    if not checksum.startswith("sha256="):
        return _error(package_dir, "command_download requires a sha256 checksum")

    archive_path = f"{package_dir}.download"
    tar_command = [
        "tar",
        _tar_option(url),
        archive_path,
        "-C",
        package_dir,
    ]
    if strip_components:
        tar_command.append(f"--strip-components={strip_components}")

    command = " && ".join(
        [
            f"install -d -m 0755 {shlex.quote(package_dir)}",
            "curl -fL "
            f"--connect-timeout {PACKAGE_SOURCE_CONNECT_TIMEOUT_SECONDS} "
            f"--max-time {PACKAGE_SOURCE_MAX_TIME_SECONDS} "
            f"--retry {PACKAGE_SOURCE_ATTEMPTS} "
            f"--retry-delay {PACKAGE_SOURCE_RETRY_SECONDS} "
            f"--retry-max-time {PACKAGE_SOURCE_MAX_TIME_SECONDS} "
            f"-o {shlex.quote(archive_path)} {shlex.quote(url)}",
            "printf '%s  %s\n' "
            f"{shlex.quote(checksum.removeprefix('sha256='))} "
            f"{shlex.quote(archive_path)} | sha256sum -c -",
            f"find {shlex.quote(package_dir)} -mindepth 1 -delete",
            shlex.join(tar_command),
            f"rm -f {shlex.quote(archive_path)}",
        ]
    )
    result = __salt__["cmd.run_all"](command, python_shell=True)
    if not isinstance(result, dict):
        return _error(package_dir, "cmd.run_all returned an invalid result")
    command_result = cast("dict[str, object]", result)

    if command_result.get("retcode") != 0:
        return _error(
            package_dir,
            str(command_result.get("stderr") or command_result.get("stdout")),
        )

    if user:
        _ = __salt__["cmd.run"](
            f"chown -R {shlex.quote(user)}:{shlex.quote(user)} "
            f"{shlex.quote(package_dir)}",
            python_shell=True,
        )

    return {
        "name": package_dir,
        "result": True,
        "changes": {"extracted": package_dir},
        "comment": f"{url} downloaded, verified, and extracted to {package_dir}",
    }


def _retry_package_source(name: str, operation: Callable[[], "Result"]) -> "Result":
    comments: list[str] = []
    for attempt_number in range(1, PACKAGE_SOURCE_ATTEMPTS + 1):
        try:
            result = operation()
        except AttributeError as error:
            result = _error(name, f"{type(error).__name__}: {error}")

        if result["result"] is not False:
            return result

        comments.append(str(result["comment"]))
        if attempt_number < PACKAGE_SOURCE_ATTEMPTS:
            time.sleep(PACKAGE_SOURCE_RETRY_SECONDS)

    return _error(
        name,
        f"Package source failed after {PACKAGE_SOURCE_ATTEMPTS} attempts: "
        + " | ".join(comments),
    )


def _ensure_directory(path: str, user: str | None = None) -> "Result":
    kwargs: dict[str, object] = {
        "name": path,
        "mode": "0755",
        "makedirs": True,
    }
    if user:
        kwargs["user"] = user
    return __states__["file.directory"](**kwargs)


def _fix_broken_symlinks(
    package_dir: str,
    resolved_binaries: dict[str, str],
    bin_dir: str,
    user: str | None = None,
) -> "Result":
    all_changes: dict[str, object] = {}
    comments: list[str] = []
    failed = False

    for link_name, binary_name in resolved_binaries.items():
        link_path = f"{bin_dir}/{link_name}"
        if os.path.islink(link_path) and os.path.exists(link_path):
            continue
        resolved = _resolve_binary_path(package_dir, binary_name)
        if resolved is None:
            continue
        symlink_result = _ensure_symlink(link_path, resolved, user)
        if symlink_result["changes"]:
            all_changes[f"symlink:{link_name}"] = symlink_result["changes"]
        if symlink_result["comment"]:
            comments.append(str(symlink_result["comment"]))
        if symlink_result["result"] is False:
            failed = True

    if not all_changes:
        return _no_changes(package_dir, "All symlinks valid")

    final_result: bool | None = False if failed else True
    return {
        "name": package_dir,
        "result": final_result,
        "changes": all_changes,
        "comment": "; ".join(comments) if comments else "Symlinks fixed",
    }


def _resolve_binary_path(package_dir: str, binary_name: str) -> str | None:
    direct = os.path.join(package_dir, binary_name)
    if os.path.isfile(direct):
        return direct
    try:
        for root, dirs, _files in os.walk(package_dir):
            if root == package_dir:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
            candidate = os.path.join(root, binary_name)
            if os.path.isfile(candidate):
                return candidate
    except OSError:
        pass
    return None


def _ensure_symlink(
    link_path: str,
    target_path: str,
    user: str | None = None,
) -> "Result":
    if os.path.islink(link_path):
        current_target = os.readlink(link_path)
        if current_target == target_path:
            return _no_changes(
                link_path, f"Symlink already correct: {link_path} -> {target_path}"
            )
    kwargs: dict[str, object] = {
        "name": link_path,
        "target": target_path,
    }
    if user:
        kwargs["user"] = user
    return __states__["file.symlink"](**kwargs)


def _manpage_section(manpage_name: str) -> int:
    manpage_name = _strip_manpage_compression_suffix(manpage_name)
    parts = manpage_name.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid manpage name: {manpage_name}")
    return int(parts[1])


def _strip_manpage_compression_suffix(manpage_name: str) -> str:
    for extension in COMPRESSED_MANPAGE_EXTENSIONS:
        if manpage_name.endswith(extension):
            return manpage_name[: -len(extension)]
    return manpage_name


def _is_manpage_filename(file_name: str) -> bool:
    try:
        _ = _manpage_section(file_name)
    except ValueError:
        return False
    return True


def _is_man_section_directory(directory_name: str) -> bool:
    return directory_name.startswith("man") and directory_name[3:].isdigit()


def _is_auto_manpage_path(relative_path: str) -> bool:
    parts = relative_path.split(os.sep)
    if any(part.startswith(".") or part.startswith("._") for part in parts):
        return False
    if "node_modules" in parts:
        return False
    if not _is_manpage_filename(os.path.basename(relative_path)):
        return False
    if len(parts) == 1:
        return True
    if parts[0] in {"man", "manpages"}:
        return True
    return (
        len(parts) >= 4
        and parts[0] == "share"
        and parts[1] == "man"
        and _is_man_section_directory(parts[2])
    )


def _discover_manpages(package_dir: str) -> dict[str, str]:
    discovered: dict[str, str] = {}
    try:
        for root, directories, files in os.walk(package_dir):
            directories[:] = sorted(
                directory
                for directory in directories
                if not directory.startswith(".") and directory != "node_modules"
            )
            for file_name in sorted(files):
                if file_name.startswith(".") or file_name.startswith("._"):
                    continue
                relative_path = os.path.relpath(
                    os.path.join(root, file_name), package_dir
                )
                if _is_auto_manpage_path(relative_path):
                    _ = discovered.setdefault(file_name, relative_path)
    except OSError:
        return discovered
    return discovered


def _resolve_manpages(
    package_dir: str,
    manpages: dict[str, str] | bool | None,
) -> dict[str, str] | None:
    if manpages is False:
        return None
    if isinstance(manpages, dict):
        return manpages or None
    discovered = _discover_manpages(package_dir)
    return discovered or None


def _manpage_directory(manpage_name: str, user: str | None = None) -> str:
    section = _manpage_section(manpage_name)
    if user:
        return _call_salt_string("userpaths.get_local_man_dir", user, section)
    return f"{SYSTEM_MAN_DIR}/man{section}"


def _completion_directory(user: str | None = None) -> str:
    if user:
        return _call_salt_string("userpaths.get_bashrc_dir", user)
    return SYSTEM_COMPLETION_DIR


def _repair_supporting_symlinks(
    package_dir: str,
    manpages: dict[str, str] | None,
    completions: dict[str, str] | None,
    user: str | None = None,
) -> "Result":
    all_changes: dict[str, object] = {}
    failed = False

    directories: list[str] = []
    if manpages:
        directories.extend(
            _manpage_directory(manpage_name, user) for manpage_name in manpages
        )
    if completions:
        directories.append(_completion_directory(user))

    for directory in dict.fromkeys(directories):
        directory_result = _ensure_directory(directory, user)
        if directory_result["changes"]:
            all_changes[f"directory:{directory}"] = directory_result["changes"]
        if directory_result["result"] is False:
            failed = True

    if manpages:
        for manpage_name, source_path in manpages.items():
            symlink_result = _ensure_symlink(
                f"{_manpage_directory(manpage_name, user)}/{manpage_name}",
                f"{package_dir}/{source_path}",
                user,
            )
            if symlink_result["changes"]:
                all_changes[f"manpage:{manpage_name}"] = symlink_result["changes"]
            if symlink_result["result"] is False:
                failed = True

    if completions:
        for completion_name, source_path in completions.items():
            symlink_result = _ensure_symlink(
                f"{_completion_directory(user)}/{completion_name}",
                f"{package_dir}/{source_path}",
                user,
            )
            if symlink_result["changes"]:
                all_changes[f"completion:{completion_name}"] = symlink_result["changes"]
            if symlink_result["result"] is False:
                failed = True

    if not all_changes:
        return _no_changes(package_dir, "All supporting symlinks valid")

    return {
        "name": package_dir,
        "result": False if failed else True,
        "changes": all_changes,
        "comment": "Supporting symlinks fixed",
    }


def _binary_source_map(
    name: str,
    binaries: "list[str] | dict[str, str] | None | bool",
    bin_subdir: str | None,
) -> dict[str, str]:
    if isinstance(binaries, dict):
        return binaries
    prefix = f"{bin_subdir}/" if bin_subdir else ""
    if isinstance(binaries, list):
        return {binary: f"{prefix}{binary}" for binary in binaries}
    return {name: f"{prefix}{name}"}


def _fix_binary_modes(package_dir: str, source_map: dict[str, str]) -> "Result":
    all_changes: dict[str, object] = {}
    comments: list[str] = []
    failed = False

    for link_name, source_path in source_map.items():
        target_path = os.path.join(package_dir, source_path)
        if not os.path.exists(target_path):
            resolved = _resolve_binary_path(package_dir, os.path.basename(source_path))
            if resolved is None:
                continue
            target_path = resolved

        try:
            file_status = os.stat(target_path)
        except OSError as error:
            failed = True
            comments.append(f"Could not stat {target_path}: {error}")
            continue

        current_mode = stat.S_IMODE(file_status.st_mode)
        desired_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if current_mode == desired_mode:
            continue

        if not _is_test_mode():
            try:
                os.chmod(target_path, desired_mode)
            except OSError as error:
                failed = True
                comments.append(f"Could not chmod {target_path}: {error}")
                continue

        all_changes[f"mode:{link_name}"] = {
            "old": oct(current_mode),
            "new": oct(desired_mode),
        }

    if not all_changes:
        return _no_changes(package_dir, "All binary modes valid")

    final_result: bool | None
    if failed:
        final_result = False
    elif _is_test_mode():
        final_result = None
    else:
        final_result = True

    return {
        "name": package_dir,
        "result": final_result,
        "changes": all_changes,
        "comment": "; ".join(comments) if comments else "Binary modes fixed",
    }


def _install_system(
    name: str,
    url: str,
    checksum: str,
    strip_components: int,
    binaries: "list[str] | dict[str, str] | None | bool",
    bin_subdir: str | None,
    manpages: dict[str, str] | bool | None,
    completions: dict[str, str] | None,
    package_dir: str,
    version: str,
    is_raw: bool = False,
    command_download: bool = False,
) -> "Result":
    all_changes: dict[str, object] = {}
    comments: list[str] = []
    failed = False

    directories: list[str] = []
    if binaries is not False:
        directories.append(SYSTEM_BIN_DIR)
    if isinstance(manpages, dict):
        for man_file in manpages:
            directories.append(_manpage_directory(man_file))
    if completions:
        directories.append(SYSTEM_COMPLETION_DIR)

    ensured_directories: set[str] = set()
    for directory in dict.fromkeys(directories):
        dir_result = _ensure_directory(directory)
        ensured_directories.add(directory)
        if dir_result["changes"]:
            all_changes[f"directory:{directory}"] = dir_result["changes"]
        if dir_result["result"] is False:
            return {
                "name": name,
                "result": False,
                "changes": all_changes,
                "comment": str(dir_result["comment"]),
            }

    def install_source() -> "Result":
        if command_download and not is_raw:
            return _extract_archive_with_command(
                package_dir, url, checksum, None, strip_components
            )
        return (
            _download_binary(package_dir, url, checksum, None, name)
            if is_raw
            else _extract_archive(package_dir, url, checksum, None, strip_components)
        )

    extract = _retry_package_source(name, install_source)
    if extract["changes"]:
        all_changes["archive"] = extract["changes"]
    if extract["comment"]:
        comments.append(str(extract["comment"]))
    if extract["result"] is False:
        return {
            "name": name,
            "result": False,
            "changes": all_changes,
            "comment": str(extract["comment"]),
        }

    resolved_manpages = _resolve_manpages(package_dir, manpages)

    if binaries is not False:
        links = _binary_source_map(name, binaries, bin_subdir)
        mode_result = _fix_binary_modes(package_dir, links)
        if mode_result["changes"]:
            all_changes["binary_modes"] = mode_result["changes"]
        if (mode_result["changes"] or mode_result["result"] is False) and mode_result[
            "comment"
        ]:
            comments.append(str(mode_result["comment"]))
        if mode_result["result"] is False:
            failed = True

        for link_name, source_path in links.items():
            link_path = f"{SYSTEM_BIN_DIR}/{link_name}"
            target_path = f"{package_dir}/{source_path}"
            if not os.path.exists(target_path):
                resolved = _resolve_binary_path(
                    package_dir, os.path.basename(source_path)
                )
                if resolved is not None:
                    target_path = resolved
            symlink_result = _ensure_symlink(link_path, target_path)
            if symlink_result["changes"]:
                all_changes[f"symlink:{link_name}"] = symlink_result["changes"]
            if symlink_result["comment"]:
                comments.append(str(symlink_result["comment"]))
            if symlink_result["result"] is False and symlink_result["changes"]:
                failed = True

    if resolved_manpages:
        for man_file, source_path in resolved_manpages.items():
            man_dir = _manpage_directory(man_file)
            if man_dir not in ensured_directories:
                dir_result = _ensure_directory(man_dir)
                ensured_directories.add(man_dir)
                if dir_result["changes"]:
                    all_changes[f"directory:{man_dir}"] = dir_result["changes"]
                if dir_result["result"] is False:
                    failed = True
            symlink_result = _ensure_symlink(
                f"{man_dir}/{man_file}", f"{package_dir}/{source_path}"
            )
            if symlink_result["changes"]:
                all_changes[f"manpage:{man_file}"] = symlink_result["changes"]
            if symlink_result["result"] is False and symlink_result["changes"]:
                failed = True

    if completions:
        for comp_name, source_path in completions.items():
            symlink_result = _ensure_symlink(
                f"{SYSTEM_COMPLETION_DIR}/{comp_name}",
                f"{package_dir}/{source_path}",
            )
            if symlink_result["changes"]:
                all_changes[f"completion:{comp_name}"] = symlink_result["changes"]
            if symlink_result["result"] is False and symlink_result["changes"]:
                failed = True

    is_test = _is_test_mode()
    if failed:
        final_result: bool | None = False
    elif is_test and all_changes:
        final_result = None
    else:
        final_result = True

    if not comments:
        if all_changes:
            comments.append(f"{name} {version} installed system-wide")
        else:
            comments.append(f"{name} {version} is already installed system-wide")

    return {
        "name": name,
        "result": final_result,
        "changes": all_changes,
        "comment": "; ".join(comments),
    }


def _install_user(
    name: str,
    user: str,
    url: str,
    checksum: str,
    strip_components: int,
    binaries: "list[str] | dict[str, str] | None | bool",
    bin_subdir: str | None,
    manpages: dict[str, str] | bool | None,
    completions: dict[str, str] | None,
    package_dir_template: str | None = None,
    version: str = "",
    is_raw: bool = False,
    command_download: bool = False,
) -> "Result":
    if package_dir_template:
        home = _call_salt_string("userpaths.get_home", user)
        package_dir = package_dir_template.format(home=home)
    else:
        package_dir = _call_salt_string("userpaths.get_package_dir", user, name)
    local_bin_dir = _call_salt_string("userpaths.get_local_bin_dir", user)
    skip_binaries = binaries is False

    all_changes: dict[str, object] = {}
    comments: list[str] = []
    failed = False

    directories: list[str] = [] if skip_binaries else [local_bin_dir]
    if isinstance(manpages, dict):
        for man_file in manpages:
            directories.append(_manpage_directory(man_file, user))
    if completions:
        directories.append(_call_salt_string("userpaths.get_bashrc_dir", user))

    ensured_directories: set[str] = set()
    for directory in directories:
        dir_result = _ensure_directory(directory, user)
        ensured_directories.add(directory)
        if dir_result["changes"]:
            all_changes[f"directory:{directory}"] = dir_result["changes"]
        if dir_result["result"] is False:
            return {
                "name": name,
                "result": False,
                "changes": all_changes,
                "comment": str(dir_result["comment"]),
            }

    def install_source() -> "Result":
        if command_download and not is_raw:
            return _extract_archive_with_command(
                package_dir, url, checksum, user, strip_components
            )
        return (
            _download_binary(package_dir, url, checksum, user, name)
            if is_raw
            else _extract_archive(package_dir, url, checksum, user, strip_components)
        )

    extract = _retry_package_source(name, install_source)
    if extract["changes"]:
        all_changes["archive"] = extract["changes"]
    if extract["comment"]:
        comments.append(str(extract["comment"]))
    if extract["result"] is False:
        return {
            "name": name,
            "result": False,
            "changes": all_changes,
            "comment": str(extract["comment"]),
        }

    resolved_manpages = _resolve_manpages(package_dir, manpages)

    if not skip_binaries:
        links = _binary_source_map(name, binaries, bin_subdir)
        mode_result = _fix_binary_modes(package_dir, links)
        if mode_result["changes"]:
            all_changes["binary_modes"] = mode_result["changes"]
        if (mode_result["changes"] or mode_result["result"] is False) and mode_result[
            "comment"
        ]:
            comments.append(str(mode_result["comment"]))
        if mode_result["result"] is False:
            failed = True

        for link_name, source_path in links.items():
            link_path = f"{local_bin_dir}/{link_name}"
            target_path = f"{package_dir}/{source_path}"
            if not os.path.exists(target_path):
                resolved = _resolve_binary_path(
                    package_dir, os.path.basename(source_path)
                )
                if resolved is not None:
                    target_path = resolved
            symlink_result = _ensure_symlink(link_path, target_path, user)
            if symlink_result["changes"]:
                all_changes[f"symlink:{link_name}"] = symlink_result["changes"]
            if symlink_result["comment"]:
                comments.append(str(symlink_result["comment"]))
            if symlink_result["result"] is False:
                failed = True

    if resolved_manpages:
        for man_file, source_path in resolved_manpages.items():
            man_dir = _manpage_directory(man_file, user)
            if man_dir not in ensured_directories:
                dir_result = _ensure_directory(man_dir, user)
                ensured_directories.add(man_dir)
                if dir_result["changes"]:
                    all_changes[f"directory:{man_dir}"] = dir_result["changes"]
                if dir_result["result"] is False:
                    failed = True
            symlink_result = _ensure_symlink(
                f"{man_dir}/{man_file}", f"{package_dir}/{source_path}", user
            )
            if symlink_result["changes"]:
                all_changes[f"manpage:{man_file}"] = symlink_result["changes"]
            if symlink_result["result"] is False:
                failed = True

    if completions:
        bashrc_dir = _call_salt_string("userpaths.get_bashrc_dir", user)
        for bashrc_name, source_path in completions.items():
            symlink_result = _ensure_symlink(
                f"{bashrc_dir}/{bashrc_name}",
                f"{package_dir}/{source_path}",
                user,
            )
            if symlink_result["changes"]:
                all_changes[f"completion:{bashrc_name}"] = symlink_result["changes"]
            if symlink_result["result"] is False:
                failed = True

    is_test = _is_test_mode()
    if failed:
        final_result: bool | None = False
    elif is_test and all_changes:
        final_result = None
    else:
        final_result = True

    if not comments:
        if all_changes:
            msg = (
                f"{name} {version} installed for {user}"
                if version
                else f"{name} installed for {user}"
            )
            comments.append(msg)
        else:
            msg = (
                f"{name} {version} is already installed for {user}"
                if version
                else f"{name} is already installed for {user}"
            )
            comments.append(msg)

    return {
        "name": name,
        "result": final_result,
        "changes": all_changes,
        "comment": "; ".join(comments),
    }


def binary_package(
    name: str,
    pillar_key: str | None = None,
    binaries: "list[str] | dict[str, str] | None | bool" = None,
    bin_subdir: str | None = None,
    strip_components: int = 0,
    manpages: dict[str, str] | bool | None = None,
    completions: dict[str, str] | None = None,
    scope: str | None = None,
    user: str | None = None,
    package_dir: str | None = None,
) -> "Result":
    """Ensure a binary package is installed from an archive.

    Supports two scopes:
    - system: Installs to /opt/packages/<tool>/, symlinks to /usr/local/bin/
    - user: Installs to ~/.local/packages/<tool>/, symlinks to ~/.local/bin/

    name
        Tool name or state ID. If a state ID with ``::`` separators is
        passed (e.g. ``packages::fd``), the last segment is used as the
        tool name for pillar lookups and package directories.

    pillar_key
        Pillar key under ``packages:``. Defaults to *name*.

    binaries
        List of binary names to symlink, or a dict mapping
        ``{link_name: source_path}`` relative to the package dir.
        Defaults to ``[name]``. Set to ``False`` to skip binary symlinks.

    bin_subdir
        Subdirectory within the extracted archive where binaries live.

    strip_components
        Value for ``tar --strip-components``. Default ``0``.

    manpages
        Dict mapping ``{filename.section: source_path}`` relative to the
        package dir. Defaults to conservative auto-discovery from package root,
        ``man/``, ``manpages/``, and ``share/man/man*/``. Set to ``False`` to
        disable auto-discovery.

    completions
        Dict mapping ``{completion_name: source_path}`` relative to the
        package dir. For system scope, symlinked to
        ``/usr/share/bash-completion/completions/``. For user scope,
        symlinked to ``~/.bashrc.d/``.

    scope
        Installation scope: ``system`` or ``user``. Defaults to ``system``.

    user
        Username for user-scope installation. Required when scope is ``user``.

    package_dir
        Override the extraction directory. For user scope, supports ``{home}``
        placeholder.
    """
    tool_name = name.rsplit("::", 1)[-1] if "::" in name else name
    pillar_prefix = pillar_key or tool_name

    kernel_value = __grains__["kernel"]
    if not isinstance(kernel_value, str):
        return _error(name, "Invalid grain type: kernel must be a string")
    kernel = kernel_value
    if kernel != "Linux":
        return _no_changes(name, f"Skipped: unsupported kernel {kernel}")

    raw_pillar = _get_package_pillar(pillar_prefix)
    if raw_pillar is None:
        return _error(name, f"Missing pillar key: packages:{pillar_prefix}")

    version_value = raw_pillar.get("version")
    if not isinstance(version_value, str):
        return _error(name, f"Missing pillar key: packages:{pillar_prefix}:version")

    arch_value = raw_pillar.get("arch")
    if not isinstance(arch_value, dict):
        return _error(name, f"Missing pillar key: packages:{pillar_prefix}:arch")

    pillar = cast("PackagePillar", cast(object, raw_pillar))

    if scope is None:
        scope = "system"

    if scope not in ("system", "user"):
        return _error(name, f"Invalid scope: {scope}. Must be 'system' or 'user'")

    if scope == "user" and not user:
        return _error(name, "scope=user requires explicit user parameter")

    url = _resolve_url(pillar)
    if not url:
        cpuarch = __grains__["cpuarch"]
        return _no_changes(name, f"Skipped: no arch entry for {cpuarch}")

    checksum = _resolve_checksum(pillar)
    version: str = str(pillar["version"])
    if strip_components == 0:
        strip_components = int(pillar.get("strip_components", 0))
    if binaries is None:
        pillar_binaries = pillar.get("binaries")
        binaries = pillar_binaries if pillar_binaries is not None else [tool_name]
    if bin_subdir is None:
        bin_subdir = pillar.get("bin_subdir")
    if manpages is None:
        pillar_manpages = pillar.get("manpages")
        manpages = pillar_manpages if pillar_manpages is not None else None
    if completions is None:
        pillar_completions = pillar.get("completions")
        completions = pillar_completions if pillar_completions else None

    is_raw = bool(pillar.get("raw_binary", not _is_archive_url(url)))
    command_download = bool(pillar.get("command_download", False))

    effective_user = user if scope == "user" else None
    if scope == "system":
        resolved_package_dir = package_dir or os.path.join(
            SYSTEM_PACKAGE_DIR, tool_name
        )
    elif package_dir:
        home = _call_salt_string("userpaths.get_home", user)
        resolved_package_dir = package_dir.format(home=home)
    else:
        resolved_package_dir = _call_salt_string(
            "userpaths.get_package_dir",
            user,
            tool_name,
        )

    installed_version = _read_installed_version(resolved_package_dir)
    if installed_version == version:
        changes: dict[str, object] = {}
        comments: list[str] = []
        failed = False
        if binaries is not False:
            source_map = _binary_source_map(tool_name, binaries, bin_subdir)
            bin_dir = (
                SYSTEM_BIN_DIR
                if scope == "system"
                else _call_salt_string("userpaths.get_local_bin_dir", user)
            )
            mode_result = _fix_binary_modes(resolved_package_dir, source_map)
            fix_result = _fix_broken_symlinks(
                resolved_package_dir, source_map, bin_dir, effective_user
            )
            if mode_result["changes"]:
                changes["binary_modes"] = mode_result["changes"]
            if (
                mode_result["changes"] or mode_result["result"] is False
            ) and mode_result["comment"]:
                comments.append(str(mode_result["comment"]))
            if mode_result["result"] is False:
                failed = True
            if fix_result["changes"]:
                changes["symlinks"] = fix_result["changes"]
            if (fix_result["changes"] or fix_result["result"] is False) and fix_result[
                "comment"
            ]:
                comments.append(str(fix_result["comment"]))
            if fix_result["result"] is False:
                failed = True
        supporting_result = _repair_supporting_symlinks(
            resolved_package_dir,
            _resolve_manpages(resolved_package_dir, manpages),
            completions,
            effective_user,
        )
        if supporting_result["changes"]:
            changes["supporting_symlinks"] = supporting_result["changes"]
            comments.append(str(supporting_result["comment"]))
        if supporting_result["result"] is False:
            failed = True
        if changes:
            return {
                "name": name,
                "result": False if failed else True,
                "changes": changes,
                "comment": "; ".join(comments),
            }
        return _no_changes(
            name,
            f"{tool_name} {version} is already installed"
            + (f" for {user}" if user else ""),
        )

    is_test = _is_test_mode()
    if is_test:
        if installed_version:
            comment = (
                f"{tool_name} would be upgraded: {installed_version} -> {version}"
                + (f" for {user}" if user else "")
            )
        else:
            comment = f"{tool_name} {version} would be installed" + (
                f" for {user}" if user else ""
            )
        return {"name": name, "result": None, "changes": {}, "comment": comment}

    if installed_version:
        _clean_package_dir(resolved_package_dir)

    if scope == "system":
        result = _install_system(
            name=tool_name,
            url=url,
            checksum=checksum,
            strip_components=strip_components,
            binaries=binaries,
            bin_subdir=bin_subdir,
            manpages=manpages,
            completions=completions,
            package_dir=resolved_package_dir,
            version=version,
            is_raw=is_raw,
            command_download=command_download,
        )
    else:
        assert user is not None
        result = _install_user(
            name=tool_name,
            user=user,
            url=url,
            checksum=checksum,
            strip_components=strip_components,
            binaries=binaries,
            bin_subdir=bin_subdir,
            manpages=manpages,
            completions=completions,
            package_dir_template=package_dir,
            version=version,
            is_raw=is_raw,
            command_download=command_download,
        )

    if result["result"] is not False:
        _write_installed_version(resolved_package_dir, version, effective_user)

    if installed_version and result["result"] is not False:
        upgrade_msg = f"{tool_name} upgraded: {installed_version} -> {version}" + (
            f" for {user}" if user else ""
        )
        existing_comments = result.get("comment", "")
        result["comment"] = (
            f"{upgrade_msg}; {existing_comments}" if existing_comments else upgrade_msg
        )
        result["changes"]["version"] = {"old": installed_version, "new": version}

    return result
