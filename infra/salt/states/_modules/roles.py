"""Salt execution helpers for role-based state inclusion."""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import NotRequired, TypedDict

    class SlsIncludes(TypedDict):
        """Represents SLS includes."""

        include: NotRequired[list[str]]
        state_includes: NotRequired[list[str]]


def has_role(role: str) -> bool:
    """Return true when the minion has the requested role grain."""
    return role in __grains__.get("roles", [])


# Initially I tried to have a generic function that I called once to check for
# pillar files existence then for states fiels existence.
# It worked with salt-call as everything is ran locally, but it failed with
# salt-ssh.
# When using salt-ssh, the function is called locally when compiling pillar data,
# but it is called remotely for states data. This didn't work as state files
# are not available on the remote host.
def include_roles_sls(sls_format: str) -> "SlsIncludes":
    """Return state includes for every role assigned to the minion."""
    result: "SlsIncludes" = {"include": [], "state_includes": []}

    for role in __grains__.get("roles", []):
        sls_id = sls_format.format(role=role)

        for kind in ("pillar", "states"):
            base_path = f"{kind}/{sls_id.replace('.', '/')}"
            paths = [f"{base_path}.sls", f"{base_path}/init.sls"]

            if any(__salt__["file.file_exists"](path) for path in paths):
                key = "include" if kind == "pillar" else "state_includes"
                result[key].append(sls_id)

    return result
