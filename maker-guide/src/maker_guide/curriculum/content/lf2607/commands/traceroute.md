# traceroute

## Use

```bash
traceroute -m 8 1.1.1.1
```

## What It Does

`traceroute` sends probes with increasing hop limits. Routers can return diagnostic replies, allowing the command to show part of the route to a destination.

## Practice

Use `-m 8` to limit the experiment to eight hops. Compare the route only as a diagnostic clue, not as proof that a website works.

## Watch Out

A `*` means that one hop did not answer its probe. Routers often filter these probes while forwarding normal web traffic.

## Docs Pointers

- Run `man traceroute`.
- Read [ICMP](../concepts/icmp.md) and [IP Networking](../concepts/ip-networking.md).
