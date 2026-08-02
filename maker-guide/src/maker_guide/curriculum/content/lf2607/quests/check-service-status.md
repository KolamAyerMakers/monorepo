# Check service status

Quest: check-service-status

## Mission

Run `systemctl --user status site.service` and identify whether it is active.

## Commands You Will Use

- `systemctl --user`

## Steps

1. Run `systemctl --user status site.service`.
2. Find the service state.
3. Answer the guide with the state you saw.

## Hints

1. Systemd reports service state in the status output.
2. Look for words such as active or failed.
3. Mention `service` in your answer.

## If Check Fails

Run the status command again and answer with the service state.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [service](../concepts/service.md)
- [systemd user services](../concepts/systemd-user-services.md)
