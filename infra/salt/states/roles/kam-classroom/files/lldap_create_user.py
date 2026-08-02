#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
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
GROUP_ATTRIBUTES = {
    "gidNumber": ("INTEGER", False, True, False),
}
DEFAULT_GROUP_NAME = "humans"
DEFAULT_SECONDARY_GROUP_NAMES = ("linux-foundations",)
USER_ID_NUMBER_MINIMUM = 20000
USER_ID_NUMBER_MAXIMUM = 20999
DEFAULT_FORGEJO_URL = "http://127.0.0.1:3000/"
DEFAULT_FORGEJO_BINARY = "/usr/local/bin/forgejo"
DEFAULT_FORGEJO_CONFIGURATION_FILE = "/etc/forgejo/app.ini"
DEFAULT_FORGEJO_WORK_PATH = "/data/forgejo"
DEFAULT_FORGEJO_RUN_USER = "git"
DEFAULT_HOME_QUOTA_COMMAND = "/usr/local/sbin/apply-user-quotas"
DEFAULT_HOME_QUOTA_CONFIGURATION_FILE = "/etc/quotas/user-quotas.json"
SCHEMA_ALREADY_EXISTS_MARKERS = (
    "UNIQUE constraint failed: user_attribute_schema.user_attribute_schema_name",
    "UNIQUE constraint failed: group_attribute_schema.group_attribute_schema_name",
    "UNIQUE constraint failed: user_object_class_schema.user_object_class_schema_name",
)
GENERATED_PASSWORD_ATTEMPTS = 10


class LldapError(Exception):
    pass


class ForgejoError(Exception):
    pass


def is_schema_already_exists_error(error: LldapError) -> bool:
    error_message = str(error)
    return any(marker in error_message for marker in SCHEMA_ALREADY_EXISTS_MARKERS)


def default_email_domain() -> str:
    return socket.getfqdn().strip(".") or "localhost"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an LLDAP user with POSIX attributes for local SSH login."
    )
    _ = parser.add_argument("username")
    _ = parser.add_argument("--email")
    _ = parser.add_argument("--email-domain", default=default_email_domain())
    _ = parser.add_argument("--display-name")
    _ = parser.add_argument("--uid-number", type=int)
    _ = parser.add_argument("--gid-number", type=int)
    _ = parser.add_argument("--home-directory")
    _ = parser.add_argument("--shell", default="/bin/bash")
    _ = parser.add_argument("--group", default=DEFAULT_GROUP_NAME)
    _ = parser.add_argument(
        "--secondary-group",
        action="append",
        default=[],
        dest="secondary_group_names",
    )
    _ = parser.add_argument("--password-stdin", action="store_true")
    _ = parser.add_argument("--print-user-id-number", action="store_true")
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--pwscore-command", default="/usr/bin/pwscore")
    _ = parser.add_argument("--forgejo-url", default=DEFAULT_FORGEJO_URL)
    _ = parser.add_argument("--forgejo-binary", default=DEFAULT_FORGEJO_BINARY)
    _ = parser.add_argument(
        "--forgejo-configuration-file",
        default=DEFAULT_FORGEJO_CONFIGURATION_FILE,
    )
    _ = parser.add_argument("--forgejo-work-path", default=DEFAULT_FORGEJO_WORK_PATH)
    _ = parser.add_argument("--forgejo-run-user", default=DEFAULT_FORGEJO_RUN_USER)
    _ = parser.add_argument("--home-quota-command", default=DEFAULT_HOME_QUOTA_COMMAND)
    _ = parser.add_argument(
        "--home-quota-configuration-file",
        default=DEFAULT_HOME_QUOTA_CONFIGURATION_FILE,
    )
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


def forgejo_json_request(
    url: str,
    method: str,
    authorization: str,
    payload: dict[str, object] | None = None,
) -> object:
    headers = {"Authorization": authorization}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise ForgejoError(f"HTTP {error.code} from {url}: {body}") from error
    except urllib.error.URLError as error:
        raise ForgejoError(f"Could not connect to {url}: {error}") from error


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


def ensure_attribute(
    base_url: str,
    token: str,
    target: str,
    name: str,
    attribute_type: str,
    is_list: bool,
    is_visible: bool,
    is_editable: bool,
) -> None:
    if target == "user":
        mutation = """
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
        """
    else:
        mutation = """
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
        """
    try:
        _ = graphql(
            base_url,
            token,
            mutation,
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
    group_schema = cast(dict[str, object], schema["groupSchema"])
    user_attributes = cast(list[dict[str, object]], user_schema["attributes"])
    group_attributes = cast(list[dict[str, object]], group_schema["attributes"])
    existing_user_attributes = {str(attribute["name"]) for attribute in user_attributes}
    existing_group_attributes = {
        str(attribute["name"]) for attribute in group_attributes
    }
    for name, attribute_settings in USER_ATTRIBUTES.items():
        if name not in existing_user_attributes:
            ensure_attribute(base_url, token, "user", name, *attribute_settings)
    for name, attribute_settings in GROUP_ATTRIBUTES.items():
        if name not in existing_group_attributes:
            ensure_attribute(base_url, token, "group", name, *attribute_settings)

    user_object_class_items = cast(
        list[dict[str, object]],
        user_schema["ldapObjectClasses"],
    )
    user_object_classes = {str(item["objectClass"]) for item in user_object_class_items}
    if "posixAccount" not in user_object_classes:
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
             attributes { name value }
          }
        }
        """,
        {},
    )["users"]
    return cast(list[dict[str, object]], users)


def group_id_number(group: dict[str, object]) -> int | None:
    attributes = cast(list[dict[str, object]], group["attributes"])
    for attribute in attributes:
        if str(attribute["name"]).lower() == "gidnumber":
            values = cast(list[str], attribute["value"])
            return int(values[0])
    return None


def user_id_number(user: dict[str, object]) -> int | None:
    attributes = cast(list[dict[str, object]], user["attributes"])
    for attribute in attributes:
        if str(attribute["name"]).lower() == "uidnumber":
            values = cast(list[str], attribute["value"])
            return int(values[0])
    return None


def allocate_user_id_number(base_url: str, token: str) -> int:
    candidates: list[int] = []
    for user in load_users(base_url, token):
        value = user_id_number(user)
        if (
            value is not None
            and USER_ID_NUMBER_MINIMUM <= value <= USER_ID_NUMBER_MAXIMUM
        ):
            candidates.append(value)
    if not candidates:
        return USER_ID_NUMBER_MINIMUM

    next_user_id_number = max(candidates) + 1
    if next_user_id_number > USER_ID_NUMBER_MAXIMUM:
        raise LldapError(
            f"No uidNumber is available in {USER_ID_NUMBER_MINIMUM}-{USER_ID_NUMBER_MAXIMUM}"
        )
    return next_user_id_number


def ensure_user_id_number_available(
    base_url: str,
    token: str,
    user_id_number_value: int,
) -> None:
    for user in load_users(base_url, token):
        if user_id_number(user) == user_id_number_value:
            raise LldapError(
                f"uidNumber {user_id_number_value} is already used by {user['id']}"
            )


def ensure_email_available(base_url: str, token: str, email: str) -> None:
    for user in load_users(base_url, token):
        if str(user["email"]).casefold() == email.casefold():
            raise LldapError("An account already uses that email address.")


def ensure_group(
    base_url: str,
    token: str,
    group_name: str,
    group_id_number_value: int | None,
) -> tuple[int, int]:
    for group in load_groups(base_url, token):
        if group["displayName"] != group_name:
            continue
        group_identifier = int(str(group["id"]))
        existing_group_id_number = group_id_number(group)
        if existing_group_id_number is None:
            raise LldapError(
                f"Group {group_name} does not define gidNumber; run Salt to prepare managed groups"
            )
        if existing_group_id_number != group_id_number_value:
            if group_id_number_value is None:
                return group_identifier, existing_group_id_number
            raise LldapError(
                f"Group {group_name} has gidNumber {existing_group_id_number}, expected {group_id_number_value}"
            )
        return group_identifier, existing_group_id_number

    raise LldapError(f"Group {group_name} does not exist; run Salt to create it")


def resolve_secondary_group_names(arguments: argparse.Namespace) -> list[str]:
    secondary_group_names = [
        *DEFAULT_SECONDARY_GROUP_NAMES,
        *arguments.secondary_group_names,
    ]
    return list(
        dict.fromkeys(
            group_name
            for group_name in secondary_group_names
            if group_name != arguments.group
        )
    )


def build_user_input(
    arguments: argparse.Namespace,
    user_id_number_value: int,
    group_id_number_value: int,
) -> dict[str, object]:
    user_input: dict[str, object] = {
        "id": arguments.username,
        "displayName": arguments.display_name or arguments.username,
        "attributes": [
            {"name": "uidNumber", "value": [str(user_id_number_value)]},
            {"name": "gidNumber", "value": [str(group_id_number_value)]},
            {
                "name": "homeDirectory",
                "value": [home_directory_from_arguments(arguments)],
            },
            {"name": "unixShell", "value": [arguments.shell]},
        ],
    }
    user_input["email"] = resolve_user_email(arguments)
    return user_input


def resolve_user_email(arguments: argparse.Namespace) -> str:
    return arguments.email or f"{arguments.username}@{arguments.email_domain}"


def create_user(
    arguments: argparse.Namespace,
    base_url: str,
    token: str,
    user_id_number_value: int,
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
            "user": build_user_input(
                arguments, user_id_number_value, group_id_number_value
            )
        },
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


def set_password(
    base_url: str,
    token: str,
    username: str,
    password: str,
) -> None:
    environment = os.environ.copy()
    environment["LLDAP_USER_PASSWORD"] = password
    _ = subprocess.run(
        [
            "/usr/local/bin/lldap_set_password",
            "--base-url",
            base_url,
            "--token",
            token,
            "--username",
            username,
        ],
        env=environment,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def home_directory_from_arguments(arguments: argparse.Namespace) -> str:
    return arguments.home_directory or f"/home/{arguments.username}"


def ensure_student_home(
    home_directory: str,
    user_id_number_value: int,
    group_id_number_value: int,
    username: str,
    email: str,
) -> None:
    home_path = Path(home_directory)
    bin_directory = home_path / "bin"
    public_html_directory = home_path / "public_html"
    git_configuration_file = home_path / ".gitconfig"
    home_path.mkdir(mode=0o711, parents=True, exist_ok=True)
    bin_directory.mkdir(mode=0o700, exist_ok=True)
    public_html_directory.mkdir(mode=0o755, exist_ok=True)
    os.chown(home_path, user_id_number_value, group_id_number_value)
    os.chown(bin_directory, user_id_number_value, group_id_number_value)
    os.chown(public_html_directory, user_id_number_value, group_id_number_value)
    os.chmod(home_path, 0o711)
    os.chmod(bin_directory, 0o700)
    os.chmod(public_html_directory, 0o755)
    if not git_configuration_file.exists():
        _ = git_configuration_file.write_text(
            f"[user]\n\tname = {username}\n\temail = {email}\n",
            encoding="utf-8",
        )
    os.chown(git_configuration_file, user_id_number_value, group_id_number_value)
    os.chmod(git_configuration_file, 0o600)


def ensure_student_ssh_key(
    home_directory: str,
    user_id_number_value: int,
    group_id_number_value: int,
    key_comment: str,
) -> str:
    home_path = Path(home_directory)
    ssh_directory = home_path / ".ssh"
    private_key_file = ssh_directory / "id_ed25519"
    public_key_file = ssh_directory / "id_ed25519.pub"

    home_path.mkdir(mode=0o711, parents=True, exist_ok=True)
    ssh_directory.mkdir(mode=0o700, exist_ok=True)
    os.chown(home_path, user_id_number_value, group_id_number_value)
    os.chown(ssh_directory, user_id_number_value, group_id_number_value)
    os.chmod(home_path, 0o711)
    os.chmod(ssh_directory, 0o700)

    if not private_key_file.exists():
        _ = subprocess.run(
            [
                "/usr/bin/ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                key_comment,
                "-f",
                str(private_key_file),
            ],
            check=True,
        )
    if not public_key_file.exists():
        raise LldapError(f"{public_key_file} was not created")

    os.chown(private_key_file, user_id_number_value, group_id_number_value)
    os.chown(public_key_file, user_id_number_value, group_id_number_value)
    os.chmod(private_key_file, 0o600)
    os.chmod(public_key_file, 0o644)
    return public_key_file.read_text(encoding="utf-8").strip()


def run_forgejo_command(arguments: argparse.Namespace, command: list[str]) -> str:
    completed_process = subprocess.run(
        [
            "/usr/sbin/runuser",
            "-u",
            arguments.forgejo_run_user,
            "--",
            arguments.forgejo_binary,
            "--config",
            arguments.forgejo_configuration_file,
            "--work-path",
            arguments.forgejo_work_path,
            *command,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed_process.returncode != 0:
        raise ForgejoError(
            completed_process.stderr.strip() or completed_process.stdout.strip()
        )
    return completed_process.stdout


def forgejo_user_already_exists(error: ForgejoError) -> bool:
    return "already exists" in str(error).lower()


def create_forgejo_user(
    arguments: argparse.Namespace,
    forgejo_password: str,
) -> None:
    command = [
        "admin",
        "user",
        "create",
        "--username",
        arguments.username,
        "--email",
        resolve_user_email(arguments),
        "--password",
        forgejo_password,
        "--must-change-password=false",
    ]
    if arguments.display_name:
        command.extend(["--fullname", arguments.display_name])
    try:
        _ = run_forgejo_command(arguments, command)
    except ForgejoError as error:
        if forgejo_user_already_exists(error):
            return
        raise


def change_forgejo_password(
    arguments: argparse.Namespace,
    forgejo_password: str,
) -> None:
    _ = run_forgejo_command(
        arguments,
        [
            "admin",
            "user",
            "change-password",
            "--username",
            arguments.username,
            "--password",
            forgejo_password,
            "--must-change-password=false",
        ],
    )


def forgejo_basic_authorization(
    username: str,
    password: str,
) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return "Basic " + token


def ensure_forgejo_public_key(
    arguments: argparse.Namespace,
    authorization: str,
    public_key: str,
) -> None:
    keys = forgejo_json_request(
        append_path(arguments.forgejo_url, "/api/v1/user/keys"),
        "GET",
        authorization,
    )
    if not isinstance(keys, list):
        raise ForgejoError("Forgejo key list response was not an array")
    for key in cast(list[object], keys):
        if not isinstance(key, dict):
            continue
        if cast(dict[str, object], key).get("key") == public_key:
            return

    _ = forgejo_json_request(
        append_path(arguments.forgejo_url, "/api/v1/user/keys"),
        "POST",
        authorization,
        {"title": resolve_user_email(arguments), "key": public_key},
    )


def provision_forgejo_account(
    arguments: argparse.Namespace,
    forgejo_password: str,
    public_key: str,
) -> None:
    create_forgejo_user(arguments, forgejo_password)
    change_forgejo_password(arguments, forgejo_password)
    ensure_forgejo_public_key(
        arguments,
        forgejo_basic_authorization(arguments.username, forgejo_password),
        public_key,
    )


def apply_home_quota(
    quota_command: str,
    configuration_file: str,
    username: str,
    user_id_number_value: int,
    group_names: list[str],
) -> None:
    command = [
        quota_command,
        "--configuration",
        configuration_file,
        "--username",
        username,
        "--user-id-number",
        str(user_id_number_value),
    ]
    for group_name in group_names:
        command.extend(["--group", group_name])
    _ = subprocess.run(command, check=True)


def generate_password() -> str:
    result = subprocess.run(
        [
            "/usr/bin/diceware",
            "--no-caps",
            "--delimiter",
            "-",
            "--num",
            "6",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    password = result.stdout.strip()
    if not password:
        raise LldapError("diceware did not generate a password")
    return password


def password_strength_error(
    pwscore_command: str,
    username: str,
    password: str,
) -> str | None:
    if not password:
        return "The password is empty."
    if username in password.lower():
        return "It contains the username."
    try:
        completed_process = subprocess.run(
            [pwscore_command],
            check=False,
            input=password + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return f"{pwscore_command} was not found."
    if completed_process.returncode == 0:
        return None
    return (
        completed_process.stderr.strip()
        or completed_process.stdout.strip()
        or "The password did not pass the system strength policy."
    )


def validate_password(pwscore_command: str, username: str, password: str) -> None:
    error = password_strength_error(pwscore_command, username, password)
    if error is not None:
        raise LldapError(f"Password rejected: {error}")


def generate_compliant_password(pwscore_command: str, username: str) -> str:
    last_error = "unknown password quality failure"
    remaining_attempts = GENERATED_PASSWORD_ATTEMPTS
    while remaining_attempts > 0:
        remaining_attempts -= 1
        password = generate_password()
        error = password_strength_error(pwscore_command, username, password)
        if error is None:
            return password
        last_error = error
    raise LldapError(
        "diceware did not generate a compliant password after "
        f"{GENERATED_PASSWORD_ATTEMPTS} attempts: {last_error}"
    )


def resolve_password(
    pwscore_command: str,
    username: str,
    password_stdin: bool,
) -> str:
    if not password_stdin:
        return generate_compliant_password(pwscore_command, username)
    password = sys.stdin.read().rstrip("\n")
    validate_password(pwscore_command, username, password)
    return password


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


def main() -> int:
    arguments = parse_arguments()
    environment_file = read_environment_file(Path(arguments.environment_file))
    admin_password = environment_file.get("LLDAP_LDAP_USER_PASS")
    if not admin_password:
        raise LldapError(
            f"{arguments.environment_file} does not define LLDAP_LDAP_USER_PASS"
        )

    password = resolve_password(
        arguments.pwscore_command,
        arguments.username,
        arguments.password_stdin,
    )

    token = login(arguments.base_url, arguments.admin_username, admin_password)
    ensure_schema(arguments.base_url, token)
    group_identifier, group_id_number_value = ensure_group(
        arguments.base_url,
        token,
        arguments.group,
        arguments.gid_number,
    )
    secondary_group_names = resolve_secondary_group_names(arguments)
    secondary_group_identifiers = [
        ensure_group(arguments.base_url, token, group_name, None)[0]
        for group_name in secondary_group_names
    ]
    user_id_number_value = arguments.uid_number or allocate_user_id_number(
        arguments.base_url,
        token,
    )
    ensure_user_id_number_available(arguments.base_url, token, user_id_number_value)
    ensure_email_available(arguments.base_url, token, resolve_user_email(arguments))
    ensure_student_home(
        home_directory_from_arguments(arguments),
        user_id_number_value,
        group_id_number_value,
        arguments.username,
        resolve_user_email(arguments),
    )
    public_key = ensure_student_ssh_key(
        home_directory_from_arguments(arguments),
        user_id_number_value,
        group_id_number_value,
        resolve_user_email(arguments),
    )
    create_user(
        arguments,
        arguments.base_url,
        token,
        user_id_number_value,
        group_id_number_value,
    )
    add_user_to_group(arguments.base_url, token, arguments.username, group_identifier)
    for group_identifier in secondary_group_identifiers:
        add_user_to_group(
            arguments.base_url,
            token,
            arguments.username,
            group_identifier,
        )
    apply_home_quota(
        arguments.home_quota_command,
        arguments.home_quota_configuration_file,
        arguments.username,
        user_id_number_value,
        [arguments.group, *secondary_group_names],
    )
    set_password(arguments.base_url, token, arguments.username, password)
    try:
        invalidate_sss_cache(arguments.username)
    except subprocess.CalledProcessError as error:
        print(
            f"lldap-create-user: could not invalidate SSSD cache for {arguments.username}: "
            f"{(error.stderr or str(error)).strip()}",
            file=sys.stderr,
        )
    provision_forgejo_account(arguments, generate_password(), public_key)
    if arguments.print_user_id_number:
        print(user_id_number_value)
    else:
        print(arguments.username)
    if not arguments.password_stdin and not arguments.print_user_id_number:
        print(password)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ForgejoError, LldapError) as error:
        print(f"lldap-create-user: {error}", file=sys.stderr)
        raise SystemExit(1)
