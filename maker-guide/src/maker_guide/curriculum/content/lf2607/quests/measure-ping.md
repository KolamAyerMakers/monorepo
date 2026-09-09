# Measure a ping

Quest: measure-ping

## Mission

Run `ping -c 3 1.1.1.1` and report the average round-trip time in `ms`, or `100% packet loss` if no replies provide an average. Ping tests ICMP, not whether a website works.

## Commands You Will Use

- `ping`

## Steps

1. Run `ping -c 3 1.1.1.1`.
2. Read the summary line at the end.
3. Find the average round-trip time if replies arrived. With no replies, read the packet-loss summary instead; do not invent an average.
4. Use `guide answer 'your observed result'` with the average and `ms`, or the observed `100% packet loss`.

## Hints

1. `-c 3` stops after three packets.
2. The average appears in the final timing summary.
3. Include `ms` for a timing value, or `% packet loss` when no average is available. ICMP may be blocked even when HTTP works.

## If Check Fails

Include the observed average and unit, or `100% packet loss` if there were no replies. The quest checks your reported result, not captured ping output. If ping could not run at all, ask for help rather than inventing a result.

## Related Reading

- [S6 self-study](../sessions/S06/self-study.md)
- [ping](../commands/ping.md)
- [network-diagnostics](../concepts/network-diagnostics.md)
