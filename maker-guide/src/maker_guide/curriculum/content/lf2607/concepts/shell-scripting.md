# Shell Scripting

## Core Idea

A shell script is a file of commands that Bash can run repeatably.

Start with commands that already work at the prompt. Save them one per line, run the file, then change one thing at a time.

## Practice Alone

Create a script in a fresh temporary directory:

```bash
work=$(mktemp -d)
micro "$work/report.sh"
```

Save this content:

```bash
#!/bin/bash
printf 'User: %s\n' "$(whoami)"
printf 'Host: %s\n' "$(hostname)"
```

Run the file explicitly with Bash:

```bash
bash "$work/report.sh"
```

The direct path should initially fail with `Permission denied`. Add the owner's execute permission, then try again:

```bash
"$work/report.sh"
chmod u+x "$work/report.sh"
"$work/report.sh"
```

## Done When

Your script works twice in a row without manual fixes.

From the script's directory, `./report.sh` names the same file. Explain why `bash PATH` needed no execute bit but direct execution did.

## Go Deeper

- [Shebang](shebang.md) explains why the first line chooses the interpreter for direct execution.
- [Script permissions](script-permissions.md) explains why `chmod u+x` matters.
- [Environment variables](environment-variables.md) explains the values scripts inherit.
- [exit](../commands/exit.md) explains how later scripts report failure deliberately.
- [One-liners](oneliner.md) explains when a short shell program can stay at the prompt.
