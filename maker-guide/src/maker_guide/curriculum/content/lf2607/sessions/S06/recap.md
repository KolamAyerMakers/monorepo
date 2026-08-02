# S6 Recap: Decisions And Networks

Session: S6

## Core Idea

Shell scripts can branch, repeat, and ask other machines for data.

## Remember

- `if` handles choices.
- `for` and `while` handle repetition.
- `curl` fetches data.
- Network output is still text you can save, inspect, and publish.

## Live Core

If you attended live, you have the core milestone when you can write one branch, one loop, one DNS or ping check, and one `curl -I` check.

## Optional Reinforcement

Use the S6 quests if you want repetition across control flow and networking. They resolve DNS, save network evidence, and publish fetched output. Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

## Can You Explain This?

- When should you use `for` instead of `while`?
- Why does `[[ -e "$1" ]]` need quotes?
- What does `curl -I` show that plain `curl` does not?

## Keep

Keep `alive.sh` if you made it. It is useful optional evidence that combines arguments, networking, and branching.

## Full Autonomy

Use [S6 Self-Study Guide: Control Flow And Networking](self-study.md) for loop examples, exit status, network diagnostics, and the fetched-content publishing pattern.
