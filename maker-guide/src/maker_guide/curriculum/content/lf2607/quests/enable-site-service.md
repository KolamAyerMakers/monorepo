# Enable site.service

Quest: enable-site-service

## Mission

Give your Caddy server to systemd so it runs independently of your terminal. Check the page, not just the process.

## Create The Unit

Use your own classroom SSH account and existing site. If manual Caddy is still running, stop it with `Ctrl-C` in its terminal first; it uses the same port.

Follow [Create the user unit](../sessions/S08/self-study.md#2-create-the-user-unit) for the complete `~/.config/systemd/user/site.service` file. Use your printed numeric port, `WorkingDirectory=%h`, and explicit `--root %h/public_html`. Read an existing unit before editing and preserve unrelated settings.

Control only your own service with `systemctl --user`. Never use `caddy stop` or `caddy reload`, which can target shared Caddy. No `sudo`, shared routing changes, or TLS bypasses are needed. Keep private files and symlinks to them out of the published root.

## Verify, Start, Enable

Check the unit without starting it:

```bash
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Fix reported mistakes, including warnings, then check again. `daemon-reload` reads the unit; `start` runs it now; `enable` arranges startup with your user manager:

```bash
systemctl --user daemon-reload
systemctl --user start site.service
systemctl --user enable site.service
systemctl --user status site.service
```

Look for `Active: active (running)`. Press `q` to leave. If you edited an already-running unit, use `systemctl --user restart site.service` after reloading to apply the change.

## Request Your Page

```bash
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Read the statuses and local HTML. Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) on your laptop, replacing `your-handle`. If it fails, use [Troubleshooting](../sessions/S08/self-study.md#troubleshooting).

Try the [logout experiment](../sessions/S08/self-study.md#9-test-logout-survival). An enabled unit can start again on login, so `active` after reconnecting alone is not proof that it kept running.

[Preserve the working unit](../sessions/S08/self-study.md#4-preserve-the-working-unit), then [watch its logs](watch-service-logs.md). Edit an existing page under `~/src/pages`, run `build-website`, and reload the browser to see the change without restarting Caddy.
