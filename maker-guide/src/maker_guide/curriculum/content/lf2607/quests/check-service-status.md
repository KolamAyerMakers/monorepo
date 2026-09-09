# Check service status

Quest: check-service-status

## Mission

Run `systemctl --user status site.service` and report the state it actually shows. Reading a stopped or failed service correctly is part of the mission, not an incorrect answer.

## Commands You Will Use

- `systemctl --user`

## Steps

1. Run `systemctl --user status site.service`.
2. Find the `Active:` line. It may say `active (running)`, `inactive (dead)`, `failed`, or a transitional state such as `activating`.
3. Answer with the unit name and your observed state using `guide answer 'your observation'`. Do not copy `active` if the service is inactive or failed.
4. If the unit is missing, report `Unit site.service could not be found` rather than inventing a state. Press `q` to leave a status pager.

## Hints

1. The `Loaded:` line describes the unit file and enablement; `Active:` describes its current runtime state.
2. A nonzero exit status from `systemctl status` is normal for an inactive or failed unit. Preserve that evidence.
3. An active process is not proof of HTTP 200. Inspect responses separately.

## Repair Next

After reporting what you saw, repair a service that should be running:

- If the unit is missing, follow [enable-site-service](enable-site-service.md).
- If it is inactive, run `systemctl --user start site.service`, then inspect status again.
- If it failed, read `journalctl --user -u site.service --no-pager -n 50` before editing. Stop your manual server if the assigned port is occupied; do not change the assigned port or kill another learner's process.
- After a unit edit, run `systemctl --user daemon-reload`, then `systemctl --user restart site.service`, and repeat the endpoint checks in the enable-service quest.

Repair is a next step, not permission to rewrite the original observation. Keep `--user`; do not use `sudo`.

## If Check Fails

Run the status command again and name `site.service` with the exact state you saw. If the guide rejects a truthful inactive or failed observation, bring the output to staff; do not fabricate a running service to satisfy it.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [service](../concepts/service.md)
- [systemd user services](../concepts/systemd-user-services.md)
