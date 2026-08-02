"""Tests for apt."""

from __future__ import annotations

from textwrap import dedent

from states._modules import apt


def test_build_repository_egress_derives_dynamic_sets_from_apt_sources() -> None:
    """Test that build repository egress derives dynamic sets from apt sources."""
    repository_egress = apt.build_repository_egress(
        {
            "sources": {
                "debian-main": {
                    "URIs": "https://deb.debian.org/debian",
                },
                "debian-security": {
                    "URIs": "https://deb.debian.org/debian-security",
                },
                "local-cache": {
                    "URIs": [
                        "http://packages.example.invalid/debian",
                        "file:///srv/packages",
                    ],
                },
            }
        }
    )

    assert repository_egress == {
        "destinations": {
            "apt-http": {
                "family": "inet",
                "table": "filter",
                "set_v4": "apt_repository_http_v4",
                "set_v6": "apt_repository_http_v6",
            },
            "apt-https": {
                "family": "inet",
                "table": "filter",
                "set_v4": "apt_repository_https_v4",
                "set_v6": "apt_repository_https_v6",
            },
        },
        "domains": [
            {
                "exact": "packages.example.invalid",
                "destination": "apt-http",
            },
            {
                "exact": "deb.debian.org",
                "destination": "apt-https",
            },
        ],
        "repositories": [
            {
                "name": "apt-http",
                "users": ["root", "_apt"],
                "ipv4_set": "apt_repository_http_v4",
                "ipv6_set": "apt_repository_http_v6",
                "tcp_ports": [80],
            },
            {
                "name": "apt-https",
                "users": ["root", "_apt"],
                "ipv4_set": "apt_repository_https_v4",
                "ipv6_set": "apt_repository_https_v6",
                "tcp_ports": [443],
            },
        ],
    }


def test_render_sources_expands_named_inline_signing_key() -> None:
    """Test that render sources expands named inline signing keys."""
    source_key = dedent(
        """\
        -----BEGIN PGP PUBLIC KEY BLOCK-----

        abc
        -----END PGP PUBLIC KEY BLOCK-----"""
    )

    assert apt.render_sources(
        {
            "system76-ubuntu-repo": {
                "Types": "deb",
                "URIs": "http://apt.pop-os.org/release-ubuntu/",
                "Suites": "noble",
                "Components": "main",
                "Signed-By-Key": "system76-ubuntu-repo",
            }
        },
        {"system76-ubuntu-repo": source_key},
    ) == dedent(
        """\
        Types: deb
        URIs: http://apt.pop-os.org/release-ubuntu/
        Suites: noble
        Components: main
        Signed-By: -----BEGIN PGP PUBLIC KEY BLOCK-----
         .
         abc
         -----END PGP PUBLIC KEY BLOCK-----
        """
    )


def test_render_sources_joins_sequence_values() -> None:
    """Test that render sources joins sequence values."""
    assert (
        apt.render_sources(
            {
                "example": {
                    "Types": "deb",
                    "URIs": [
                        "https://one.example.invalid",
                        "https://two.example.invalid",
                    ],
                }
            }
        )
        == "Types: deb\nURIs: https://one.example.invalid https://two.example.invalid\n"
    )
