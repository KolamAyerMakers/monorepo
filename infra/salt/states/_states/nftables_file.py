"""Render simple nftables table files from structured Salt data.

The state accepts counters, sets, chains, and rules as data, performs basic
validation, and writes a deterministic nftables include file through Salt's
standard file state.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TypedDict, cast

__virtualname__ = "nftables_file"


class Result(TypedDict):
    """Salt state return mapping used by this module."""

    name: str
    result: bool | None
    changes: dict[str, object]
    comment: str


__states__: dict[str, Callable[..., Result]]


def __virtual__() -> str:
    return __virtualname__


def managed(
    name: str,
    family: str = "inet",
    table: str = "filter",
    header: str = "",
    counters: Sequence[object] | None = None,
    sets: Sequence[object] | None = None,
    chains: Sequence[object] | None = None,
    rules: Sequence[object] | None = None,
    user: str = "root",
    group: str = "root",
    mode: str = "0644",
) -> Result:
    """Render and manage an nftables table include file.

    Use `family` and `table` to choose the table header, then pass ordered
    `counters`, `sets`, `chains`, and `rules` sequences. The function converts
    that data to nft syntax and delegates ownership, mode, and change reporting
    to `file.managed`.
    """
    try:
        contents = _contents(
            family=family,
            table=table,
            header=header,
            counters=counters or [],
            sets=sets or [],
            chains=chains or [],
            rules=rules or [],
        )
    except (TypeError, ValueError) as error:
        return {
            "name": name,
            "result": False,
            "changes": {},
            "comment": str(error),
        }

    return __states__["file.managed"](
        name,
        contents=contents,
        user=user,
        group=group,
        mode=mode,
    )


def _contents(
    *,
    family: str,
    table: str,
    header: str,
    counters: Sequence[object],
    sets: Sequence[object],
    chains: Sequence[object],
    rules: Sequence[object],
) -> str:
    lines: list[str] = []
    if header:
        lines.extend(header.rstrip("\n").splitlines())
    lines.append(f"table {family} {table} {{")

    for counter_definition in counters:
        lines.append(_counter_line(counter_definition))

    for set_definition in _sorted_mappings(sets):
        lines.extend(_set_lines(set_definition))

    rules_by_chain = _rules_by_chain(rules)
    for chain_definition in _sorted_mappings(chains):
        chain_name = _required_string(chain_definition, "name", "chain")
        lines.extend(_chain_lines(chain_definition, rules_by_chain.get(chain_name, [])))

    lines.append("}")
    return "\n".join(lines) + "\n"


def _counter_line(counter_definition: object) -> str:
    if isinstance(counter_definition, str):
        return f"    counter {counter_definition} {{}}"
    counter_mapping = _mapping(counter_definition)
    return f"    counter {_required_string(counter_mapping, 'name', 'counter')} {{}}"


def _set_lines(set_definition: Mapping[str, object]) -> list[str]:
    name = _required_string(set_definition, "name", "set")
    set_type = _required_string(set_definition, "type", name)
    lines = [
        f"    set {name} {{",
        f"        type {set_type}",
    ]
    flags = _optional_strings(set_definition, "flags")
    if flags:
        lines.append(f"        flags {', '.join(flags)}")
    timeout = _optional_string(set_definition, "timeout")
    if timeout:
        lines.append(f"        timeout {timeout}")
    elements = set_definition.get("elements")
    if isinstance(elements, Sequence) and not isinstance(elements, str):
        lines.append(f"        elements = {{ {_joined_elements(elements)} }}")
    lines.append("    }")
    return lines


def _chain_lines(
    chain_definition: Mapping[str, object],
    rules: Sequence[Mapping[str, object]],
) -> list[str]:
    chain_name = _required_string(chain_definition, "name", "chain")
    lines = [f"    chain {chain_name} {{"]
    chain_options = _chain_options(chain_definition)
    if chain_options:
        lines.append(f"        {'; '.join(chain_options)};")
    for rule_definition in rules:
        lines.append(f"        {_required_string(rule_definition, 'rule', chain_name)}")
    lines.append("    }")
    return lines


def _chain_options(chain_definition: Mapping[str, object]) -> list[str]:
    options: list[str] = []
    hook = _optional_string(chain_definition, "hook")
    if hook:
        options.append(_optional_string(chain_definition, "type") or "type filter")
        options.append(f"hook {hook}")
        options.append(f"priority {chain_definition.get('priority', 0)}")
    policy = _optional_string(chain_definition, "policy")
    if policy:
        options.append(f"policy {policy}")
    return options


def _rules_by_chain(
    rules: Sequence[object],
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for rule_definition in _sorted_mappings(rules):
        chain = _required_string(rule_definition, "chain", "rule")
        grouped.setdefault(chain, []).append(rule_definition)
    return grouped


def _sorted_mappings(values: Sequence[object]) -> list[Mapping[str, object]]:
    return sorted(
        (_mapping(value) for value in values),
        key=lambda value: _optional_string(value, "position") or "50",
    )


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


def _optional_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str):
        return value
    return ""


def _optional_strings(mapping: Mapping[str, object], key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [item for item in value if isinstance(item, str)]


def _joined_elements(elements: Iterable[object]) -> str:
    return ", ".join(_nft_scalar(element) for element in elements)


def _nft_scalar(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value)
