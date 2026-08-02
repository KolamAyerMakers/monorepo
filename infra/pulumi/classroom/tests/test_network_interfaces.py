"""Tests for UpCloud network interface construction."""

from __future__ import annotations

import pytest

from network_interfaces import build_network_interfaces, public_ip_address


def test_network_interfaces_exclude_upcloud_utility_network() -> None:
    """Test only attaches public network interfaces."""
    assert build_network_interfaces(source_ip_filtering=True) == [
        {
            "type": "public",
            "index": 1,
            "ip_address_family": "IPv4",
            "source_ip_filtering": True,
        },
        {
            "type": "public",
            "index": 2,
            "ip_address_family": "IPv6",
            "source_ip_filtering": True,
        },
    ]


def test_public_ip_address_extracts_matching_public_address() -> None:
    assert (
        public_ip_address(
            [
                {
                    "type": "public",
                    "ip_address_family": "IPv4",
                    "ip_address": "213.163.204.189",
                },
                {
                    "type": "public",
                    "ip_address_family": "IPv6",
                    "ip_address": "2a04:3543:1000:2310:409a:c4ff:fea5:4ddc",
                },
            ],
            "IPv6",
        )
        == "2a04:3543:1000:2310:409a:c4ff:fea5:4ddc"
    )


def test_public_ip_address_rejects_missing_address_family() -> None:
    with pytest.raises(ValueError, match="missing public IPv6 address"):
        public_ip_address(
            [
                {
                    "type": "public",
                    "ip_address_family": "IPv4",
                    "ip_address": "213.163.204.189",
                }
            ],
            "IPv6",
        )
