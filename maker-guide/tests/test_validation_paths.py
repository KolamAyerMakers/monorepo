"""Tests for catalog validation path resolution."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from maker_guide import validation_paths
from maker_guide.validation_paths import (
    UnixAccount,
    UnixAccountLookup,
    open_validation_file,
    resolve_validation_path,
)


def test_resolves_home_relative_and_absolute_paths(tmp_path: Path) -> None:
    """Catalog paths resolve through learner home rules and exact absolute paths."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    nested_file = learner_home / "playground" / "notes.txt"
    nested_file.parent.mkdir()
    nested_file.write_text("notes", encoding="utf-8")
    absolute_file = tmp_path / "system-observation.txt"
    absolute_file.write_text("system", encoding="utf-8")

    home_resolution = resolve_validation_path(
        "alice",
        "~",
        account_lookup=_account_lookup(learner_home),
    )
    explicit_home_resolution = resolve_validation_path(
        "alice",
        "~/playground/notes.txt",
        account_lookup=_account_lookup(learner_home),
    )
    relative_resolution = resolve_validation_path(
        "alice",
        "playground/notes.txt",
        account_lookup=_account_lookup(learner_home),
    )
    absolute_resolution = resolve_validation_path(
        "alice",
        str(absolute_file),
        account_lookup=_account_lookup(learner_home),
    )

    assert home_resolution.failure_reason is None
    assert home_resolution.target_path == learner_home.resolve(strict=True)
    assert explicit_home_resolution.failure_reason is None
    assert explicit_home_resolution.target_path == nested_file.resolve(strict=True)
    assert relative_resolution.failure_reason is None
    assert relative_resolution.target_path == nested_file.resolve(strict=True)
    assert absolute_resolution.failure_reason is None
    assert absolute_resolution.target_path == absolute_file.resolve(strict=True)


@pytest.mark.parametrize(
    "catalog_path",
    [
        "",
        " ",
        r"~\file",
        "../outside",
        "~/../outside",
        "safe/./file",
        "~bob/file",
    ],
)
def test_rejects_unsafe_catalog_paths(tmp_path: Path, catalog_path: str) -> None:
    """Unsafe lexical path declarations fail before filesystem inspection."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    resolution = resolve_validation_path(
        "alice",
        catalog_path,
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "unsafe-path"
    assert resolution.target_path is None


def test_reports_unknown_user(tmp_path: Path) -> None:
    """Missing Unix accounts produce a stable unknown-user failure."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    resolution = resolve_validation_path(
        "bob",
        "~/notes.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "unknown-user"
    assert resolution.home_path is None


def test_reports_missing_path(tmp_path: Path) -> None:
    """Nonexistent targets produce a stable missing-path failure."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    resolution = resolve_validation_path(
        "alice",
        "~/missing.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "missing-path"
    assert resolution.candidate_path == learner_home / "missing.txt"


def test_follows_in_scope_symlink(tmp_path: Path) -> None:
    """Learner-home symlinks pass when their resolved target stays in scope."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    target_file = learner_home / "target.txt"
    target_file.write_text("target", encoding="utf-8")
    (learner_home / "link.txt").symlink_to(target_file)

    resolution = resolve_validation_path(
        "alice",
        "link.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason is None
    assert resolution.target_path == target_file.resolve(strict=True)


def test_rejects_learner_home_symlink_escape(tmp_path: Path) -> None:
    """Learner-home symlinks fail when their resolved target escapes home."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    (learner_home / "outside-link.txt").symlink_to(outside_file)

    resolution = resolve_validation_path(
        "alice",
        "outside-link.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "path-escapes-scope"
    assert resolution.target_path == outside_file.resolve(strict=True)


def test_allows_declared_absolute_symlink_target(tmp_path: Path) -> None:
    """Exact absolute catalog paths are allowed to resolve outside learner home."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    absolute_link = tmp_path / "absolute-link.txt"
    absolute_link.symlink_to(outside_file)

    resolution = resolve_validation_path(
        "alice",
        str(absolute_link),
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason is None
    assert resolution.target_path == outside_file.resolve(strict=True)


def test_reports_broken_symlink(tmp_path: Path) -> None:
    """Broken symlinks get a distinct stable failure reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    (learner_home / "broken-link.txt").symlink_to(learner_home / "missing-target.txt")

    resolution = resolve_validation_path(
        "alice",
        "broken-link.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "broken-symlink"


def test_reports_symlink_loop(tmp_path: Path) -> None:
    """Symlink loops get a distinct stable failure reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    link_one = learner_home / "link-one.txt"
    link_two = learner_home / "link-two.txt"
    link_one.symlink_to(link_two)
    link_two.symlink_to(link_one)

    resolution = resolve_validation_path(
        "alice",
        "link-one.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "symlink-loop"


def test_reports_permission_denied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Permission errors are converted into learner-facing failure reasons."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    secret_file = learner_home / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")
    original_resolve = Path.resolve

    def resolve_with_permission_error(path: Path, *, strict: bool = False) -> Path:
        if path == secret_file:
            raise PermissionError
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_permission_error)

    resolution = resolve_validation_path(
        "alice",
        "secret.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert resolution.failure_reason == "permission-denied"


def test_open_validation_file_rejects_swapped_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Descriptor validation rejects a symlink swapped outside home before open."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    inside_file = learner_home / "inside.txt"
    inside_file.write_text("inside", encoding="utf-8")
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    link_path = learner_home / "link.txt"
    link_path.symlink_to(inside_file)
    original_open = validation_paths.os.open

    def open_after_symlink_swap(path: Path, flags: int) -> int:
        if path == link_path:
            link_path.unlink()
            link_path.symlink_to(outside_file)
        return original_open(path, flags)

    monkeypatch.setattr(validation_paths.os, "open", open_after_symlink_swap)

    opened_file = open_validation_file(
        "alice",
        "link.txt",
        account_lookup=_account_lookup(learner_home),
    )

    assert opened_file.failure_reason == "path-escapes-scope"
    assert opened_file.file_descriptor is None


def test_open_validation_file_rejects_parent_symlink_swapped_outside_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Descriptor validation rejects a parent symlink swapped outside home before open."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    inside_directory = learner_home / "inside"
    inside_directory.mkdir()
    (inside_directory / "hostname").write_text("inside", encoding="utf-8")
    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()
    (outside_directory / "hostname").write_text("outside", encoding="utf-8")
    workspace_link = learner_home / "workspace"
    workspace_link.symlink_to(inside_directory, target_is_directory=True)
    original_open = validation_paths.os.open

    def open_after_parent_symlink_swap(path: Path, flags: int) -> int:
        if path == workspace_link / "hostname":
            workspace_link.unlink()
            workspace_link.symlink_to(outside_directory, target_is_directory=True)
        return original_open(path, flags)

    monkeypatch.setattr(validation_paths.os, "open", open_after_parent_symlink_swap)

    opened_file = open_validation_file(
        "alice",
        "workspace/hostname",
        account_lookup=_account_lookup(learner_home),
    )

    assert opened_file.failure_reason == "path-escapes-scope"
    assert opened_file.file_descriptor is None


def test_open_validation_file_reads_same_descriptor_after_path_swap(tmp_path: Path) -> None:
    """Opened validation descriptors keep pointing at the file that was validated."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    notes_file = learner_home / "notes.txt"
    notes_file.write_text("ready", encoding="utf-8")

    opened_file = open_validation_file(
        "alice",
        "notes.txt",
        account_lookup=_account_lookup(learner_home),
    )
    try:
        replacement_file = learner_home / "replacement.txt"
        replacement_file.write_text("changed", encoding="utf-8")
        notes_file.unlink()
        replacement_file.rename(notes_file)
        assert opened_file.failure_reason is None
        assert opened_file.file_descriptor is not None
        assert os.read(opened_file.file_descriptor, 32) == b"ready"
    finally:
        if opened_file.file_descriptor is not None:
            os.close(opened_file.file_descriptor)


def test_open_validation_file_reports_not_regular_from_descriptor(tmp_path: Path) -> None:
    """Descriptor validation reports directories as non-regular files."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    (learner_home / "workspace").mkdir()

    opened_file = open_validation_file(
        "alice",
        "workspace",
        account_lookup=_account_lookup(learner_home),
    )

    assert opened_file.failure_reason == "not-regular-file"
    assert opened_file.file_descriptor is None


def test_open_validation_file_reports_fifo_without_blocking(tmp_path: Path) -> None:
    """FIFO paths are opened nonblocking and rejected as non-regular files."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    os.mkfifo(learner_home / "pipe")

    opened_file = open_validation_file(
        "alice",
        "pipe",
        account_lookup=_account_lookup(learner_home),
    )

    assert opened_file.failure_reason == "not-regular-file"
    assert opened_file.file_descriptor is None


def _account_lookup(learner_home: Path) -> UnixAccountLookup:
    def lookup(handle: str) -> UnixAccount | None:
        if handle != "alice":
            return None
        return UnixAccount(handle=handle, user_id=4242, home_directory=learner_home)

    return lookup
