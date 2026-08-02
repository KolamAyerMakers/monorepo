# Platform Reference

Use this page when a quest says "your server", "your first URL", "your second URL", "your port", IRC, Forgejo, or web SSH.

## Fixed Names

- SSH server: `lf2607.kolamayermakers.org`
- Web SSH: browser terminal for onboarding only
- Course static site host: `lf2607.kolamayermakers.org`
- IRC web client: [lf2607.kolamayermakers.org/irc/](https://lf2607.kolamayermakers.org/irc/)
- IRC channel: `#lf2607`
- Forgejo web UI: [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/)
- Forgejo SSH host: `lf2607.kolamayermakers.org`
- Course bot: the guide.
- Static site source: `~/src/pages/`
- Static site output: `~/public_html/`
- User service unit path: `~/.config/systemd/user/site.service`
- User timer path: `~/.config/systemd/user/site-build.timer`

## guide checks

Use the guide throughout the course for help, objectives, quests, answer submission, and progress checks. In a terminal, run `guide now` to see your current session objective. After you complete it, `guide now` shows your current quest. Submit a prompted answer with `guide answer 'your answer'`; after practical work, run `guide check`. In an IRC DM to `guide`, send only `now`, `answer <your answer>`, or `check`. The guide checks explicit evidence such as command history, files, and answers, then records score and progress when the check passes. Chat responses can help you understand what to do, but progress requires a passing check. Read [scoring and rankings](scoring.md) for every score award, tier, ranking tie-breaker, and the points ledger.

The guide uses only course-approved evidence for checks. Do not paste secrets into IRC or chat: no passwords, private keys, access tokens, or private setup links.

## IRC Shape

Use your course username as your IRC nickname. Join `#lf2607` for public help, completion announcements, and coordination.

If your nickname is already in use, check whether you are still connected in another browser tab or client. If you need a temporary suffix, tell the instructor and switch back to your course username after the stale session disconnects.

The web IRC entry point is [lf2607.kolamayermakers.org/irc/](https://lf2607.kolamayermakers.org/irc/).

## Forgejo Shape

Forgejo is the class git server. Use the same course username and password as your Unix and IRC account.

- Web UI: [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/)
- Repository name for site source: `src`
- Local source path: `~/src`
- Remote name: `origin`
- HTTPS remote shape: `https://lf2607.kolamayermakers.org/git/username/src.git`
- SSH remote shape: `git@lf2607.kolamayermakers.org:username/src.git`

Use HTTPS first unless the instructor has confirmed your Forgejo SSH key setup. Verify the remote with `git remote -v` before pushing.

## Login Shape

```bash
ssh username@lf2607.kolamayermakers.org
```

The `new@lf2607.kolamayermakers.org` account is only the onboarding door. It creates your real account, prints the real SSH command, then disconnects.

Use the [password guide](passwords.md) when choosing or changing your classroom passphrase.

## Web SSH Graduation

Web SSH is an onboarding bridge. Use it when browser access is the only thing working or when you are still learning enough SSH to recover from mistakes.

Normal SSH is the target skill:

```bash
ssh username@lf2607.kolamayermakers.org
```

Web SSH recovery is available to Linux Foundations course members. It is not a graduation gate: use it whenever browser access is the only working path.

## Public URL Shapes

Static page URL:

```text
https://lf2607.kolamayermakers.org/~username/
```

User service URL:

```text
https://username.lf2607.kolamayermakers.org/
```

If the service URL does not resolve, collect local evidence before asking for routing help:

```bash
host "$(whoami).lf2607.kolamayermakers.org"
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
systemctl --user status site.service
```

If local curl works and the public hostname does not resolve, bring those exact outputs to the instructor as a routing issue.

## Service Port Formula

In this course only, your personal service port is `10000 + uid`.

```bash
printf '%s\n' "$((10000 + $(id -u)))"
```

Use the result anywhere a service quest says `PORT`.

Ports are numeric. If your computed value is above `65535`, stop and ask the instructor because that account id does not fit this course port formula.

## Proof Commands

```bash
whoami
pwd
ls -la ~
curl -I https://lf2607.kolamayermakers.org/~username/
git -C ~/src remote -v
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 50
```

## Docs Pointers

- [OpenSSH manual index](https://man.openbsd.org/ssh)
- [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [curl manual](https://curl.se/docs/manpage.html)
- [Python http.server documentation](https://docs.python.org/3/library/http.server.html)
