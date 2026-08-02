# S5 Recap: Scripting Begins

Session: S5

## Core Idea

A script is a saved conversation with the shell.

## Remember

- Start scripts with a shebang.
- Exit status `0` means success; nonzero means failure.
- Fail loudly with `set -euo pipefail`.
- Quote variables unless you know why you are not quoting them.
- Make scripts executable before running them directly.

## Live Core

If you attended live, you have the core milestone when you have one script with a shebang, `set -euo pipefail`, quoted variables, `printf`, and executable permission.

## Optional Reinforcement

Use the S5 quests if you want a stronger script collection. They harden arguments, quoting, documentation, output capture, and path usage. Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

## Can You Explain This?

- What does `$1` mean?
- Why does the missing-argument path use `exit 1`?
- Why is `printf` more predictable than `echo`?
- What does executable permission add?

## Keep

Keep the live script. Optional quests can expand it into a reusable script collection.

## Full Autonomy

Use [S5 Self-Study Guide: Scripting Begins](self-study.md) for the script template, exit status, `set -euo pipefail`, argument guards, quoting examples, and debugging symptoms.
