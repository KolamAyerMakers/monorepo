# SMTP Basics

## Core Idea

SMTP is the protocol mail servers use to move email between systems. You do not administer mail in this course, but SMTP is a useful comparison point because it shows that the internet is many text-based protocols, not just HTTP.

## Mental Model

HTTP usually means a client asks a web server for a resource. SMTP usually means a mail sender talks to a mail server to hand off a message. Both involve clients, servers, commands, replies, hostnames, ports, and logs.

## Common Ports

- `25`: server-to-server SMTP.
- `587`: message submission with authentication and encryption negotiation.
- `465`: SMTP over TLS in many deployments.

## What To Notice

Mail delivery depends on DNS records, especially MX records. A domain can have a website and no mail service, or mail service and no website.

```bash
dig MX example.org
```

## Why We Do Not Practice Sending Mail Here

Mail systems have spam, abuse, reputation, authentication, privacy, and operational risks. The course uses SMTP as protocol literacy, not as a shared-server exercise.

## Common Confusions

- SMTP sends mail. IMAP and POP3 retrieve mail.
- A domain's web server and mail server are often different machines.
- Port reachability does not mean you are allowed to relay mail.
- Modern mail requires authentication and anti-spoofing records such as SPF, DKIM, and DMARC.

## Proof Check

Run `dig MX example.org` and identify whether the domain publishes mail exchanger records.

## Docs Pointers

- Run `man dig`.
- Read [Cloudflare: DNS MX record](https://www.cloudflare.com/learning/dns/dns-records/dns-mx-record/).
- Read [RFC 5321](https://www.rfc-editor.org/rfc/rfc5321) only if you want the formal SMTP protocol specification.
