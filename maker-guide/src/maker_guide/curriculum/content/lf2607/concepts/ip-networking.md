# IP Networking

## Core Idea

IP networking moves packets between hosts; protocols such as TCP, SSH, HTTP, DNS, and SMTP build useful conversations on top of that movement.

## Layered Questions

When a network task fails, separate the questions:

1. Name: does DNS resolve the hostname?
2. Address: which IP address did it resolve to?
3. Reachability: can packets travel there?
4. Port: is the service listening on the expected port?
5. Protocol: did the client and server speak the same protocol?
6. Application: did authentication, routing, files, or permissions succeed?

## Course Commands

```bash
host lf2607.kolamayermakers.org
ping -c 3 1.1.1.1
curl -I https://lf2607.kolamayermakers.org/~username/
ssh username@lf2607.kolamayermakers.org
```

Each command answers a different networking question. Do not use one command as proof for every layer.

## Addresses And Ports

- IPv4: `203.0.113.10`
- IPv6: `2001:db8::10`
- Localhost IPv4: `127.0.0.1`
- Localhost name: `localhost`
- HTTPS default port: `443`
- SSH default port: `22`

A port identifies a service endpoint on a host. Your course user-managed service listens on a local high port behind the public proxy.

## DNS Is Not The Service

DNS can work while HTTP fails. HTTP can fail while SSH works. Ping can fail while HTTPS works. Keep the layers separate.

## Common Failures

- `Name or service not known`: hostname did not resolve.
- `Connection refused`: a host answered, but nothing accepted the connection on that port.
- Timeout: packets or replies did not arrive before the client gave up.
- `502`: a proxy accepted your request but could not reach the backend service.
- Certificate error: TLS identity or trust failed.

## Proof Check

For a broken URL, run one DNS command and one HTTP command. Explain which layer each command tested.

## Docs Pointers

- Run `man host`, `man dig`, `man ping`, `man ssh`, and `man curl`.
- Read [MDN: How DNS works](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_domain_name).
- Read [MDN: What is a URL?](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_URL).
- Read [DNS](dns.md), [ICMP](icmp.md), and [HTTP](http.md) for focused protocol notes.
- Read [IP Addressing Basics](ip-addressing-basics.md) for address notation and localhost details.
- Read [Sockets](sockets.md) for how processes use addresses and ports.
