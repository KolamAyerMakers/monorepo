# Run scripts from elsewhere

Quest: run-scripts-from-elsewhere

## Mission

Change to `~/playground`, confirm the directory, then run `maker-report.sh` with Bash and a quoted title using its home-anchored `~/...` path.

## Commands You Will Use

- `mkdir`
- `pwd`
- `cd`
- `bash`
- `build-website`

## Steps

1. Run `guide now` so this quest is assigned before you create evidence.
2. Run `mkdir -p ~/playground`.
3. Run `cd ~/playground`.
4. Run `pwd` and confirm that it ends in `/playground`.
5. Run `bash ~/scripts/maker-report.sh "Elsewhere Report"`.
6. Run `build-website` so the HTML matches the new Markdown report.
7. Run `guide check`.

## Hints

1. Your current directory and the script path answer different questions.
2. `~/scripts/maker-report.sh` points to the same file from anywhere in your home.
3. `./maker-report.sh` would mean a file in `~/playground`; the home-anchored path reaches the script in `~/scripts`.
4. The guide needs `cd ~/playground`, `pwd`, a quoted `bash ~/scripts/maker-report.sh ...` run, then `build-website` in that order.

## If Check Fails

Run `mkdir -p ~/playground`, then `cd ~/playground`, `pwd`, `bash ~/scripts/maker-report.sh "Elsewhere Report"`, and `build-website`. Run `guide check` promptly after those successful commands.

## Related Reading

- [pwd](../commands/pwd.md)
- [cd](../commands/cd.md)
- [bash](../commands/bash.md)
- [build website](../commands/build-website.md)
- [path](../concepts/path.md)
- [shell scripting](../concepts/shell-scripting.md)
