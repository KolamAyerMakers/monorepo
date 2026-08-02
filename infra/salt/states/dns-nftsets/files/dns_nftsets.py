#!/usr/bin/env python3
"""Resolve declared DNS names and refresh nftables sets.

The program reads a JSON Lines configuration assembled by Salt, queries the
configured local resolver with dnspython, and updates only the nftables sets
declared in that configuration.

Sample configuration:

    # Managed by Salt.
    {"kind":"settings","resolver":{"address":"127.0.0.1","port":53,"timeout":2.0,"lifetime":5.0},"ttl":{"minimum_seconds":60,"maximum_seconds":86400}}
    {"kind":"destination","name":"package-repositories","family":"inet","table":"filter","set_v4":"package_repositories_v4","set_v6":"package_repositories_v6"}
    {"kind":"domain","exact":"deb.debian.org","destination":"package-repositories"}
"""

from __future__ import annotations

import argparse
import importlib
import ipaddress
import json
import re
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

NFTABLES_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
NFTABLES_FAMILIES = frozenset(("ip", "ip6", "inet"))


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings loaded from the dns-nftsets configuration file."""

    resolver_address: str
    resolver_port: int
    resolver_timeout: float
    resolver_lifetime: float
    minimum_ttl_seconds: int
    maximum_ttl_seconds: int


@dataclass(frozen=True, slots=True)
class Destination:
    """One nftables destination that can receive DNS resolved addresses."""

    name: str
    family: str
    table: str
    set_v4: str | None
    set_v6: str | None


@dataclass(frozen=True, slots=True)
class DomainRule:
    """One exact DNS name mapped to a configured destination."""

    exact: str
    destination: str


@dataclass(frozen=True, slots=True)
class Configuration:
    """Complete dns-nftsets configuration loaded from JSON Lines."""

    settings: Settings
    destinations: Mapping[str, Destination]
    domains: Sequence[DomainRule]


@dataclass(frozen=True, slots=True)
class ResolvedAddress:
    """One resolved IP address with the TTL that should be installed."""

    address: ipaddress.IPv4Address | ipaddress.IPv6Address
    ttl_seconds: int


class _DnsResolver(Protocol):
    nameservers: list[str]
    port: int
    timeout: float
    lifetime: float

    def resolve(
        self,
        domain_name: str,
        record_type: str,
        *,
        raise_on_no_answer: bool,
    ) -> "_DnsAnswer": ...


class _DnsAnswer(Protocol):
    rrset: "_ResourceRecordSet | None"

    def __iter__(self) -> Iterator[object]: ...


class _ResourceRecordSet(Protocol):
    ttl: int


class _NftablesClient(Protocol):
    def cmd(self, command: str) -> tuple[int, str, str]: ...


def load_configuration(path: Path) -> Configuration:
    """Load and validate a JSON Lines dns-nftsets configuration file."""
    settings: Settings | None = None
    destinations: dict[str, Destination] = {}
    domains: list[DomainRule] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        document = _load_json_line(stripped_line, path, line_number)
        kind = _required_string(document, "kind", f"{path}:{line_number}")
        if kind == "settings":
            if settings is not None:
                raise ValueError("Only one settings document is allowed")
            settings = _settings(document)
        elif kind == "destination":
            destination = _destination(document)
            if destination.name in destinations:
                raise ValueError(f"Duplicate destination {destination.name!r}")
            destinations[destination.name] = destination
        elif kind == "domain":
            domains.append(_domain(document))
        else:
            raise ValueError(f"Unsupported document kind {kind!r}")

    if settings is None:
        raise ValueError("Missing settings document")
    _validate_domain_destinations(domains, destinations)
    return Configuration(settings=settings, destinations=destinations, domains=domains)


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line program and return a process exit code."""
    parsed_arguments = _parse_arguments(arguments)
    try:
        configuration = load_configuration(parsed_arguments.configuration)
        commands, errors = _build_nftables_commands(configuration)
        if parsed_arguments.dry_run:
            for command in commands:
                print(command)
            return 1 if errors else 0
        if commands:
            _apply_nftables_commands(commands)
    except (OSError, ValueError) as error:
        print(f"dns-nftsets: {error}", file=sys.stderr)
        return 1

    for error in errors:
        print(f"dns-nftsets: {error}", file=sys.stderr)
    return 1 if errors else 0


def _parse_arguments(arguments: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--configuration",
        type=Path,
        required=True,
        help="JSON Lines configuration path",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print nftables commands without applying them",
    )
    return parser.parse_args(arguments)


def _load_json_line(line: str, path: Path, line_number: int) -> Mapping[str, object]:
    try:
        document = json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON at {path}:{line_number}: {error}") from error
    if not isinstance(document, Mapping):
        raise ValueError(f"Expected object at {path}:{line_number}")
    return cast(Mapping[str, object], document)


def _settings(document: Mapping[str, object]) -> Settings:
    resolver = _mapping(document.get("resolver"), "settings.resolver")
    ttl = _mapping(document.get("ttl"), "settings.ttl")
    minimum_ttl_seconds = _required_integer(ttl, "minimum_seconds", "settings.ttl")
    maximum_ttl_seconds = _required_integer(ttl, "maximum_seconds", "settings.ttl")
    if minimum_ttl_seconds < 1:
        raise ValueError("settings.ttl.minimum_seconds must be greater than zero")
    if maximum_ttl_seconds < minimum_ttl_seconds:
        raise ValueError(
            "settings.ttl.maximum_seconds must be greater than or equal to "
            "minimum_seconds"
        )
    return Settings(
        resolver_address=_required_string(resolver, "address", "settings.resolver"),
        resolver_port=_required_integer(resolver, "port", "settings.resolver"),
        resolver_timeout=_required_number(resolver, "timeout", "settings.resolver"),
        resolver_lifetime=_required_number(resolver, "lifetime", "settings.resolver"),
        minimum_ttl_seconds=minimum_ttl_seconds,
        maximum_ttl_seconds=maximum_ttl_seconds,
    )


def _destination(document: Mapping[str, object]) -> Destination:
    name = _required_string(document, "name", "destination")
    family = _required_string(document, "family", name)
    table = _required_string(document, "table", name)
    set_v4 = _optional_string(document, "set_v4")
    set_v6 = _optional_string(document, "set_v6")

    _validate_nftables_identifier(name, "destination")
    _validate_nftables_family(family)
    _validate_nftables_identifier(table, name)
    if set_v4 is None and set_v6 is None:
        raise ValueError(f"{name} requires at least one nftables set")
    if set_v4 is not None:
        _validate_nftables_identifier(set_v4, name)
    if set_v6 is not None:
        _validate_nftables_identifier(set_v6, name)

    return Destination(
        name=name,
        family=family,
        table=table,
        set_v4=set_v4,
        set_v6=set_v6,
    )


def _domain(document: Mapping[str, object]) -> DomainRule:
    exact = _normalize_domain_name(_required_string(document, "exact", "domain"))
    return DomainRule(
        exact=exact,
        destination=_required_string(document, "destination", "domain"),
    )


def _mapping(value: object, owner: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"{owner} must be an object")


def _required_string(
    mapping: Mapping[str, object],
    key: str,
    owner: str,
) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{owner} requires non-empty {key}")


def _optional_string(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{key} must be a non-empty string")


def _required_integer(
    mapping: Mapping[str, object],
    key: str,
    owner: str,
) -> int:
    value = mapping.get(key)
    if isinstance(value, int):
        return value
    raise ValueError(f"{owner}.{key} must be an integer")


def _required_number(
    mapping: Mapping[str, object],
    key: str,
    owner: str,
) -> float:
    value = mapping.get(key)
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"{owner}.{key} must be a number")


def _normalize_domain_name(value: str) -> str:
    try:
        return value.rstrip(".").encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError(f"Invalid DNS name {value!r}") from error


def _validate_domain_destinations(
    domains: Iterable[DomainRule],
    destinations: Mapping[str, Destination],
) -> None:
    for domain in domains:
        if domain.destination not in destinations:
            raise ValueError(
                f"Domain {domain.exact!r} references unknown destination "
                f"{domain.destination!r}"
            )


def _validate_nftables_identifier(value: str, owner: str) -> None:
    if not NFTABLES_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{owner} has invalid nftables identifier {value!r}")


def _validate_nftables_family(value: str) -> None:
    if value not in NFTABLES_FAMILIES:
        raise ValueError(f"Unsupported nftables family {value!r}")


def _build_nftables_commands(
    configuration: Configuration,
) -> tuple[list[str], list[str]]:
    resolver = _dns_resolver(configuration.settings)
    addresses_by_destination: dict[str, dict[str, list[ResolvedAddress]]] = {
        name: {"ipv4": [], "ipv6": []} for name in configuration.destinations
    }
    failed_destinations: dict[str, list[str]] = {}

    for domain in configuration.domains:
        for address_family, record_type in (("ipv4", "A"), ("ipv6", "AAAA")):
            try:
                addresses = _resolve_addresses(
                    resolver,
                    domain.exact,
                    record_type,
                    configuration.settings,
                )
            except ValueError as error:
                failed_destinations.setdefault(domain.destination, []).append(
                    str(error)
                )
                continue
            addresses_by_destination[domain.destination][address_family].extend(
                addresses
            )

    commands: list[str] = []
    for destination_name, destination in sorted(configuration.destinations.items()):
        if failed_destinations.get(destination_name):
            continue
        commands.extend(
            _destination_commands(
                destination, addresses_by_destination[destination_name]
            )
        )

    errors = [
        f"{destination_name}: {'; '.join(messages)}"
        for destination_name, messages in sorted(failed_destinations.items())
        if messages
    ]
    return commands, errors


def _dns_resolver(settings: Settings) -> _DnsResolver:
    resolver_module = importlib.import_module("dns.resolver")
    resolver_factory = getattr(resolver_module, "Resolver")
    resolver = cast(_DnsResolver, resolver_factory(configure=False))
    resolver.nameservers = [settings.resolver_address]
    resolver.port = settings.resolver_port
    resolver.timeout = settings.resolver_timeout
    resolver.lifetime = settings.resolver_lifetime
    return resolver


def _resolve_addresses(
    resolver: _DnsResolver,
    domain_name: str,
    record_type: str,
    settings: Settings,
) -> list[ResolvedAddress]:
    dns_exception_module = importlib.import_module("dns.exception")
    dns_resolver_module = importlib.import_module("dns.resolver")
    dns_exception = cast(type[Exception], getattr(dns_exception_module, "DNSException"))
    no_answer_exception = cast(
        type[Exception], getattr(dns_resolver_module, "NoAnswer")
    )
    name_not_found_exception = cast(
        type[Exception], getattr(dns_resolver_module, "NXDOMAIN")
    )
    try:
        answer = resolver.resolve(
            domain_name,
            record_type,
            raise_on_no_answer=False,
        )
    except (no_answer_exception, name_not_found_exception):
        return []
    except dns_exception as error:
        message = str(error) or error.__class__.__name__
        raise ValueError(f"{domain_name} {record_type}: {message}") from error

    resource_record_set = answer.rrset
    if resource_record_set is None:
        return []

    ttl_seconds = _clamp_ttl(int(getattr(resource_record_set, "ttl")), settings)
    return [
        ResolvedAddress(
            address=ipaddress.ip_address(str(item)), ttl_seconds=ttl_seconds
        )
        for item in answer
    ]


def _clamp_ttl(ttl_seconds: int, settings: Settings) -> int:
    return min(
        max(ttl_seconds, settings.minimum_ttl_seconds),
        settings.maximum_ttl_seconds,
    )


def _destination_commands(
    destination: Destination,
    addresses: Mapping[str, Sequence[ResolvedAddress]],
) -> list[str]:
    commands: list[str] = []
    if destination.set_v4 is not None:
        commands.extend(
            _set_commands(
                destination.family,
                destination.table,
                destination.set_v4,
                addresses["ipv4"],
            )
        )
    if destination.set_v6 is not None:
        commands.extend(
            _set_commands(
                destination.family,
                destination.table,
                destination.set_v6,
                addresses["ipv6"],
            )
        )
    return commands


def _set_commands(
    family: str,
    table: str,
    set_name: str,
    addresses: Sequence[ResolvedAddress],
) -> list[str]:
    commands = [f"flush set {family} {table} {set_name}"]
    elements = _nftables_elements(addresses)
    if elements:
        commands.append(f"add element {family} {table} {set_name} {{ {elements} }}")
    return commands


def _nftables_elements(addresses: Sequence[ResolvedAddress]) -> str:
    unique_addresses = {
        address.address: address.ttl_seconds
        for address in sorted(addresses, key=lambda item: item.address)
    }
    return ", ".join(
        f"{address} timeout {ttl_seconds}s"
        for address, ttl_seconds in unique_addresses.items()
    )


def _apply_nftables_commands(commands: Sequence[str]) -> None:
    nftables_module = importlib.import_module("nftables")
    nftables_factory = getattr(nftables_module, "Nftables")
    nftables_client = cast(_NftablesClient, nftables_factory())
    command_batch = "\n".join(commands)
    result = nftables_client.cmd(command_batch)
    return_code, _output, error = result
    if return_code != 0:
        raise ValueError(f"nftables failed: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
