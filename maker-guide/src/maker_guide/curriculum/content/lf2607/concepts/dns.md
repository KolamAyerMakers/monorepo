# DNS

## Core Idea

DNS maps human-readable names to records, including IP addresses, mail exchangers, aliases, and other service metadata.

## Commands To Try

```bash
host lf2607.kolamayermakers.org
dig lf2607.kolamayermakers.org
dig lf2607.kolamayermakers.org A
dig lf2607.kolamayermakers.org AAAA
dig example.org MX
```

Use `host` for short answers. Use `dig` when you want to see record types, TTLs, answer sections, and which resolver answered.

## Common Record Types

| Type | Meaning |
|---|---|
| `A` | Name to IPv4 address. |
| `AAAA` | Name to IPv6 address. |
| `CNAME` | Alias from one name to another name. |
| `MX` | Mail exchanger records for a domain. |
| `TXT` | Text metadata, often verification, SPF, DKIM, or DMARC data. |
| `NS` | Authoritative name servers for a zone. |

## How DNS Fits The Request

```text
name -> DNS answer -> IP address -> TCP connection -> protocol request
```

DNS success only proves that a name resolved. It does not prove that the server process is alive or that HTTP, SSH, or SMTP will work.

## Common Failures

- `NXDOMAIN`: the name does not exist in DNS.
- No `A` record but an `AAAA` record exists: the service may be IPv6-only.
- DNS returns an address, but `curl` fails: move to port, protocol, or application debugging.
- Different answers from different networks: DNS caches and split-horizon setups can differ.

## TTL

TTL means time to live. It tells resolvers how long they may cache an answer. Recent DNS changes may not appear everywhere immediately.

## Proof Check

Run `dig lf2607.kolamayermakers.org`. Identify the `ANSWER SECTION`, record type, and returned address or name.

## Docs Pointers

- Run `man host` and `man dig`.
- Read [Cloudflare: What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/).
- Read [Cloudflare: DNS record types](https://www.cloudflare.com/learning/dns/dns-records/).
- Read [IP Networking](ip-networking.md) for the broader network debugging model.
