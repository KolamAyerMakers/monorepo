# S5 Recap: Make The Shell Work For You

Session: S5

## What You Built

`~/scripts/maker-report.sh` accepts one title, collects live system facts, and writes `~/src/pages/maker-report.md`. `build-website` turns that Markdown into `maker-report.html`.

## Four Models

```text
bash maker-report.sh -> start Bash explicitly; execute permission is not needed
./maker-report.sh    -> run the file here; requires execute permission and a shebang
```

```text
"My Maker Report" -> $1 -> report_title="$1" -> "$report_title" -> one value
```

```text
{
  many commands
} > file

many stdout streams -> one generated file
```

```text
maker-report.sh -> maker-report.md -> build-website -> maker-report.html
```

## Details Worth Remembering

- `.sh` is a filename convention, not executable permission.
- `.` means the current directory, so `./maker-report.sh` names the file here.
- In `chmod u+x`, `u` is the user who owns the file and `x` is execute permission.
- `#!/bin/bash` tells Linux to use Bash when the file is run directly.
- Shell assignment has no spaces around `=`.
- Quotes are needed both when passing a multi-word argument and when expanding it.
- Triple backticks open and close the report's plain-text code block.
- `bash -x` reveals commands as Bash runs them and keeps its trace on stderr.

## Repeat The Safe Workflow

```bash
cd ~/scripts
bash -n maker-report.sh
./maker-report.sh "Fresh Report"
cat ~/src/pages/maker-report.md
build-website
```

## Optional Reinforcement

For extra practice, add uptime, run the script from another directory, and preserve it in Git.

The self-study guide also contains an optional shell-options appendix. It demonstrates `set -u` with an unset `$1`, then `set -e` with one standalone failed command. These options reveal failures; they do not replace input checks or explicit error handling.

## Can You Explain This?

- Why can `bash maker-report.sh` run a non-executable text file?
- What does `./` mean?
- What does `chmod u+x` change?
- What does the `#!/bin/bash` first line tell Linux?
- Why is `report_title = "$1"` wrong?
- Why do both the caller and the script use quotes?
- How does one `>` capture output from every command inside `{ ... }`?

## Full Autonomy

Use [S5 Self-Study Guide: Make The Shell Work For You](self-study.md) for every exercise, the complete script, reset steps, and symptom-based recovery.
