# Explain user services

Quest: explain-user-services

## Mission

Explain the difference between a user service and a system service.

## Inspect And Explain

```bash
systemctl --user status site.service
```

Press `q` to leave. Which manager runs this service, and under whose account? Why does controlling it not change the machine's SSH service?

Explain in your own words with `guide answer 'Your explanation'` when this quest is current.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [service](../concepts/service.md)
- [systemd user services](../concepts/systemd-user-services.md)
