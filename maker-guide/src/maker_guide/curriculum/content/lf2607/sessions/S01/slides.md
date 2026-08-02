# Linux Foundations S1

Session: S1

First contact: SSH and the lay of the land

Today you get a real account on a real Linux server.

<!-- end_slide -->

# The Contract

This course is not about memorizing commands.

It is about learning how to ask the machine clear questions.

If you can read what Linux says back, you can keep going.

<!-- end_slide -->

# Your Identity

One handle.

The same handle is your Unix username.

Pick something you can live with.

<!-- end_slide -->

# Create Your Account

Hands-on now: everyone follows this on their own laptop.

Windows: open Windows Terminal from Start.

macOS: open Terminal from Applications > Utilities.

No SSH client? Use the [browser registration page](https://lf2607.kolamayermakers.org/register/).

```bash
ssh new@lf2607.kolamayermakers.org
```

The kiosk creates your real account, prints your real SSH command, then disconnects.

`new` never gives you a shell. It is only the door.

<!-- end_slide -->

# Reconnect As Yourself

Hands-on now: stop using `new`; rerun the personal SSH command the kiosk printed.

No SSH client? Reconnect with [browser SSH](https://lf2607.kolamayermakers.org/ssh/).

Your personal-account prompt is not decoration.

It tells you who you are, where you are, and whether the shell is waiting.

<!-- end_slide -->

# Mental Model: Talking to Linux

SSH connects you to a remote computer.

A shell is the text program waiting at the prompt.

```bash
command option argument
ls      -la    /docs
```

You type a command. The shell runs it. Linux prints a result or an error.

<!-- end_slide -->

# Ask The Machine

Hands-on now: type each command and read the output before moving on.

```bash
whoami    # show current username
hostname  # show machine name
date      # show current date and time
uptime    # show server uptime and load
```

No magic. No guessing.

Commands go in. Text comes out.

<!-- end_slide -->

# Do Not Panic

Hands-on now: run `guide` and ask it one question.

```bash
guide
```

`guide` is your course tool and AI tutor. Use it throughout class and between sessions for help, objectives, quests, answer submission, and progress checks.

In a terminal, guide requests always start with `guide`:

```bash
guide now
guide check
guide answer 'your answer'
```

In an IRC DM to `guide`, send the request without `guide`: `now`, `check`, or `answer <your answer>`. A passing check records your progress.

Your recovery kit:

- Tab completion
- Ctrl-C to cancel
- Ctrl-L to clear the screen
- `man <command>`
- `tldr <command>`
- read the error

<!-- end_slide -->

# IRC and guide

IRC is the public classroom backchannel.

Hands-on task: join IRC now at [the classroom IRC page](https://lf2607.kolamayermakers.org/irc/).

Use `#lf2607` to ask for help during class or between sessions.

Use `#kolamayermakers` for general chat.

DM `guide` for help from the AI tutor. It is the same tutor as the `guide` command.

Do not paste passwords, private keys, or tokens.

<!-- end_slide -->

# The Filesystem

```text
/
├── home/
│   └── <you>/  your home: ~
├── docs/       course materials
└── etc/        system settings
```

Every file and directory belongs somewhere below `/`.

<!-- end_slide -->

# Filesystem Map

Hands-on now: move slowly. The goal is to know where you are.

```bash
pwd         # show current directory
ls          # list files
ls -la      # include hidden files
cd ~        # go home
cd ..       # go up one directory
cd /docs    # go to course materials
tree        # show directory structure
find /docs  # list everything under /docs
```

`/docs` is your course-material playground. Read anything in it and follow what interests you.

You are not inside an app. You are inside this filesystem.

<!-- end_slide -->

# Reading Files

Hands-on now: open files, then practise leaving `less` with `q`.

```bash
cat /etc/os-release      # print operating system info
less /etc/services       # read one page at a time
head -n 5 /etc/services  # show first five lines
```

Files are how Unix systems explain themselves.

<!-- end_slide -->

# Your Page Goes Live

Hands-on now: build first, understand the script later.

```bash
build-website
```

Check your page at `https://lf2607.kolamayermakers.org/~<username>/`, replacing `<username>` with the username you chose.

For example: [https://lf2607.kolamayermakers.org/~johndoe/](https://lf2607.kolamayermakers.org/~johndoe/).

You will not understand the build script yet.

That is fine. Use it first. Read it later.

<!-- end_slide -->

# After Class

Use quests between sessions for highly recommended reinforcement or catch-up.

Run `guide now` to get the current session objective. After you complete it, `guide now` shows your current quest. Ask the guide for help, submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work to record progress.

If stuck outside class, read the S1 recap or self-study guide, then ask in public help.

Read the full course as formatted web pages at [lf2607.kolamayermakers.org/docs](https://lf2607.kolamayermakers.org/docs/).

Autonomy starts today.
