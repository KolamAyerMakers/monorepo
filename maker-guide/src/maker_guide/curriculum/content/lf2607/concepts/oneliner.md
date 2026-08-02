# One-Liners

## Core Idea

A one-liner is a small shell program typed at the prompt instead of saved in a script file.

It can combine commands, pipes, redirection, variables, command substitution, loops, and conditionals. This is where separate Linux skills start becoming one tool.

## Build It In Layers

Do not start with a clever compressed command. Build the pieces first.

```bash
cut -d: -f1 /etc/passwd
cut -d: -f1 /etc/passwd | wc -l
```

Then keep the final one-liner only if you can still explain every stage.

## Common Forms

Pipeline:

```bash
cut -d: -f1 /etc/passwd | wc -l
```

Run the next command only if the first succeeds:

```bash
mkdir -p ~/playground/oneliners && cd ~/playground/oneliners
```

Group several commands and redirect their combined output:

```bash
{ printf '# Status\n\n'; date; hostname; } > ~/src/pages/status.md
```

Loop over a list:

```bash
for path in ~/src/pages/*.md; do printf '%s\n' "$path"; done
```

Branch on a command result:

```bash
if curl -fsS https://example.org >/dev/null; then printf 'up\n'; else printf 'down\n'; fi
```

Use command output as an argument:

```bash
printf 'host=%s date=%s\n' "$(hostname)" "$(date +%F)"
```

## When To Stop Being Clever

Move the one-liner into a script when it is reused, risky, hard to quote, hard to explain, or longer than one screen line.

A good one-liner is compressed, not mysterious. The skill is composition, not showing off.

## Safety Rules

- Expand and test each piece before combining it.
- Quote variables and command substitutions.
- Prefer `&&` when the second command depends on the first succeeding.
- Use scratch paths before touching course source files.
- Read destructive commands twice before pressing Enter.
- If history would not explain it to future you, make it a script.

## Proof Check

Write one one-liner that creates a Markdown file containing a heading, the current date, and the hostname. Then rewrite it as a multi-line script. Explain why both versions do the same work.

## Docs Pointers

- Run `man bash`, then read `Pipelines`, `Lists`, `Compound Commands`, and `Command Substitution`.
- Read [pipes](pipes.md), [stream redirection](stream-redirection.md), [control flow](control-flow.md), [loops](loops.md), [conditionals](conditionals.md), and [shell scripting](shell-scripting.md).
