#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast


USER_ATTRIBUTES = {
    "uidNumber": ("INTEGER", False, True, False),
    "gidNumber": ("INTEGER", False, True, False),
    "homeDirectory": ("STRING", False, True, False),
    "unixShell": ("STRING", False, True, False),
    "sshPublicKey": ("STRING", True, True, True),
}
SCHEMA_ALREADY_EXISTS_MARKERS = (
    "UNIQUE constraint failed: user_attribute_schema.user_attribute_schema_name",
    "UNIQUE constraint failed: user_object_class_schema.user_object_class_schema_name",
)


class LldapError(Exception):
    pass


def is_schema_already_exists_error(error: LldapError) -> bool:
    error_message = str(error)
    return any(marker in error_message for marker in SCHEMA_ALREADY_EXISTS_MARKERS)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure an LLDAP POSIX user exists.")
    _ = parser.add_argument("username")
    _ = parser.add_argument("--uid-number", type=int, required=True)
    _ = parser.add_argument("--display-name", required=True)
    _ = parser.add_argument("--email", required=True)
    _ = parser.add_argument("--home-directory", required=True)
    _ = parser.add_argument("--shell", required=True)
    _ = parser.add_argument("--primary-group", required=True)
    _ = parser.add_argument(
        "--secondary-group",
        action="append",
        default=[],
        dest="secondary_group_names",
    )
    _ = parser.add_argument(
        "--ssh-public-key",
        action="append",
        default=[],
        dest="ssh_public_keys",
    )
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--check", action="store_true")
    _ = parser.add_argument("--skip-sss-cache", action="store_true")
    return parser.parse_args()


def read_environment_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        if "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", 1)
        values[key] = value
    return values


def append_path(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def post_json(
    url: str,
    payload: dict[str, object],
    token: str | None = None,
) -> dict[str, object]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return cast(dict[str, object], json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise LldapError(f"HTTP {error.code} from {url}: {body}") from error
    except urllib.error.URLError as error:
        raise LldapError(f"Could not connect to {url}: {error}") from error


def login(base_url: str, username: str, password: str) -> str:
    response = post_json(
        append_path(base_url, "/auth/simple/login"),
        {"username": username, "password": password},
    )
    try:
        return str(response["token"])
    except KeyError as error:
        raise LldapError("Login response did not contain a token") from error


def graphql(
    base_url: str,
    token: str,
    query: str,
    variables: dict[str, object],
) -> dict[str, object]:
    response = post_json(
        append_path(base_url, "/api/graphql"),
        {"query": query, "variables": variables},
        token=token,
    )
    if response.get("errors"):
        raise LldapError(json.dumps(response["errors"], indent=2))
    data = response.get("data")
    if not isinstance(data, dict):
        raise LldapError("GraphQL response did not contain a data object")
    return cast(dict[str, object], data)


def load_schema(base_url: str, token: str) -> dict[str, object]:
    schema = graphql(
        base_url,
        token,
        """
        query LoadSchema {
          schema {
            userSchema {
              attributes { name }
              ldapObjectClasses { objectClass }
            }
          }
        }
        """,
        {},
    )["schema"]
    if not isinstance(schema, dict):
        raise LldapError("GraphQL schema query did not return a schema object")
    return cast(dict[str, object], schema)


def ensure_user_attribute(
    base_url: str,
    token: str,
    name: str,
    attribute_type: str,
    is_list: bool,
    is_visible: bool,
    is_editable: bool,
) -> None:
    try:
        _ = graphql(
            base_url,
            token,
            """
            mutation AddUserAttribute(
              $name: String!,
              $attributeType: AttributeType!,
              $isList: Boolean!,
              $isVisible: Boolean!,
              $isEditable: Boolean!
            ) {
              addUserAttribute(
                name: $name,
                attributeType: $attributeType,
                isList: $isList,
                isVisible: $isVisible,
                isEditable: $isEditable
              ) { ok }
            }
            """,
            {
                "name": name,
                "attributeType": attribute_type,
                "isList": is_list,
                "isVisible": is_visible,
                "isEditable": is_editable,
            },
        )
    except LldapError as error:
        if is_schema_already_exists_error(error):
            return
        raise


def ensure_schema(base_url: str, token: str) -> None:
    schema = load_schema(base_url, token)
    user_schema = cast(dict[str, object], schema["userSchema"])
    user_attributes = cast(list[dict[str, object]], user_schema["attributes"])
    existing_user_attributes = {
        str(attribute["name"]).lower() for attribute in user_attributes
    }
    for name, attribute_settings in USER_ATTRIBUTES.items():
        if name.lower() not in existing_user_attributes:
            ensure_user_attribute(base_url, token, name, *attribute_settings)

    object_class_items = cast(
        list[dict[str, object]],
        user_schema["ldapObjectClasses"],
    )
    object_classes = {str(item["objectClass"]).lower() for item in object_class_items}
    if "posixaccount" in object_classes:
        return
    try:
        _ = graphql(
            base_url,
            token,
            "mutation AddUserObjectClass($name: String!) { addUserObjectClass(name: $name) { ok } }",
            {"name": "posixAccount"},
        )
    except LldapError as error:
        if not is_schema_already_exists_error(error):
            raise


def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
    groups = graphql(
        base_url,
        token,
        """
        query LoadGroups {
          groups {
            id
            displayName
            attributes { name value }
          }
        }
        """,
        {},
    )["groups"]
    return cast(list[dict[str, object]], groups)


def load_users(base_url: str, token: str) -> list[dict[str, object]]:
    users = graphql(
        base_url,
        token,
        """
        query LoadUsers {
          users {
            id
            email
            displayName
            attributes { name value }
            groups { id displayName }
          }
        }
        """,
        {},
    )["users"]
    return cast(list[dict[str, object]], users)


def attribute_value(item: dict[str, object], name: str) -> str | None:
    values = attribute_values(item, name)
    return values[0] if values else None


def attribute_values(item: dict[str, object], name: str) -> list[str]:
    for attribute in cast(list[dict[str, object]], item["attributes"]):
        if str(attribute["name"]).lower() != name.lower():
            continue
        return cast(list[str], attribute["value"])
    return []


def integer_attribute_value(item: dict[str, object], name: str) -> int | None:
    value = attribute_value(item, name)
    return int(value) if value is not None else None


def group_id_number(group: dict[str, object]) -> int | None:
    return integer_attribute_value(group, "gidNumber")


def user_id_number(user: dict[str, object]) -> int | None:
    return integer_attribute_value(user, "uidNumber")


def find_group(
    groups: list[dict[str, object]],
    group_name: str,
) -> dict[str, object] | None:
    for group in groups:
        if group["displayName"] == group_name:
            return group
    return None


def find_user(
    users: list[dict[str, object]],
    username: str,
) -> dict[str, object] | None:
    for user in users:
        if user["id"] == username:
            return user
    return None


def resolve_group(
    groups: list[dict[str, object]],
    group_name: str,
) -> tuple[int, int]:
    group = find_group(groups, group_name)
    if group is None:
        raise LldapError(f"Group {group_name} does not exist; run Salt to create it")
    group_identifier = int(str(group["id"]))
    existing_group_id_number = group_id_number(group)
    if existing_group_id_number is None:
        raise LldapError(
            f"Group {group_name} does not define gidNumber; run Salt to prepare managed groups"
        )
    return group_identifier, existing_group_id_number


def expected_attributes(
    arguments: argparse.Namespace,
    group_id_number_value: int,
) -> dict[str, list[str]]:
    attributes = {
        "uidNumber": [str(arguments.uid_number)],
        "gidNumber": [str(group_id_number_value)],
        "homeDirectory": [str(arguments.home_directory)],
        "unixShell": [str(arguments.shell)],
    }
    if arguments.ssh_public_keys:
        attributes["sshPublicKey"] = list(dict.fromkeys(arguments.ssh_public_keys))
    return attributes


def validate_user_id_number_available(
    users: list[dict[str, object]],
    username: str,
    user_id_number_value: int,
) -> None:
    for user in users:
        if user["id"] == username:
            continue
        if user_id_number(user) == user_id_number_value:
            raise LldapError(
                f"uidNumber {user_id_number_value} is already used by {user['id']}"
            )


def create_user(
    arguments: argparse.Namespace,
    base_url: str,
    token: str,
    group_id_number_value: int,
) -> None:
    _ = graphql(
        base_url,
        token,
        """
        mutation CreateUser($user: CreateUserInput!) {
          createUser(user: $user) { id }
        }
        """,
        {
            "user": {
                "id": arguments.username,
                "email": arguments.email,
                "displayName": arguments.display_name,
                "attributes": [
                    {"name": name, "value": values}
                    for name, values in expected_attributes(
                        arguments, group_id_number_value
                    ).items()
                ],
            }
        },
    )


def update_user(
    arguments: argparse.Namespace,
    base_url: str,
    token: str,
    changed_attributes: dict[str, list[str]],
) -> None:
    user_input: dict[str, object] = {"id": arguments.username}
    if changed_attributes:
        user_input["insertAttributes"] = [
            {"name": name, "value": values}
            for name, values in changed_attributes.items()
        ]
    if arguments.email is not None:
        user_input["email"] = arguments.email
    if arguments.display_name is not None:
        user_input["displayName"] = arguments.display_name
    _ = graphql(
        base_url,
        token,
        """
        mutation UpdateUser($user: UpdateUserInput!) {
          updateUser(user: $user) { ok }
        }
        """,
        {"user": user_input},
    )


def add_user_to_group(
    base_url: str,
    token: str,
    username: str,
    group_identifier: int,
) -> None:
    _ = graphql(
        base_url,
        token,
        """
        mutation AddUserToGroup($userId: String!, $groupId: Int!) {
          addUserToGroup(userId: $userId, groupId: $groupId) { ok }
        }
        """,
        {"userId": username, "groupId": group_identifier},
    )


def changed_user_attributes(
    user: dict[str, object],
    expected_user_attributes: dict[str, list[str]],
) -> dict[str, list[str]]:
    changed_attributes: dict[str, list[str]] = {}
    for name, expected_values in expected_user_attributes.items():
        current_values = attribute_values(user, name)
        if (
            name.lower() in {"uidnumber", "gidnumber"}
            and current_values
            and current_values != expected_values
        ):
            raise LldapError(
                f"User {user['id']} has {name} {current_values[0]}, expected {expected_values[0]}"
            )
        if current_values != expected_values:
            changed_attributes[name] = expected_values
    return changed_attributes


def user_group_names(user: dict[str, object]) -> set[str]:
    return {
        str(group["displayName"])
        for group in cast(list[dict[str, object]], user["groups"])
    }


def migrate_group_members(
    base_url: str,
    token: str,
    legacy_group_name: str,
    target_group_names: list[str],
    check_only: bool,
) -> bool:
    groups = load_groups(base_url, token)
    _ = resolve_group(groups, legacy_group_name)
    target_group_identifiers = {
        group_name: resolve_group(groups, group_name)[0]
        for group_name in target_group_names
    }
    changed = False
    for user in load_users(base_url, token):
        if legacy_group_name not in user_group_names(user):
            continue
        for group_name, group_identifier in target_group_identifiers.items():
            if group_name in user_group_names(user):
                continue
            if check_only:
                raise LldapError(f"User {user['id']} needs membership in {group_name}")
            add_user_to_group(base_url, token, str(user["id"]), group_identifier)
            changed = True
    return changed


def invalidate_sss_cache(username: str) -> None:
    if not Path("/usr/sbin/sss_cache").is_file():
        return
    completed_process = subprocess.run(
        ["/usr/sbin/sss_cache", "-u", username],
        check=False,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed_process.returncode == 0:
        return
    if "No cache object matched the specified search" in completed_process.stderr:
        return
    raise subprocess.CalledProcessError(
        completed_process.returncode,
        completed_process.args,
        stderr=completed_process.stderr,
    )


def ensure_user(
    arguments: argparse.Namespace,
    base_url: str,
    token: str,
    check_only: bool,
) -> bool:
    groups = load_groups(base_url, token)
    primary_group_identifier, primary_group_id_number = resolve_group(
        groups,
        arguments.primary_group,
    )
    secondary_group_identifiers = [
        resolve_group(groups, group_name)[0]
        for group_name in arguments.secondary_group_names
    ]
    users = load_users(base_url, token)
    validate_user_id_number_available(users, arguments.username, arguments.uid_number)
    user = find_user(users, arguments.username)
    desired_group_names = [
        arguments.primary_group,
        *arguments.secondary_group_names,
    ]
    desired_group_name_set = set(desired_group_names)
    desired_group_identifiers = [
        primary_group_identifier,
        *secondary_group_identifiers,
    ]
    if user is None:
        if check_only:
            raise LldapError(f"User {arguments.username} does not exist")
        create_user(arguments, base_url, token, primary_group_id_number)
        for group_identifier in desired_group_identifiers:
            add_user_to_group(
                base_url,
                token,
                arguments.username,
                group_identifier,
            )
        return True

    pending_attributes = changed_user_attributes(
        user,
        expected_attributes(arguments, primary_group_id_number),
    )
    pending_profile_update = (
        user["email"] != arguments.email
        or user["displayName"] != arguments.display_name
    )
    missing_group_names = desired_group_name_set - user_group_names(user)
    if (
        not pending_attributes
        and not pending_profile_update
        and not missing_group_names
    ):
        return False
    if check_only:
        raise LldapError(f"User {arguments.username} needs changes")

    if pending_attributes or pending_profile_update:
        update_user(arguments, base_url, token, pending_attributes)
    for group_identifier, group_name in zip(
        desired_group_identifiers,
        desired_group_names,
        strict=True,
    ):
        if group_name in missing_group_names:
            add_user_to_group(base_url, token, arguments.username, group_identifier)
    return True


def main() -> int:
    arguments = parse_arguments()
    environment_file = read_environment_file(Path(arguments.environment_file))
    admin_password = environment_file.get("LLDAP_LDAP_USER_PASS")
    if not admin_password:
        raise LldapError(
            f"{arguments.environment_file} does not define LLDAP_LDAP_USER_PASS"
        )

    token = login(arguments.base_url, arguments.admin_username, admin_password)
    if not arguments.check:
        ensure_schema(arguments.base_url, token)
    changed = ensure_user(arguments, arguments.base_url, token, arguments.check)
    if changed and not arguments.skip_sss_cache:
        invalidate_sss_cache(arguments.username)
    print(arguments.username)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LldapError, subprocess.CalledProcessError) as error:
        print(f"lldap-ensure-user: {error}", file=sys.stderr)
        raise SystemExit(1)
