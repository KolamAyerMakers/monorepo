# Quest Index

Quests are highly recommended reinforcement. Use them for extra practice or catch-up. Live sessions remain the primary course path.

You can read any quest for independent practice and inspect the actual result. The bot's recorded reinforcement path is linear: `guide now` shows the current task, not an arbitrary quest selector, and there is no skip feature. If you want recorded progress, follow that task and run `guide now` before and after practical work; use `guide answer 'your answer'` when asked. See the dedicated [support guide](../guides/irc-support.md) and [scoring guide](../guides/scoring.md) for that optional workflow.

## S01 Reinforcement

- [prove-shell-alive](prove-shell-alive.md)
- [name-system](name-system.md)
- [count-home-entries](count-home-entries.md)
- [explain-ls](explain-ls.md)
- [read-file-ends](read-file-ends.md)

## S02 Reinforcement

- [build-playground](build-playground.md)
- [edit-with-micro](edit-with-micro.md)
- [redirect-and-append](redirect-and-append.md)
- [copy-and-inspect-ownership](copy-and-inspect-ownership.md)
- [personalize-homepage](personalize-homepage.md)

## S03 Reinforcement

- [count-stream](count-stream.md)
- [keep-pipeline-copy](keep-pipeline-copy.md)

## S04 Reinforcement

- [read-permissions](read-permissions.md)
- [make-file-executable](make-file-executable.md)
- [recover-directory-traversal](recover-directory-traversal.md)
- [commit-source](commit-source.md)
- [ignore-scratch-files](ignore-scratch-files.md)
- [explain-git-states](explain-git-states.md)

## S05 Reinforcement

- [extend-maker-report](extend-maker-report.md)
- [run-scripts-from-elsewhere](run-scripts-from-elsewhere.md)
- [preserve-maker-report](preserve-maker-report.md)

## S06 Reinforcement

Practise the observations and checker from the [S6 self-study](../sessions/S06/self-study.md), using its [diagnostic cases](../sessions/S06/self-study.md#diagnostic-cases). Equivalent implementations are welcome, not just the reference. Run `bash ~/scripts/site-check.sh "" maker-report.html` and inspect both pages in your browser; simulated results do not verify live site health.

- [resolve-hostname](resolve-hostname.md)
- [measure-ping](measure-ping.md)
- [read-http-headers](read-http-headers.md)
- [check-personal-pages](check-personal-pages.md)

## S07 Reinforcement

Run Your Own Web Server: foreground requests and visitor logs, own PID/listening-port correlation with `ps` and `ss`, and core raw HTTP with a path-only change. The [S7 self-study](../sessions/S07/self-study.md) covers three safe incidents: occupied own port, empty public practice root, and stopped backend, with recovery and comparison to independent static delivery. Publishing, notes, Git, and extra page quests below remain optional reinforcement; they are not required live-session deliverables.

The S7 reinforcement order puts core server work and diagnosis before publishing. Optional for the live lesson does not mean skippable within the bot's linear quest sequence.

- [serve-local-check-page](serve-local-check-page.md)
- [diagnose-second-url](diagnose-second-url.md)
- [explain-status-codes](explain-status-codes.md)
- [probe-closed-port](probe-closed-port.md)
- [inspect-first-url-headers](inspect-first-url-headers.md)
- [record-http-headers](record-http-headers.md)
- [document-service-port](document-service-port.md)

## S08 Reinforcement

Keep Your Server Running: supervision, journal evidence, safe repair, and logout observations. Tmux and helper functions are optional, not prerequisites for the service.

- [keep-tmux-workbench](keep-tmux-workbench.md)
- [write-site-helper-functions](write-site-helper-functions.md)
- [enable-site-service](enable-site-service.md)
- [watch-service-logs](watch-service-logs.md)
- [break-and-read-error](break-and-read-error.md)
- [fix-and-restart-service](fix-and-restart-service.md)
- [check-service-status](check-service-status.md)
- [restart-service-cleanly](restart-service-cleanly.md)
- [read-recent-logs](read-recent-logs.md)
- [add-health-page](add-health-page.md)
- [explain-user-services](explain-user-services.md)
- [preflight-both-urls](preflight-both-urls.md)

## S09 Reinforcement

Automate It. Hand It Over. Refresh report facts before building, observe automatic publication, and peer-test a recoverable handoff of two scripts and three units. No `site.sh` dispatcher is required. Cron, sed, awk, vim, and the webring remain optional interests. Demo, investigation, and next-step quests are available here to prepare for S10, Show What You Can Do; their IDs stay unchanged.

- [try-cron-and-remove-it](try-cron-and-remove-it.md)
- [transform-heading-with-sed](transform-heading-with-sed.md)
- [extract-fields-with-awk](extract-fields-with-awk.md)
- [survive-vim](survive-vim.md)
- [write-readme](write-readme.md)
- [enable-webring](enable-webring.md)
- [schedule-site-rebuilds](schedule-site-rebuilds.md)
- [refresh-pipes-for-bandit](refresh-pipes-for-bandit.md)
- [prepare-bandit-approach](prepare-bandit-approach.md)
- [demo-site](demo-site.md)
- [write-next-path](write-next-path.md)
- [prepare-source-handoff](prepare-source-handoff.md)
- [use-terminal-irc](use-terminal-irc.md)
