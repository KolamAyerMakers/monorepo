"""Pulumi entry point for the classroom server UpCloud stack."""

from __future__ import annotations

import pulumi
import pulumi_cloudflare as cloudflare
import pulumi_upcloud as upcloud

from configuration import cloudflare_dns_record_name, load_configuration
from network_interfaces import build_network_interfaces, public_ip_address
from upcloud_ip_address import UpCloudIpAddressReverseDns

configuration = load_configuration()

server = upcloud.Server(
    "classroom",
    hostname=configuration.hostname,
    title=configuration.title,
    zone=configuration.zone,
    plan=configuration.plan,
    metadata=configuration.metadata,
    firewall=configuration.firewall,
    timezone=configuration.timezone,
    boot_order=configuration.boot_order,
    nic_model=configuration.nic_model,
    video_model=configuration.video_model,
    template={
        "storage": configuration.server_template_storage,
        "size": configuration.disk_gib,
    },
    network_interfaces=build_network_interfaces(configuration.source_ip_filtering),
    login={
        "user": configuration.login_user,
        "keys": configuration.ssh_public_keys,
        "password_delivery": "none",
        "create_password": False,
    },
)

public_ipv4_address = server.network_interfaces.apply(
    lambda network_interfaces: public_ip_address(network_interfaces, "IPv4")
)
public_ipv6_address = server.network_interfaces.apply(
    lambda network_interfaces: public_ip_address(network_interfaces, "IPv6")
)

cloudflare_zone = cloudflare.get_zone(
    filter={
        "account": {"id": configuration.cloudflare_account_id},
        "match": "all",
        "name": configuration.cloudflare_zone_name,
    }
)

ipv4_dns_record = cloudflare.DnsRecord(
    "classroom-ipv4-dns-record",
    zone_id=cloudflare_zone.zone_id,
    name=cloudflare_dns_record_name(
        configuration.canonical_dns_record_name,
        configuration.cloudflare_zone_name,
    ),
    ttl=float(configuration.dns_record_ttl),
    type="A",
    content=public_ipv4_address,
    proxied=configuration.dns_record_proxied,
    opts=pulumi.ResourceOptions(depends_on=[server], delete_before_replace=True),
)
ipv6_dns_record = cloudflare.DnsRecord(
    "classroom-ipv6-dns-record",
    zone_id=cloudflare_zone.zone_id,
    name=cloudflare_dns_record_name(
        configuration.canonical_dns_record_name,
        configuration.cloudflare_zone_name,
    ),
    ttl=float(configuration.dns_record_ttl),
    type="AAAA",
    content=public_ipv6_address,
    proxied=configuration.dns_record_proxied,
    opts=pulumi.ResourceOptions(depends_on=[server], delete_before_replace=True),
)
wildcard_ipv4_dns_record = cloudflare.DnsRecord(
    "classroom-wildcard-ipv4-dns-record",
    zone_id=cloudflare_zone.zone_id,
    name=cloudflare_dns_record_name(
        f"*.{configuration.canonical_dns_record_name}",
        configuration.cloudflare_zone_name,
    ),
    ttl=float(configuration.dns_record_ttl),
    type="A",
    content=public_ipv4_address,
    proxied=configuration.dns_record_proxied,
    opts=pulumi.ResourceOptions(depends_on=[server], delete_before_replace=True),
)
wildcard_ipv6_dns_record = cloudflare.DnsRecord(
    "classroom-wildcard-ipv6-dns-record",
    zone_id=cloudflare_zone.zone_id,
    name=cloudflare_dns_record_name(
        f"*.{configuration.canonical_dns_record_name}",
        configuration.cloudflare_zone_name,
    ),
    ttl=float(configuration.dns_record_ttl),
    type="AAAA",
    content=public_ipv6_address,
    proxied=configuration.dns_record_proxied,
    opts=pulumi.ResourceOptions(depends_on=[server], delete_before_replace=True),
)

UpCloudIpAddressReverseDns(
    "classroom-ipv4-reverse-dns",
    token=configuration.upcloud_token,
    ip_address=public_ipv4_address,
    reverse_dns_hostname=configuration.ipv4_reverse_dns_hostname,
    opts=pulumi.ResourceOptions(depends_on=[server]),
)
UpCloudIpAddressReverseDns(
    "classroom-ipv6-reverse-dns",
    token=configuration.upcloud_token,
    ip_address=public_ipv6_address,
    reverse_dns_hostname=configuration.ipv4_reverse_dns_hostname,
    opts=pulumi.ResourceOptions(depends_on=[server]),
)

pulumi.export("server_id", server.id)
pulumi.export("hostname", server.hostname)
pulumi.export("public_ipv4_address", public_ipv4_address)
pulumi.export("public_ipv6_address", public_ipv6_address)
pulumi.export("ipv4_dns_record_id", ipv4_dns_record.id)
pulumi.export("ipv6_dns_record_id", ipv6_dns_record.id)
pulumi.export("wildcard_ipv4_dns_record_id", wildcard_ipv4_dns_record.id)
pulumi.export("wildcard_ipv6_dns_record_id", wildcard_ipv6_dns_record.id)
pulumi.export("network_interfaces", server.network_interfaces)
