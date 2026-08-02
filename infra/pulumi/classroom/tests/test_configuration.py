"""Tests for stack configuration helpers."""

from __future__ import annotations

import pytest

from configuration import (
    _load_ssh_public_keys,
    cloudflare_dns_record_name,
)


def test_load_ssh_public_keys_returns_known_keys() -> None:
    """Test that SSH public key names resolve through local project data."""
    public_keys = _load_ssh_public_keys(["yubikey_25_939_134", "salt_ssh"])

    assert len(public_keys) == 2
    assert public_keys[0].endswith(" cardno:25_939_134")
    assert public_keys[1].endswith(" pmuller@tardis")


@pytest.mark.parametrize("value", ["salt_ssh", ["salt_ssh", 42]])
def test_load_ssh_public_keys_rejects_invalid_values(value: object) -> None:
    """Test that SSH public key names must be a list of strings."""
    with pytest.raises(ValueError, match="sshPublicKeyNames"):
        _load_ssh_public_keys(value)


@pytest.mark.parametrize(
    "record_name",
    [
        "kolamayermakers.org",
        "classroom-dev.kolamayermakers.org",
        "auth.dev.kolamayermakers.org",
        "*.lf2607.kolamayermakers.org",
    ],
)
def test_cloudflare_dns_record_name_returns_full_record_name(record_name: str) -> None:
    """Test that Cloudflare receives the full record name."""
    assert cloudflare_dns_record_name(record_name, "kolamayermakers.org") == record_name


def test_cloudflare_dns_record_name_rejects_records_outside_zone() -> None:
    """Test that Cloudflare record names must belong to the zone."""
    with pytest.raises(ValueError, match="must be under kolamayermakers.org"):
        cloudflare_dns_record_name("example.org", "kolamayermakers.org")
