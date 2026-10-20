# Concept: Shell Basics

At a Bash prompt, enter a command, press Enter, and read its result before continuing. Do not copy the prompt symbol itself.

```bash
pwd
printf 'hello\n'
ls /no/such/path
printf 'exit status: %s\n' "$?"
```

The first command reports your current directory; the next prints `hello`. The missing path produces an error, and the immediately following `$?` reports its nonzero exit status. Any command in between would replace that status.

No new prompt may mean a running command is waiting for input. `Ctrl-C` interrupts it. A continuation prompt such as `>` may mean an unfinished quote or command; cancel and check the line rather than typing unrelated commands into it.

## Go Deeper

- [Shell](shell.md) explains what Bash does before a program starts.
- [Terminal](terminal.md) explains the text interface carrying your keystrokes and output.
- [Readline](readline.md) gives the keystrokes that make command-line editing fast.
- [Environment Variables](environment-variables.md) explains values such as `$HOME`, `$USER`, and `$PATH`.
