#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast


GROUP_ATTRIBUTES = {
    "gidNumber": ("INTEGER", False, True, False),
}
SCHEMA_ALREADY_EXISTS_MARKERS = (
    "UNIQUE constraint failed: group_attribute_schema.group_attribute_schema_name",
)


class LldapError(Exception):
    pass


def is_schema_already_exists_error(error: LldapError) -> bool:
    error_message = str(error)
    return any(marker in error_message for marker in SCHEMA_ALREADY_EXISTS_MARKERS)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure an LLDAP group exists.")
    _ = parser.add_argument("group")
    _ = parser.add_argument("--gid-number", type=int, required=True)
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--check", action="store_true")
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
            groupSchema {
              attributes { name }
            }
          }
        }
        """,
        {},
    )["schema"]
    if not isinstance(schema, dict):
        raise LldapError("GraphQL schema query did not return a schema object")
    return cast(dict[str, object], schema)


def ensure_group_attribute(
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
            mutation AddGroupAttribute(
              $name: String!,
              $attributeType: AttributeType!,
              $isList: Boolean!,
              $isVisible: Boolean!,
              $isEditable: Boolean!
            ) {
              addGroupAttribute(
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
    group_schema = cast(dict[str, object], schema["groupSchema"])
    group_attributes = cast(list[dict[str, object]], group_schema["attributes"])
    existing_group_attributes = {
        str(attribute["name"]).lower() for attribute in group_attributes
    }
    for name, attribute_settings in GROUP_ATTRIBUTES.items():
        if name.lower() not in existing_group_attributes:
            ensure_group_attribute(base_url, token, name, *attribute_settings)


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


def group_id_number(group: dict[str, object]) -> int | None:
    attributes = cast(list[dict[str, object]], group["attributes"])
    for attribute in attributes:
        if str(attribute["name"]).lower() == "gidnumber":
            values = cast(list[str], attribute["value"])
            return int(values[0])
    return None


def find_group(
    base_url: str,
    token: str,
    group_name: str,
) -> dict[str, object] | None:
    for group in load_groups(base_url, token):
        if group["displayName"] == group_name:
            return group
    return None


def create_group(
    base_url: str,
    token: str,
    group_name: str,
    group_id_number_value: int,
) -> None:
    _ = graphql(
        base_url,
        token,
        """
        mutation CreateGroup($request: CreateGroupInput!) {
          createGroupWithDetails(request: $request) { id }
        }
        """,
        {
            "request": {
                "displayName": group_name,
                "attributes": [
                    {"name": "gidNumber", "value": [str(group_id_number_value)]}
                ],
            }
        },
    )


def update_group_id_number(
    base_url: str,
    token: str,
    group_identifier: int,
    group_id_number_value: int,
) -> None:
    _ = graphql(
        base_url,
        token,
        """
        mutation UpdateGroup($group: UpdateGroupInput!) {
          updateGroup(group: $group) { ok }
        }
        """,
        {
            "group": {
                "id": group_identifier,
                "insertAttributes": [
                    {"name": "gidNumber", "value": [str(group_id_number_value)]}
                ],
            }
        },
    )


def ensure_group(
    base_url: str,
    token: str,
    group_name: str,
    group_id_number_value: int,
    check_only: bool,
) -> None:
    group = find_group(base_url, token, group_name)
    if group is None:
        if check_only:
            raise LldapError(f"Group {group_name} does not exist")
        create_group(base_url, token, group_name, group_id_number_value)
        return

    existing_group_id_number = group_id_number(group)
    if existing_group_id_number == group_id_number_value:
        return
    if existing_group_id_number is not None:
        raise LldapError(
            f"Group {group_name} has gidNumber {existing_group_id_number}, expected {group_id_number_value}"
        )
    if check_only:
        raise LldapError(f"Group {group_name} does not define gidNumber")

    update_group_id_number(
        base_url,
        token,
        int(str(group["id"])),
        group_id_number_value,
    )


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
    ensure_group(
        arguments.base_url,
        token,
        arguments.group,
        arguments.gid_number,
        arguments.check,
    )
    print(arguments.group)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LldapError as error:
        print(f"lldap-ensure-group: {error}", file=sys.stderr)
        raise SystemExit(1)
