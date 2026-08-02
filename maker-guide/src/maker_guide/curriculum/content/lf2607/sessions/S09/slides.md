# Linux Foundations S9

Session: S9

Polish: timers, markdown, vim, webring

<!-- end_slide -->

# Today's Story

Useful systems run again tomorrow without you remembering.

Teacher shows the automation loop, then learners polish their own site source.

<!-- end_slide -->

# Hands-On Spine

Hands-on now: inspect timers, edit source, rebuild, and verify output.

```bash
systemctl --user list-timers
sed
awk
vim
micro ~/src/site.toml
build-website
grep -i webring ~/public_html/index.html
```

<!-- end_slide -->

# Exit Goal

Learners polish the site, write enough README for another person, and join the cohort webring from source configuration.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Try a temporary cron job and remove it.
2. Transform a heading with `sed`.
3. Extract fields with `awk`.
4. Save and quit from vim.
5. Write a README and push it.
6. Schedule rebuilds with a user timer.
7. Refresh pipelines for Bandit.

<!-- end_slide -->

# Polish Means Reproducible

Your site should have source, README, service files, logs, and a rebuild story.
