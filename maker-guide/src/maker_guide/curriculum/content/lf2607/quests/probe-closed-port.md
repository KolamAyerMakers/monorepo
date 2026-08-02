# Probe a closed port

Quest: probe-closed-port

## Mission

Use `nc` against a port with no service and describe the failure.

## Commands You Will Use

- `nc`

## Steps

1. Pick a local port where you do not have a service running.
2. Run `nc -vz 127.0.0.1 <port>`.
3. Read the failure message.
4. Answer the guide with what happened.

## Hints

1. A closed port is useful evidence.
2. The exact wording can vary.
3. Use words like refused, closed, or failed in your answer.

## If Check Fails

Run the `nc` probe again and answer with the failure message.

## Related Reading

- [nc](../commands/nc.md)
- [sockets](../concepts/sockets.md)
- [reverse proxy](../concepts/reverse-proxy.md)
