# IP Addressing Basics

## Core Idea

An IP address names a network interface location. DNS names such as `lf2607.kolamayermakers.org` are human-readable labels that resolve to addresses. Ports identify a service on an address.

## Commands To Try

```bash
host lf2607.kolamayermakers.org
curl -I https://lf2607.kolamayermakers.org/~username/
```

`host` gives a compact DNS answer. `dig` gives a fuller DNS answer. `curl` tests whether an HTTP service responds after DNS and connection setup.

## Address, Port, Protocol

```text
https://lf2607.kolamayermakers.org/~username/
|     |                                             |
scheme host name                                     path
```

`https` implies TCP port 443 unless another port is written explicitly. Your user-managed service uses a local high port behind the public reverse proxy.

## IPv4 And IPv6

- IPv4 addresses look like `203.0.113.10`.
- IPv6 addresses look like `2001:db8::10`.
- DNS can return either or both.
- A service can work on one address family and fail on another if routing or firewall rules differ.

## Common Confusions

- DNS success does not prove the web service works.
- Ping failure does not prove HTTP failure; ICMP can be blocked.
- `localhost` and `127.0.0.1` mean the same machine from the point of view of the process running the command.
- A port can be open locally but unreachable publicly if no proxy or firewall path points to it.

## Proof Check

Use `host`, then `curl -I`, and explain which command tested name resolution and which tested HTTP.

## Docs Pointers

- Run `man host`, `man dig`, and `man curl`.
- Read [Cloudflare Learning Center: What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/).
- Read [MDN: What is a URL?](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_URL).
- Read [IP Networking](ip-networking.md) for the broader layered debugging model.
- Read [DNS](dns.md) when you want record types and resolver behavior.
- Read [ICMP](icmp.md) when you want to understand what `ping` proves and does not prove.
