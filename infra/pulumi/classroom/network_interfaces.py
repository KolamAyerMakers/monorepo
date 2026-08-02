"""Network interface construction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from pulumi_upcloud._inputs import ServerNetworkInterfaceArgsDict as NetworkInterface

_PUBLIC_NETWORK_TYPE = "public"


def build_network_interfaces(source_ip_filtering: bool) -> list[NetworkInterface]:
    """Build public network interfaces without attaching utility networking."""
    return [
        {
            "type": "public",
            "index": 1,
            "ip_address_family": "IPv4",
            "source_ip_filtering": source_ip_filtering,
        },
        {
            "type": "public",
            "index": 2,
            "ip_address_family": "IPv6",
            "source_ip_filtering": source_ip_filtering,
        },
    ]


def public_ip_address(
    network_interfaces: Sequence[Mapping[str, object]] | None,
    address_family: str,
) -> str:
    """Return the public IP address with the requested UpCloud address family."""
    for network_interface in network_interfaces or ():
        if network_interface.get("type") != _PUBLIC_NETWORK_TYPE:
            continue
        if network_interface.get("ip_address_family") != address_family:
            continue

        ip_address = network_interface.get("ip_address")
        if isinstance(ip_address, str) and ip_address:
            return ip_address

    raise ValueError(f"missing public {address_family} address")
