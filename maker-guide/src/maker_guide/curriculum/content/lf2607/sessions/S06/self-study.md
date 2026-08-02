# S6 Self-Study Guide: Control Flow And Networking

Session: S6

## Study Path

1. Use `for` when you already have a list.
2. Use `while` when a condition decides whether to continue.
3. Use `if command; then` when command success controls the branch.
4. Combine known pieces into one-liners only after each piece works alone.
5. Use DNS, ping, and HTTP tools for different network questions.
6. Fetch small text into Markdown, then rebuild the site.

## Complete Loop Examples

```bash
for number in 1 2 3 4 5; do
  printf '%s\n' "$number"
done
```

```bash
count=5
while [[ "$count" -gt 0 ]]; do
  printf '%s\n' "$count"
  count=$((count - 1))
done
```

If a loop never stops, press `Ctrl-C`, then check that the loop variable changes inside the loop.

## Exit Status

Commands return `0` for success and nonzero for failure. `if command; then` uses that result.

```bash
ping -c 1 example.org
printf '%s\n' "$?"
```

## Network Decision Tree

- DNS question: `host example.org` or `dig example.org`.
- Reachability hint: `ping -c 3 1.1.1.1`; remember ICMP may be blocked.
- HTTP question: `curl -I https://example.org`.
- Redirect question: add `-L` to follow redirects.
- Connection detail: use `curl -vI`.

## One-Liner Pattern

Start expanded, then compress.

```bash
date
hostname
```

```bash
{ date; hostname; } > ~/playground/status.txt
```

The second command is an inline shell script: grouped commands with one redirection. Keep it only if you can explain every part.

## Fetched Content Pattern

```bash
{
  printf '# Network Fetch\n\n'
  printf 'Fetched at: '
  date
  printf '\n```text\n'
  curl -L https://example.org
  printf '\n```\n'
} > ~/src/pages/network.md
build-website
```

## Troubleshooting

- Loop never stops: press `Ctrl-C`, then check that the loop variable changes inside the loop.
- `curl` prints HTML you did not expect: rerun with `curl -I` and check redirects.
- `ping` fails but the site loads: ICMP reachability and HTTP availability are different questions.
- Script says `unbound variable`: add an argument check before using `$1`.

## Proof Checklist

- `count-ten.sh` uses `for`.
- `exists.sh` uses `if [[ -e "$1" ]]`.
- `countdown.sh` changes the counter inside the loop.
- You can explain why ping failure is not identical to website failure.
- `network.md` contains fetched text inside a fenced code block.

## Docs Pointers

- Run `help if`, `help for`, `help while`, and `help [[`.
- Run `man curl`, then read options `-I`, `-L`, and `-v`.
- Run `man ping`, `man dig`, and `man host`.
- Read the [curl man page](https://curl.se/docs/manpage.html) for HTTP inspection details.
- Read [IP Networking](../../concepts/ip-networking.md) for the layered model: DNS, address, reachability, port, protocol, application.
- Read [IP Addressing Basics](../../concepts/ip-addressing-basics.md) for DNS, ports, localhost, IPv4, and IPv6.
- Read [DNS](../../concepts/dns.md), [ICMP](../../concepts/icmp.md), and [HTTP](../../concepts/http.md) for focused protocol notes behind `host`, `dig`, `ping`, and `curl`.
- Read [SMTP Basics](../../concepts/smtp-basics.md) for a short protocol comparison with HTTP.
- Read [One-Liners](../../concepts/oneliner.md) before compressing loops, branches, pipes, and redirection onto one prompt line.
