# Shell Scripting

## Core Idea

A shell script is a file of commands that Bash can run repeatably.

Start with commands that already work at the prompt. Save them one per line, run the file, then change one thing at a time.

## Practice Alone

Save commands that already work at the prompt into `~/scripts/report.sh`: start the file with `#!/bin/bash` and put one command per line below it.

Run the file explicitly with Bash:

```bash
bash report.sh
```

Try the current-directory path before changing permissions, then add execute permission for the user who owns the file:

```bash
./report.sh
chmod u+x report.sh
./report.sh
```

## Done When

Your script works twice in a row without manual fixes.

You can explain how `bash path` differs from `./path`, why a quoted argument remains one value, and how grouped commands can share one redirection.

## Go Deeper

- [Shebang](shebang.md) explains why the first line chooses the interpreter for direct execution.
- [Script permissions](script-permissions.md) explains why `chmod u+x` matters.
- [Environment variables](environment-variables.md) explains the values scripts inherit.
- [exit](../commands/exit.md) explains how later scripts report failure deliberately.
- [One-liners](oneliner.md) explains when a short shell program can stay at the prompt.
