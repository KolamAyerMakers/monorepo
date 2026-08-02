# Demo your site

Quest: demo-site

## Mission

Show your public site, source repo, service, and README to another person.

## Commands You Will Use

- `curl`
- `git log`
- `systemctl --user`

## Steps

1. Run `curl -I "https://lf2607.kolamayermakers.org/~$(whoami)/"`.
2. Run `git -C ~/src remote -v` and `git -C ~/src log --oneline -5`.
3. Open your Forgejo source repo in the browser.
4. Run `systemctl --user status site.service`.
5. Run `journalctl --user -u site.service --no-pager -n 20`.
6. Point at the README.
7. Answer the guide with what you demoed.

## Hints

1. A demo is proof, not a speech.
2. Show the running thing and the source that creates it.
3. Use the word `site` in your answer.

## If Check Fails

Answer again with the site feature you showed and what feedback you got.

## Related Reading

- [multi-page sites](../concepts/multi-page-sites.md)
- [Forgejo publishing](../concepts/forgejo-publishing.md)
- [README writing](../concepts/readme-writing.md)
- [systemd user services](../concepts/systemd-user-services.md)
