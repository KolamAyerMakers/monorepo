# Demo your site

Quest: demo-site

## Mission

Show your existing site and report, source repo, real backend service, and README to another person. These are the normal graduation core, not optional extras.

## Commands You Will Use

- `curl`
- `git log`
- `systemctl --user`

## Return To The Classroom

If you are in Bandit, run `exit` to close that connection and use `whoami` and `hostname` to confirm where you are. Exit any remaining nested Bandit connection. If you return to your laptop instead of the classroom, reconnect with `ssh your-classroom-username@lf2607.kolamayermakers.org`, replacing `your-classroom-username` with your classroom account. Do not use the laptop's `$USER` as if it were your classroom username.

The commands below run in the classroom, where your project, scripts, and user services live. Use your laptop browser for the outside view.

## Check The Existing Project

```bash
bash ~/scripts/site-check.sh
PORT="$(~/bin/site.sh site_port)"
printf 'Service port: %s\n' "$PORT"
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user status site.service --no-pager
```

The checker covers the static homepage and report. The helper prints the S8 port, `10000 + uid`. Read the actual HTTP responses; neither a successful static request nor an active service proves that the public backend route works.

## Prove The Report Body

Use fresh scratch files so you do not overwrite existing work:

```bash
demo_directory="$(mktemp -d /tmp/site-demo.XXXXXX)"
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$demo_directory/static-report.html"
curl -fsS "http://127.0.0.1:$PORT/maker-report.html" -o "$demo_directory/local-report.html"
curl -fsS "https://$USER.lf2607.kolamayermakers.org/maker-report.html" -o "$demo_directory/service-report.html"
diff ~/public_html/maker-report.html "$demo_directory/static-report.html"
diff ~/public_html/maker-report.html "$demo_directory/local-report.html"
diff ~/public_html/maker-report.html "$demo_directory/service-report.html"
journalctl --user -u site.service --no-pager -n 20
```

`-f` makes HTTP errors fail, `-sS` hides progress but shows errors, and `-o` saves the response body. Stop and diagnose failed requests. Successful fetches and no `diff` output show the report matches disk through all three routes. Point to the actual report requests in the service journal.

## Show Source And The Outside View

```bash
git -C ~/src remote -v
git -C ~/src log --oneline -5
git -C ~/src status
cat ~/src/README.md
ls -l ~/src/scripts ~/src/services
systemctl --user list-timers
journalctl --user -u site-build.service --no-pager -n 20
```

1. Open both public URLs and their report page in your laptop browser. Type your real classroom username in place of `$USER`; a browser does not expand shell variables.
2. Open your Forgejo repo and show the latest commit, README, site/report source, and all six [handoff copies](prepare-source-handoff.md#copy-working-files).
3. Explain how `maker-report.sh` collects facts, while the builder and timer only render existing Markdown. Explain one failure and recovery from your own work.
4. Answer the guide with the site feature you showed, actual HTTP/body/log results, and feedback you received. Do not present expected output as observed evidence.

## Hints

1. A demo is proof, not a speech.
2. Show the running backend, the source that creates its pages, and the units that run it.
3. If you missed S8 or S9, agree with the instructor on an explicitly reduced demo, name the missing artifacts, and date the recovery work.

## If Check Fails

Inspect actual failures before answering again. Static `404` means check the source/build/output path. A personal URL `502` means compare the local port request, service status, and journal. If local requests work but public DNS does not, collect the [platform-reference evidence](../guides/platform-reference.md) and ask the instructor. A failed public request is not a completed end-to-end demo.

## Related Reading

- [multi-page sites](../concepts/multi-page-sites.md)
- [Forgejo publishing](../concepts/forgejo-publishing.md)
- [README writing](../concepts/readme-writing.md)
- [systemd user services](../concepts/systemd-user-services.md)
