"""Configuration loading for the classroom server Pulumi project."""

from __future__ import annotations

from dataclasses import dataclass

import pulumi

SSH_PUBLIC_KEYS = {
    "salt_ssh": " ".join(
        (
            "ssh-rsa",
            "AAAAB3NzaC1yc2EAAAADAQABAAABgQDrK3O011LNeFw/DmLngpXbH7PeX49inSVzDP7eQoP37UvpCkWmBKs/amrvdSMPToLRq7f0aIHdSkwpO0Qa6Vl7MW4P82BG+XVvtvlpE9pCz7sVCdakCMjuxnZElfX7DIwu050VLcKIJW+x9Lmr8ALBUxjmV6tKALxRAcw4Ewy9EkfNcGbtS9R4Q3/U7Bpm69dBDJHNFQ3fwouwBhQZRn9gedQn6XZpiZAPc8pxPo4x4LQFoaezYvsumNZaaiZcA8MpR4s7xUMwrCR2LCFGlUrXDsg2A6Kpw6XYPp13Cm6QUTzNniuJVayUvwdHnKzaL5cPTzWIZM7LfhNDDqPi+Gzs0APnOKPGp5TjS8OU5gB8o3q2RX1PfHQWYN1i4f5hjJIGZHK29X+gEs66K6H8Gwf2ty/5scMDBJDigzP3+NAR355ak/kCinohkFwjaLcZhVfNMGOzx0MEVbSLicwdswjOJb7+uRkP20L0zVuweez0OjhKPEGqayDdA8qTl1Avczs=",
            "pmuller@tardis",
        )
    ),
    "yubikey_25_939_134": " ".join(
        (
            "ssh-rsa",
            "AAAAB3NzaC1yc2EAAAADAQABAAACAQDvgDgAu4i3Og5u4/M6qzOYWtdHy6jOcH0XJ6f7hTS3UqlgpuEe96FvFhOdRzG42KsyhM7mN+AcmaW5ANxq6rezc7Hl+mgw0tiEF90SzdKEuMkMJ3hazQ48GD+exk995Sni2/4UvLrdir7jIdRkaEp+eM5EOTBm+z5ism68cNgN/6Ff5XLT3I3QoFLwn2ip8LvCxMDSoy+zPn2WAsnLpnELyP3IxsQjAqGrADKjrIgro4ZatKbUVXriAXb6aXveujk9SP1JIaZB+TUtvCBIiXyEwvUMz5uHuN9+/LuEhGn9fWIuDB35pWkH5dbIeKE5J20bBShWkjXvy5pq1ESMrbKUwfVkJ7updwIVceA2L0Z7scfvLjybdT0xaO02MPWzsApbO8FvTB69XVTNHwdkQNr1QxUDqCSBsRq7ANcO4quUNA5qhS6bVeBvFJ/PoyX0JYOe4/rB9+Yg0xkEofE7d9TO+S5wWNi2W0NjvgObzyIgBQiXD0xgu0ACOd8kPQB/ybmpAKp2+XlZ/tDOsjY2FPhpZuGhR13IOZjybswG9nE5uLb43UtQ+ULccSWzcIB35/U9ilX0UnDXO/l2rLDRt95aB5pH1V9h/HNau6il5ZueE2043HXhXx/8jqP8WKqeOt76BG4sKnb7yKfU3FAsGMlUg/58cXKDHMA4tBUc08IMnQ==",
            "cardno:25_939_134",
        )
    ),
}


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    """Configuration values for the stack."""

    hostname: str
    title: str
    zone: str
    plan: str
    server_template_storage: str
    disk_gib: int
    metadata: bool
    firewall: bool
    source_ip_filtering: bool
    timezone: str
    boot_order: str
    nic_model: str
    video_model: str
    ssh_public_keys: list[str]
    login_user: str
    ipv4_reverse_dns_hostname: str
    cloudflare_account_id: str
    cloudflare_zone_name: str
    canonical_dns_record_name: str
    dns_record_ttl: int
    dns_record_proxied: bool
    upcloud_token: pulumi.Output[str]


def _load_ssh_public_key(name: str) -> str:
    try:
        return SSH_PUBLIC_KEYS[name].strip()
    except KeyError as error:
        raise ValueError(f"{name}: unknown ssh public key") from error


def _load_ssh_public_keys(names: object) -> list[str]:
    if not isinstance(names, list):
        raise ValueError("sshPublicKeyNames must be a list of key names")

    ssh_public_key_names: list[str] = []
    for name in names:
        if not isinstance(name, str):
            raise ValueError("sshPublicKeyNames must be a list of key names")
        ssh_public_key_names.append(name)

    return [_load_ssh_public_key(name) for name in ssh_public_key_names]


def cloudflare_dns_record_name(record_name: str, zone_name: str) -> str:
    """Return a validated fully qualified Cloudflare DNS record name."""
    if record_name != zone_name and not record_name.endswith(f".{zone_name}"):
        raise ValueError(f"{record_name}: DNS record must be under {zone_name}")
    return record_name


def load_configuration() -> ProjectConfiguration:
    """Load Pulumi stack configuration."""
    pulumi_configuration = pulumi.Config()
    upcloud_configuration = pulumi.Config("upcloud")

    return ProjectConfiguration(
        hostname=pulumi_configuration.require("hostname"),
        title=pulumi_configuration.require("title"),
        zone=pulumi_configuration.require("zone"),
        plan=pulumi_configuration.require("plan"),
        server_template_storage=pulumi_configuration.require("serverTemplateStorage"),
        disk_gib=pulumi_configuration.require_int("diskGiB"),
        metadata=pulumi_configuration.require_bool("metadata"),
        firewall=pulumi_configuration.require_bool("firewall"),
        source_ip_filtering=pulumi_configuration.require_bool("sourceIpFiltering"),
        timezone=pulumi_configuration.require("timezone"),
        boot_order=pulumi_configuration.require("bootOrder"),
        nic_model=pulumi_configuration.require("nicModel"),
        video_model=pulumi_configuration.require("videoModel"),
        ssh_public_keys=_load_ssh_public_keys(
            pulumi_configuration.require_object("sshPublicKeyNames")
        ),
        login_user=pulumi_configuration.require("loginUser"),
        ipv4_reverse_dns_hostname=pulumi_configuration.require(
            "ipv4ReverseDnsHostname"
        ),
        cloudflare_account_id=pulumi_configuration.require("cloudflareAccountId"),
        cloudflare_zone_name=pulumi_configuration.require("cloudflareZoneName"),
        canonical_dns_record_name=pulumi_configuration.require(
            "canonicalDnsRecordName"
        ),
        dns_record_ttl=pulumi_configuration.require_int("dnsRecordTtl"),
        dns_record_proxied=pulumi_configuration.require_bool("dnsRecordProxied"),
        upcloud_token=upcloud_configuration.require_secret("token"),
    )
