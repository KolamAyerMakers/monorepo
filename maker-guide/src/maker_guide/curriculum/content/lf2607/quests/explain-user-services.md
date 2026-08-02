# Explain user services

Quest: explain-user-services

## Mission

Explain the difference between a user service and a system service.

## Commands You Will Use

- `systemctl --user`

## Steps

1. Inspect your user service with `systemctl --user`.
2. Identify which account owns it.
3. Answer the guide with why it is a user service.

## Hints

1. `--user` is the clue.
2. Your account owns this service.
3. Mention user service scope in the answer.

## If Check Fails

Answer again and explicitly mention that `site.service` runs in user scope.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [service](../concepts/service.md)
- [systemd user services](../concepts/systemd-user-services.md)
