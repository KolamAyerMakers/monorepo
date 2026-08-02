# Kolam Maker Makers classroom server UpCloud Provisioning

Pulumi Python project for the Kolam Ayer Makers classroom server on UpCloud.

## Validation

```bash
uv run ruff check
uv run ruff format --check
uv run basedpyright
uv run pytest
```

## Providers

This project uses the official
[`pulumi-upcloud`](https://www.pulumi.com/registry/packages/upcloud/)
provider. Reverse DNS uses a local Pulumi dynamic resource because
`pulumi-upcloud` does not expose PTR updates for server network interfaces; the
implementation uses the
[UpCloud IP address API](https://developers.upcloud.com/1.3/10-ip-addresses/).

DNS records are managed with the official
[`pulumi-cloudflare`](https://www.pulumi.com/registry/packages/cloudflare/)
provider. Existing Cloudflare DNS records must be imported before the first
`pulumi up`:

```bash
pulumi import cloudflare:index/dnsRecord:DnsRecord classroom-ipv4-dns-record '<zone_id>/<a_record_id>'
pulumi import cloudflare:index/dnsRecord:DnsRecord classroom-ipv6-dns-record '<zone_id>/<aaaa_record_id>'
```
