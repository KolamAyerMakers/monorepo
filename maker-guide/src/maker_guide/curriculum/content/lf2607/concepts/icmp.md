# ICMP

## Core Idea

ICMP is a network control protocol used for diagnostic and error messages; `ping` uses ICMP echo requests and echo replies.

## Commands To Try

```bash
ping -c 3 1.1.1.1
ping -c 3 lf2607.kolamayermakers.org
```

`ping` sends ICMP echo requests and reports replies, packet loss, and round-trip time.

## How To Read Ping Output

```text
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 2.1/2.8/3.4/0.5 ms
```

- Transmitted: how many requests were sent.
- Received: how many replies returned.
- Packet loss: percentage that did not return.
- Average RTT: rough latency measurement.

## What Ping Proves

Ping can prove that ICMP echo replies are coming back from a host or address. It does not prove that HTTP, SSH, DNS, or SMTP works.

## Why Ping Can Mislead

- Some networks block ICMP but allow HTTPS.
- Some hosts ignore ping but still serve websites.
- DNS can resolve to an address that does not answer ICMP.
- A load balancer or firewall can respond differently from the backend service.

## Common Failures

- `Name or service not known`: DNS failed before ICMP started.
- `100% packet loss`: no replies returned; this may be filtering, routing, or host behavior.
- `Destination Host Unreachable`: your machine or network stack found no route to the destination.
- Ping works but `curl` fails: move up the stack and debug the HTTP service.

## Proof Check

Run `ping -c 3 1.1.1.1`, then run `curl -I https://example.org`. Explain why these test different things.

## Docs Pointers

- Run `man ping`.
- Read [Cloudflare: What is ICMP?](https://www.cloudflare.com/learning/ddos/glossary/internet-control-message-protocol-icmp/).
- Read [IP Networking](ip-networking.md) for layered network debugging.
