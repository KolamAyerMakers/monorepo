# Control Flow

## Core Idea

Control flow is how a shell program chooses what happens next.

Without control flow, a script is just a fixed list of commands. With control flow, scripts can branch on success, repeat work, and stop when checks fail.

## Main Tools

- [Conditionals](conditionals.md): choose a branch with `if`.
- [Loops](loops.md): repeat commands with `for` or `while`.
- [Exit status](../commands/exit.md): communicate success or failure.
- [One-liners](oneliner.md): combine control flow at the prompt when it stays readable.

## Example

```bash
if [[ -f ~/src/pages/index.md ]]; then
  printf 'source exists\n'
else
  printf 'missing source\n' >&2
  exit 1
fi
```

## Watch Out

Readable control flow beats clever control flow. If the command is hard to explain, make it a script with clear lines.

## Docs Pointers

- Run `help if`, `help for`, and `help while`.
- Read [if](../commands/if.md), [for](../commands/for.md), [while](../commands/while.md), and [shell scripting](shell-scripting.md).
