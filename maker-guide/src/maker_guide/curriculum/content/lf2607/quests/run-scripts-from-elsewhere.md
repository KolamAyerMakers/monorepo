# Run scripts from elsewhere

Quest: run-scripts-from-elsewhere

## Mission

Change to `~/playground`, then run `maker-report.sh` with a quoted title using its home-anchored `~/...` path.

## Commands You Will Use

- `cd`

## Steps

1. Run `guide now` so this quest is assigned before you create evidence.
2. Run `cd ~/playground`.
3. Run `~/scripts/maker-report.sh "Elsewhere Report"`.
4. Run `guide check`.

## Hints

1. Your current directory and the script path answer different questions.
2. `~/scripts/maker-report.sh` points to the same file from anywhere in your home.
3. `./maker-report.sh` would mean a file in `~/playground`; the home-anchored path reaches the script in `~/scripts`.
4. `bash ~/scripts/maker-report.sh "Elsewhere Report"` also works, but direct execution proves the script is executable.

## If Check Fails

Run `cd ~/playground`, then `~/scripts/maker-report.sh "Elsewhere Report"`. Run `guide check` promptly after those successful commands.

## Related Reading

- [cd](../commands/cd.md)
- [path](../concepts/path.md)
- [shell scripting](../concepts/shell-scripting.md)
