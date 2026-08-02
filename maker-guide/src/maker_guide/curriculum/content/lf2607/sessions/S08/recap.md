# S8 Recap: Your Own Service

Session: S8

## Core Idea

A website can be served by a process you own.

## Remember

- Tmux keeps a foreground process available when SSH disconnects.
- Shell child processes die when the shell exits.
- A user service can be managed independently.
- Logs are not decoration. They are evidence.
- `systemctl --user status` is the first question when a service misbehaves.

## Live Core

If you attended live, you have the core milestone when you can complete the tmux lifecycle and `site.service` exists, uses your user port, and can be checked with `systemctl --user status` and `journalctl --user`.

## Optional Reinforcement

Use the S8 quests if you want deeper service practice. They add helper functions, break/fix practice, health checks, service notes, and URL preflight. Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

## Can You Explain This?

- Why can tmux survive an SSH disconnect but not a server reboot?
- What process serves your second URL?
- Why does `daemon-reload` matter after editing a unit file?
- Where do service errors appear?

## Keep

Keep `~/bin/site.sh` and `~/.config/systemd/user/site.service`; they become part of the final demo and README.

## Full Autonomy

Use [S8 Self-Study Guide: Your Own Web Service](self-study.md) for the tmux workflow, helper script, unit file, port formula, systemctl lifecycle, journal checks, and safe break lab.
