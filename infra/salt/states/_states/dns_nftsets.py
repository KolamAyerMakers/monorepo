"""Register DNS-backed nftables set configuration fragments.

Service formulas use this state to declare DNS names and the nftables sets that
should contain their resolved addresses. The state serializes each declaration
as JSON Lines and hands assembly to the concat state module.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import TypedDict, cast

__virtualname__ = "dns_nftsets"

DEFAULT_TARGET = "/etc/dns-nftsets/configuration.jsonl"
DOMAIN_MATCHERS = ("exact",)


class Result(TypedDict):
    """Salt state return mapping used by this module."""

    name: str
    result: bool | None
    changes: dict[str, object]
    comment: str


__states__: dict[str, Callable[..., Result]]


def __virtual__() -> str:
    """Return the Salt virtual module name."""
    return __virtualname__


def fragment(
    name: str,
    destinations: Mapping[str, object] | None = None,
    domains: Sequence[object] | None = None,
    target: str = DEFAULT_TARGET,
    destination_position: str = "20",
    domain_position: str = "60",
) -> Result:
    """Add destination and domain declarations to a dns-nftsets file.

    Pass `destinations` as destination names mapped to nftables set metadata,
    and `domains` as exact DNS names mapped to those destinations. The state
    writes ordered concat fragments for `target`.
    """
    try:
        destination_contents = _destination_contents(destinations or {})
        domain_contents = _domain_contents(domains or [])
    except (TypeError, ValueError) as error:
        return {
            "name": name,
            "result": False,
            "changes": {},
            "comment": str(error),
        }

    results: list[Result] = []
    if destination_contents:
        results.append(
            __states__["concat.fragment"](
                f"{name}::destinations",
                target=target,
                position=f"{destination_position}__destinations",
                contents=destination_contents,
            )
        )

    if domain_contents:
        results.append(
            __states__["concat.fragment"](
                f"{name}::domains",
                target=target,
                position=f"{domain_position}__domains",
                contents=domain_contents,
            )
        )

    if not results:
        return {
            "name": name,
            "result": True,
            "changes": {},
            "comment": f"No dns-nftsets fragments registered for {target}",
        }

    failed_results = [result for result in results if result["result"] is False]
    if failed_results:
        return {
            "name": name,
            "result": False,
            "changes": {},
            "comment": "; ".join(result["comment"] for result in failed_results),
        }

    return {
        "name": name,
        "result": None if any(result["result"] is None for result in results) else True,
        "changes": {
            result["name"]: result["changes"] for result in results if result["changes"]
        },
        "comment": "; ".join(result["comment"] for result in results),
    }


def _destination_contents(destinations: Mapping[str, object]) -> str:
    lines: list[str] = []
    for destination_name in sorted(destinations):
        destination = _mapping(destinations[destination_name])
        document: dict[str, object] = {
            "kind": "destination",
            "name": destination_name,
            "family": _required_string(destination, "family", destination_name),
            "table": _required_string(destination, "table", destination_name),
        }
        _set_optional_string(document, destination, "set_v4")
        _set_optional_string(document, destination, "set_v6")
        lines.append(_json_line(document))
    return _joined_lines(lines)


def _domain_contents(domains: Sequence[object]) -> str:
    lines: list[str] = []
    for raw_domain in domains:
        domain = _mapping(raw_domain)
        matcher_name, matcher_value = _domain_matcher(domain)
        lines.append(
            _json_line(
                {
                    "kind": "domain",
                    matcher_name: matcher_value,
                    "destination": _required_string(domain, "destination", "domain"),
                }
            )
        )
    return _joined_lines(lines)


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise TypeError(f"Expected mapping, got {type(value).__name__}")


def _required_string(
    mapping: Mapping[str, object],
    key: str,
    owner: str,
) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{owner} requires non-empty {key}")


def _set_optional_string(
    document: dict[str, object],
    mapping: Mapping[str, object],
    key: str,
) -> None:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        document[key] = value


def _domain_matcher(domain: Mapping[str, object]) -> tuple[str, str]:
    matches: list[tuple[str, str]] = []
    for matcher in DOMAIN_MATCHERS:
        value = domain.get(matcher)
        if isinstance(value, str) and value:
            matches.append((matcher, value))
    if len(matches) != 1:
        raise ValueError("Domain rule requires exactly one matcher")
    return matches[0]


def _json_line(document: Mapping[str, object]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def _joined_lines(lines: Sequence[str]) -> str:
    if not lines:
        return ""
    return "\n".join(lines) + "\n"
