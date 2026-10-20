# IP Addressing Basics

## Core Idea

An IP address identifies a network endpoint. DNS names such as `example.org` are human-readable labels that resolve to addresses. Ports distinguish service endpoints on an address.

## Commands To Try

```bash
host example.org
curl -I --max-time 10 https://example.org/
```

`host` gives a compact DNS answer. `dig` gives a fuller DNS answer. `curl` tests whether an HTTP service responds after DNS and connection setup.

## Address, Port, Protocol

```text
https://example.org/docs/
scheme: https
host:   example.org
path:   /docs/
```

HTTPS defaults to port `443` unless a port is written explicitly. For local HTTP, `http://127.0.0.1:8000/` names IPv4 loopback and port `8000`.

## IPv4 And IPv6

- IPv4 addresses look like `203.0.113.10`.
- IPv6 addresses look like `2001:db8::10`.
- DNS can return either or both.
- A service can work on one address family and fail on another if routing or firewall rules differ.

The two addresses above are reserved documentation examples, not live hosts to contact. `localhost` may resolve to IPv4 `127.0.0.1`, IPv6 `::1`, or both; a listener on only one family need not answer the other.

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
