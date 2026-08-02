#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import grp
import json
import os
import pwd
import subprocess
import sys
from pathlib import Path
from typing import cast


SUPPORTED_FILESYSTEM_TYPES = {"ext2", "ext3", "ext4"}


class QuotaError(Exception):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class QuotaLimit:
    soft_block_limit_kib: int
    hard_block_limit_kib: int


@dataclasses.dataclass(frozen=True, slots=True)
class FilesystemQuotaPolicy:
    path: str
    group_defaults: dict[str, QuotaLimit]
    user_overrides: dict[str, QuotaLimit]


@dataclasses.dataclass(frozen=True, slots=True)
class TargetUser:
    username: str
    user_id_number: int
    group_names: set[str]


@dataclasses.dataclass(frozen=True, slots=True)
class FilesystemMount:
    target: str
    filesystem_type: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply user filesystem quotas.")
    _ = parser.add_argument(
        "--configuration",
        default="/etc/quotas/user-quotas.json",
        type=Path,
    )
    _ = parser.add_argument("--username")
    _ = parser.add_argument("--user-id-number", type=int)
    _ = parser.add_argument("--group", action="append", default=[], dest="group_names")
    return parser.parse_args()


def load_quota_limit(value: object) -> QuotaLimit:
    if not isinstance(value, dict):
        raise QuotaError("Quota limit must be an object")
    dictionary = cast(dict[str, object], value)
    return QuotaLimit(
        soft_block_limit_kib=load_integer(dictionary["soft_block_limit_kib"]),
        hard_block_limit_kib=load_integer(dictionary["hard_block_limit_kib"]),
    )


def load_integer(value: object) -> int:
    if isinstance(value, bool):
        raise QuotaError("Quota integer values must not be boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise QuotaError("Quota integer values must be integers")


def load_configuration(path: Path) -> list[FilesystemQuotaPolicy]:
    configuration_value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(configuration_value, dict):
        raise QuotaError("Quota configuration must be an object")
    configuration = cast(dict[str, object], configuration_value)
    filesystems_value = configuration.get("filesystems")
    if not isinstance(filesystems_value, dict):
        raise QuotaError("Quota configuration must define filesystems")
    filesystems = cast(dict[str, object], filesystems_value)

    policies: list[FilesystemQuotaPolicy] = []
    for filesystem_value in filesystems.values():
        if not isinstance(filesystem_value, dict):
            raise QuotaError("Filesystem quota policy must be an object")
        filesystem = cast(dict[str, object], filesystem_value)
        group_defaults_value = filesystem.get("group_defaults", {})
        user_overrides_value = filesystem.get("user_overrides", {})
        if not isinstance(group_defaults_value, dict):
            raise QuotaError("Filesystem group defaults must be an object")
        if not isinstance(user_overrides_value, dict):
            raise QuotaError("Filesystem user overrides must be an object")
        group_defaults = cast(dict[str, object], group_defaults_value)
        user_overrides = cast(dict[str, object], user_overrides_value)
        policies.append(
            FilesystemQuotaPolicy(
                path=str(filesystem["path"]),
                group_defaults={
                    group_name: load_quota_limit(limit)
                    for group_name, limit in group_defaults.items()
                },
                user_overrides={
                    username: load_quota_limit(limit)
                    for username, limit in user_overrides.items()
                },
            )
        )
    return policies


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def find_mount(path: str) -> FilesystemMount:
    completed_process = run_command(
        [
            "/usr/bin/findmnt",
            "--json",
            "--target",
            path,
            "--output",
            "TARGET,FSTYPE",
        ]
    )
    data_value = cast(object, json.loads(completed_process.stdout))
    if not isinstance(data_value, dict):
        raise QuotaError(f"Could not parse mount information for {path}")
    data = cast(dict[str, object], data_value)
    filesystems_value = data.get("filesystems")
    if not isinstance(filesystems_value, list) or not filesystems_value:
        raise QuotaError(f"Could not find filesystem containing {path}")
    filesystem_value = cast(list[object], filesystems_value)[0]
    if not isinstance(filesystem_value, dict):
        raise QuotaError(f"Could not parse mount information for {path}")
    filesystem = cast(dict[str, object], filesystem_value)
    return FilesystemMount(
        target=str(filesystem["target"]),
        filesystem_type=str(filesystem["fstype"]),
    )


def ensure_user_quotas_enabled(mount: FilesystemMount) -> None:
    if mount.filesystem_type not in SUPPORTED_FILESYSTEM_TYPES:
        raise QuotaError(
            f"Unsupported filesystem for user quotas: {mount.filesystem_type} on {mount.target}"
        )

    _ = run_command(["/usr/bin/mount", "-o", "remount,usrquota", mount.target])
    if not (Path(mount.target) / "aquota.user").exists():
        _ = run_command(["/usr/sbin/quotacheck", "-cum", mount.target])

    quotaon_process = subprocess.run(
        ["/usr/sbin/quotaon", "-pu", mount.target],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if (
        "user quota" not in quotaon_process.stdout
        or "is on" not in quotaon_process.stdout
    ):
        _ = run_command(["/usr/sbin/quotaon", "-u", mount.target])


def groups_for_user(user: pwd.struct_passwd) -> set[str]:
    try:
        group_id_numbers = os.getgrouplist(user.pw_name, user.pw_gid)
    except OSError as error:
        raise QuotaError(
            f"Could not list groups for {user.pw_name}: {error}"
        ) from error

    group_names: set[str] = set()
    for group_id_number in group_id_numbers:
        try:
            group_names.add(grp.getgrgid(group_id_number).gr_name)
        except KeyError:
            continue
    return group_names


def add_target_user(
    users_by_name: dict[str, TargetUser],
    username: str,
    fallback_group_names: set[str],
) -> None:
    try:
        user = pwd.getpwnam(username)
    except KeyError:
        return

    users_by_name[username] = TargetUser(
        username=user.pw_name,
        user_id_number=user.pw_uid,
        group_names=groups_for_user(user) | fallback_group_names,
    )


def add_policy_group_members(
    users_by_name: dict[str, TargetUser],
    group_name: str,
) -> None:
    try:
        group = grp.getgrnam(group_name)
    except KeyError:
        return

    for username in group.gr_mem:
        add_target_user(users_by_name, username, {group_name})


def target_users_from_policies(
    policies: list[FilesystemQuotaPolicy],
) -> list[TargetUser]:
    users_by_name = {
        user.pw_name: TargetUser(
            username=user.pw_name,
            user_id_number=user.pw_uid,
            group_names=groups_for_user(user),
        )
        for user in pwd.getpwall()
    }

    for policy in policies:
        for group_name in policy.group_defaults:
            add_policy_group_members(users_by_name, group_name)
        for username in policy.user_overrides:
            add_target_user(users_by_name, username, set())

    return list(users_by_name.values())


def target_users(
    username: str | None,
    user_id_number: int | None,
    explicit_group_names: list[str],
    policies: list[FilesystemQuotaPolicy],
) -> list[TargetUser]:
    if username is not None:
        if user_id_number is None:
            try:
                user_id_number = pwd.getpwnam(username).pw_uid
            except KeyError as error:
                raise QuotaError(f"User does not exist: {username}") from error
        return [
            TargetUser(
                username=username,
                user_id_number=user_id_number,
                group_names=set(explicit_group_names)
                if explicit_group_names
                else groups_for_user(pwd.getpwuid(user_id_number)),
            )
        ]

    return target_users_from_policies(policies)


def quota_limit_for_user(
    policy: FilesystemQuotaPolicy,
    user: TargetUser,
) -> QuotaLimit | None:
    if user.username in policy.user_overrides:
        return policy.user_overrides[user.username]

    for group_name, quota_limit in policy.group_defaults.items():
        if group_name in user.group_names:
            return quota_limit
    return None


def apply_quota(
    mount: FilesystemMount,
    user: TargetUser,
    quota_limit: QuotaLimit,
) -> None:
    _ = run_command(
        [
            "/usr/sbin/setquota",
            "-u",
            str(user.user_id_number),
            str(quota_limit.soft_block_limit_kib),
            str(quota_limit.hard_block_limit_kib),
            "0",
            "0",
            mount.target,
        ]
    )


def apply_policies(
    policies: list[FilesystemQuotaPolicy],
    users: list[TargetUser],
) -> None:
    for policy in policies:
        mount = find_mount(policy.path)
        ensure_user_quotas_enabled(mount)
        for user in users:
            quota_limit = quota_limit_for_user(policy, user)
            if quota_limit is not None:
                apply_quota(mount, user, quota_limit)


def main() -> int:
    arguments = parse_arguments()
    policies = load_configuration(arguments.configuration)
    apply_policies(
        policies,
        target_users(
            arguments.username,
            arguments.user_id_number,
            arguments.group_names,
            policies,
        ),
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (QuotaError, subprocess.CalledProcessError) as error:
        print(f"apply-user-quotas: {error}", file=sys.stderr)
        raise SystemExit(1)
