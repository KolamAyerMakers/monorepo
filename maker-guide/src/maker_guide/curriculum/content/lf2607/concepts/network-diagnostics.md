# Network Diagnostics

## Core Idea

Network tools answer separate questions: name lookup, reachability, and service response.

## Practice Alone

Use `host` or `dig` for DNS, `ping` for reachability, and `curl` for HTTP.

```bash
host example.org
ping -c 3 1.1.1.1
curl -i --max-time 10 https://example.org/
```

These are separate observations, not a chain of proofs: ping tests ICMP to that address, not the website. A failed ping does not cancel a successful HTTPS result.

## Done When

You can report which observation failed and what it actually tested. Continue with [IP networking](ip-networking.md), [DNS](dns.md), or [HTTP inspection](http-inspection.md) for that layer.
