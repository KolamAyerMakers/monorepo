"""Assemble managed files from fragments registered by multiple states.

The state module provides a small Puppet-style concat primitive for Salt. A
state can register ordered fragments for a target file, and a separate managed
state assembles those fragments atomically, optionally validating the final
contents before replacing the target.
"""

from __future__ import annotations

import difflib
import grp
import os
import pwd
import stat
import tempfile
from collections.abc import Callable, Mapping
from typing import Required, TypedDict, cast


class Result(TypedDict):
    """Salt state return mapping used by this module."""

    name: str
    result: bool | None
    changes: dict[str, object]
    comment: str


class Fragment(TypedDict):
    """Registered concat fragment tracked during one Salt state run."""

    identity: Required[str]
    position: Required[str]
    fragment_name: Required[str]
    contents: Required[str]


__opts__: dict[str, object] = {}
__salt__: dict[str, Callable[..., object]] = {}
__context__: dict[str, object] = {}

__virtualname__ = "concat"

CONTEXT_PREFIX = "concat.fragments:"


def __virtual__() -> str:
    return __virtualname__


def fragment(
    name: str,
    target: str,
    contents: str | None = None,
    content: str | None = None,
    source: str | None = None,
    position: str = "50",
) -> Result:
    """Register one ordered fragment for a later `concat.managed` assembly.

    Use `target` to select the output file, `position` to control ordering, and
    exactly one of `contents`, `content`, or `source` to provide the fragment
    text. Fragments are held in Salt's per-run context, so the target must also
    have a `concat.managed` state in the same state run.
    """
    payload = _resolve_payload(contents=contents, content=content, source=source)
    if payload is None:
        return _failure(name, "Specify exactly one of contents, content, or source")

    fragment_name = _safe_fragment_name(name)
    identity = f"{position}__{fragment_name}"
    fragments = _target_fragments(target)
    if identity in fragments:
        return _failure(
            name,
            f"Duplicate concat fragment {identity!r} for target {target!r}",
        )

    fragments[identity] = {
        "identity": identity,
        "position": position,
        "fragment_name": fragment_name,
        "contents": payload,
    }

    return {
        "name": name,
        "result": True,
        "changes": {},
        "comment": f"Registered concat fragment {name!r} for {target}",
    }


def managed(
    name: str,
    user: str = "root",
    group: str = "root",
    mode: str = "0644",
    header: str = "",
    footer: str = "",
    separator: str = "",
    ensure_newline: bool = True,
    validate_cmd: str | None = None,
) -> Result:
    """Assemble registered fragments into the file named by `name`.

    Declare this state once per target file after all contributing states are
    included. The assembled file can include optional `header`, `footer`, and
    `separator` text, and `validate_cmd` may reference `%s` to test a temporary
    file before the atomic write.
    """
    fragments = _sorted_fragments(name)
    if not fragments:
        return _failure(name, f"No concat fragments registered for {name!r}")

    parts = [header]
    parts.extend(fragment["contents"] for fragment in fragments)
    parts.append(footer)
    new_contents = separator.join(part for part in parts if part)
    if ensure_newline and not new_contents.endswith("\n"):
        new_contents = f"{new_contents}\n"

    exists = os.path.exists(name)
    old_contents = _read_file(name)
    if exists and old_contents == new_contents:
        try:
            metadata_changes = _metadata_changes(
                name, user=user, group=group, mode=mode
            )
        except OSError as error:
            return _failure(name, f"Failed to inspect metadata for {name}: {error}")
        except KeyError as error:
            return _failure(name, f"Failed to resolve owner for {name}: {error}")

        if not metadata_changes:
            return {
                "name": name,
                "result": True,
                "changes": {},
                "comment": f"{name} is up to date from {len(fragments)} fragments",
            }

        if _test_mode():
            return {
                "name": name,
                "result": None,
                "changes": metadata_changes,
                "comment": f"Would update metadata for {name}",
            }

        try:
            _apply_metadata(name, user=user, group=group, mode=mode)
        except OSError as error:
            return _failure(name, f"Failed to update metadata for {name}: {error}")
        except KeyError as error:
            return _failure(name, f"Failed to resolve owner for {name}: {error}")

        return {
            "name": name,
            "result": True,
            "changes": metadata_changes,
            "comment": f"Updated metadata for {name}",
        }

    if _test_mode():
        return {
            "name": name,
            "result": None,
            "changes": {"diff": _diff(old_contents, new_contents, name)},
            "comment": f"Would assemble {name} from {len(fragments)} fragments",
        }

    validation_error = _validate(name, new_contents, validate_cmd)
    if validation_error:
        return _failure(name, validation_error)

    try:
        _atomic_write(name, new_contents, user=user, group=group, mode=mode)
    except OSError as error:
        return _failure(name, f"Failed to write {name}: {error}")
    except KeyError as error:
        return _failure(name, f"Failed to resolve owner for {name}: {error}")

    action = "updated" if old_contents else "created"
    return {
        "name": name,
        "result": True,
        "changes": {
            name: action,
            "fragments": len(fragments),
            "diff": _diff(old_contents, new_contents, name),
        },
        "comment": f"Assembled {name} from {len(fragments)} fragments",
    }


def _resolve_payload(
    *,
    contents: str | None,
    content: str | None,
    source: str | None,
) -> str | None:
    payloads = [value for value in (contents, content, source) if value is not None]
    if len(payloads) != 1:
        return None

    if source is None:
        return contents if contents is not None else content

    cached_source = __salt__["cp.cache_file"](source)
    if not isinstance(cached_source, str) or not cached_source:
        return None
    with open(cached_source, encoding="utf-8") as source_file:
        return source_file.read()


def _target_fragments(target: str) -> dict[str, Fragment]:
    context_key = f"{CONTEXT_PREFIX}{target}"
    existing = __context__.setdefault(context_key, {})
    if not isinstance(existing, dict):
        raise TypeError(f"{context_key} must be a dict")
    return cast(dict[str, Fragment], existing)


def _sorted_fragments(target: str) -> list[Fragment]:
    return [
        fragment for _identity, fragment in sorted(_target_fragments(target).items())
    ]


def _safe_fragment_name(value: str) -> str:
    return value.replace("/", "_").replace("\x00", "_").replace("\n", "_")


def _read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as existing_file:
        return existing_file.read()


def _validate(path: str, contents: str, validate_cmd: str | None) -> str:
    if not validate_cmd:
        return ""

    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=parent,
        prefix=f".{os.path.basename(path)}.concat-check-",
        delete=False,
    ) as temporary_file:
        _ = temporary_file.write(contents)
        temporary_path = temporary_file.name

    try:
        command = (
            validate_cmd.replace("%s", temporary_path)
            if "%s" in validate_cmd
            else f"{validate_cmd} {temporary_path}"
        )
        result = __salt__["cmd.run_all"](command, python_shell=True)
        if not isinstance(result, dict):
            return f"Validation command returned {type(result).__name__}"
        result_mapping = cast(Mapping[str, object], result)
        if result_mapping.get("retcode") != 0:
            output = _string_result(
                result_mapping.get("stderr"),
            ) or _string_result(result_mapping.get("stdout"))
            return f"Validation failed for {path}: {output}"
    finally:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
    return ""


def _atomic_write(
    path: str, contents: str, *, user: str, group: str, mode: str
) -> None:
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(
        dir=parent,
        prefix=f".{os.path.basename(path)}.concat-",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            _ = temporary_file.write(contents)
        os.chown(temporary_path, pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)
        os.chmod(temporary_path, int(mode, 8))
        os.replace(temporary_path, path)
    except BaseException:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise


def _metadata_changes(
    path: str, *, user: str, group: str, mode: str
) -> dict[str, object]:
    file_stat = os.stat(path)
    desired_uid = pwd.getpwnam(user).pw_uid
    desired_gid = grp.getgrnam(group).gr_gid
    desired_mode = int(mode, 8)
    current_mode = stat.S_IMODE(file_stat.st_mode)

    changes: dict[str, object] = {}
    if file_stat.st_uid != desired_uid:
        changes["user"] = {"old": _user_name(file_stat.st_uid), "new": user}
    if file_stat.st_gid != desired_gid:
        changes["group"] = {"old": _group_name(file_stat.st_gid), "new": group}
    if current_mode != desired_mode:
        changes["mode"] = {
            "old": f"{current_mode:04o}",
            "new": f"{desired_mode:04o}",
        }
    return changes


def _apply_metadata(path: str, *, user: str, group: str, mode: str) -> None:
    os.chown(path, pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)
    os.chmod(path, int(mode, 8))


def _user_name(uid: int) -> str:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _group_name(gid: int) -> str:
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def _string_result(value: object) -> str:
    if isinstance(value, str):
        return value
    return ""


def _diff(old_contents: str, new_contents: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            old_contents.splitlines(keepends=True),
            new_contents.splitlines(keepends=True),
            fromfile=f"{path} (old)",
            tofile=f"{path} (new)",
        )
    )


def _test_mode() -> bool:
    return bool(__opts__.get("test", False))


def _failure(name: str, comment: str) -> "Result":
    return {"name": name, "result": False, "changes": {}, "comment": comment}
