# S1 Recap: First Contact

Session: S1

## What You Did

You created a real Unix account, logged into it with SSH, learned the shape of the shell, navigated the filesystem, read system files, and generated your starter page.

That is not pretend progress. A server accepted your login and served your page.

## Connect Again

Your chosen username is your Unix username. On Windows, open Windows Terminal from Start. On macOS, open Terminal from Applications > Utilities.

If you need to create an account without an SSH client, use the [browser registration page](https://lf2607.kolamayermakers.org/register/). To reconnect without an SSH client, use [browser SSH](https://lf2607.kolamayermakers.org/ssh/).

## Commands You Met

- `ssh`: connect to the server.
- `whoami`: print your current username.
- `hostname`: print the machine name.
- `date`: print the current system date and time.
- `uptime`: show server uptime and load.
- `pwd`: print your current directory.
- `cd ~`: go home.
- `cd ..`: go up one directory.
- `cd /docs`: go to course materials.
- `ls`: list files.
- `ls -la`: include hidden files.
- `tree`: show directory structure.
- `find /docs`: list everything under `/docs`.
- `cat /etc/os-release`: print operating system information.
- `less`: read one page at a time.
- `head -n 5`: show the first five lines of a file.
- `tail`: show the end of a file.
- `man`: open a manual page.
- `tldr`: read a short command summary.
- `build-website`: build your personal homepage.
- `clear`: clear the terminal screen.
- `exit`: leave the shell.

## Mental Model

The shell is a conversation:

1. You type a command.
2. The machine runs it.
3. The machine prints text back.
4. You read that text before typing again.

Your home directory is your base. System files such as `/etc/os-release` are readable clues about the machine.

`/docs` is your course-material playground. Run `cd /docs`, read anything in it, and follow what interests you.

## IRC and guide

Join IRC at [the classroom IRC page](https://lf2607.kolamayermakers.org/irc/). Use `#lf2607` for course help during class or between sessions, and `#kolamayermakers` for general chat.

`guide` is your course tool and AI tutor. Run it whenever you feel lost or have a question. DM `guide` on IRC for the same tutor. In a terminal, run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

Never paste passwords, private keys, tokens, or private account links into IRC.

## If You Are Stuck

- Run `pwd` to see where you are.
- Run `ls` to see what is near you.
- Use Tab completion instead of typing long paths blindly.
- Use Ctrl-C if a command will not stop.
- Press `q` to leave `less` or `man`.
- Read the error before asking for help.
- Run `guide` whenever you need help.

## Live Core

If you attended live and generated your starter page, you have the core milestone for S1.

- You can SSH into your account.
- You can explain the shell as text in and text out.
- You can navigate home, read files, and run `build-website`.

## Optional Reinforcement

Use the S1 quests if you want extra practice, missed the live session, or want guide-checked proof of the same shell and first-site skills. Run `guide now` to start, then submit prompted answers with `guide answer 'your answer'` or run `guide check` after practical work.

## Full Autonomy

If you missed the live session or got stuck, [S1 Self-Study Guide: First Contact](self-study.md) gives expected output shapes, recovery steps, and docs pointers. Use it before or after asking for help.
