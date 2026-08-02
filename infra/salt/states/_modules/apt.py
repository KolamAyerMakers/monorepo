"""Build derived apt data used by Salt states.

This execution module converts apt source definitions from pillar into the
domain, nftables set, and firewall rule data consumed by DNS-backed egress
filtering states.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import cast
from urllib.parse import urlsplit

__virtualname__ = "apt"

DESTINATIONS = {
    "http": {
        "name": "apt-http",
        "tcp_ports": [80],
        "set_v4": "apt_repository_http_v4",
        "set_v6": "apt_repository_http_v6",
    },
    "https": {
        "name": "apt-https",
        "tcp_ports": [443],
        "set_v4": "apt_repository_https_v4",
        "set_v6": "apt_repository_https_v6",
    },
}

REPOSITORY_EGRESS_USERS = ["root", "_apt"]
SIGNED_BY_KEY = "Signed-By-Key"
SIGNED_BY = "Signed-By"


def __virtual__() -> str:
    return __virtualname__


def build_repository_egress(apt: Mapping[str, object]) -> dict[str, object]:
    """Return firewall and DNS-tracking data for configured apt repositories.

    Pass the `apt` pillar subtree. The return value contains `destinations`,
    `domains`, and `repositories` entries for `dns_nftsets.fragment` and the
    apt firewall state.
    """
    sources = _mapping(apt.get("sources"))
    domains_by_scheme: dict[str, set[str]] = {"http": set(), "https": set()}

    for source in sources.values():
        normalized_source = _mapping(source)
        for uri in _source_uris(normalized_source.get("URIs")):
            parsed_uri = urlsplit(uri)
            if parsed_uri.scheme in domains_by_scheme and parsed_uri.hostname:
                domains_by_scheme[parsed_uri.scheme].add(parsed_uri.hostname)

    destinations: dict[str, dict[str, str]] = {}
    domains: list[dict[str, str]] = []
    repositories: list[dict[str, object]] = []

    for scheme in ("http", "https"):
        scheme_domains = sorted(domains_by_scheme[scheme])
        if not scheme_domains:
            continue

        destination = DESTINATIONS[scheme]
        destination_name = _string(destination["name"])
        set_v4 = _string(destination["set_v4"])
        set_v6 = _string(destination["set_v6"])
        destinations[destination_name] = {
            "family": "inet",
            "table": "filter",
            "set_v4": set_v4,
            "set_v6": set_v6,
        }
        domains.extend(
            {"exact": domain_name, "destination": destination_name}
            for domain_name in scheme_domains
        )
        repositories.append(
            {
                "name": destination_name,
                "users": REPOSITORY_EGRESS_USERS,
                "ipv4_set": set_v4,
                "ipv6_set": set_v6,
                "tcp_ports": destination["tcp_ports"],
            }
        )

    return {
        "destinations": destinations,
        "domains": domains,
        "repositories": repositories,
    }


def render_sources(
    sources: Mapping[str, object], source_keys: Mapping[str, object] | None = None
) -> str:
    """Render Deb822 apt source definitions.

    Source mappings may use `Signed-By-Key` to reference an ASCII-armored key in
    the `source_keys` mapping. The rendered Deb822 output replaces that helper
    field with a correctly folded `Signed-By` field.
    """
    return (
        "\n\n".join(
            _render_source(_mapping(source), _mapping(source_keys))
            for source in sources.values()
        )
        + "\n"
    )


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _source_uris(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield from value.split()
        return

    if isinstance(value, Sequence):
        for item in value:
            if isinstance(item, str):
                yield item


def _string(value: object) -> str:
    if isinstance(value, str):
        return value
    raise TypeError(f"Expected string, got {type(value).__name__}")


def _render_source(
    source: Mapping[str, object], source_keys: Mapping[str, object]
) -> str:
    rendered_lines: list[str] = []

    for key, value in source.items():
        if key == SIGNED_BY_KEY:
            rendered_lines.extend(
                _render_field(SIGNED_BY, _source_key(_string(value), source_keys))
            )
            continue

        rendered_lines.extend(_render_field(key, value))

    return "\n".join(rendered_lines)


def _render_field(key: str, value: object) -> list[str]:
    if isinstance(value, str):
        return _render_string_field(key, value)
    if isinstance(value, Sequence):
        return [f"{key}: {' '.join(_sequence_strings(value))}"]
    return [f"{key}: {value}"]


def _render_string_field(key: str, value: str) -> list[str]:
    lines = value.splitlines()
    if not lines:
        return [f"{key}:"]
    if len(lines) == 1:
        return [f"{key}: {lines[0]}"]

    return [f"{key}: {lines[0]}", *[_render_continuation(line) for line in lines[1:]]]


def _render_continuation(line: str) -> str:
    if line:
        return f" {line}"
    return " ."


def _source_key(name: str, source_keys: Mapping[str, object]) -> str:
    if name not in source_keys:
        raise KeyError(f"Missing apt source key: {name}")
    return _string(source_keys[name])


def _sequence_strings(values: Sequence[object]) -> Iterable[str]:
    for value in values:
        yield _string(value)
