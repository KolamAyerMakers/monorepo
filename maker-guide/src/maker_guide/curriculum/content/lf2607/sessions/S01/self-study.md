# S1 — First Contact

Learn where your commands run, move between directories, and read files without changing them.

**At home:** prepare Ubuntu using [Continue at Home](../../guides/continue-at-home.md). Skip classroom registration and chat. Run the exercises in your Ubuntu terminal.

## 1. Connect to the classroom

Open Windows Terminal on Windows, or Terminal on Mac. These are on **your computer**.

For a new account:

```bash
ssh new@lf2607.kolamayermakers.org
```

Choose your username and follow registration. The connection closes after printing your personal SSH command. Use that command to reconnect:

```bash
ssh username@lf2607.kolamayermakers.org
```

Replace `username` with yours. When entering a password, **nothing appears as you type**; type it and press Enter.

On your first connection, SSH asks about the server's host key. Compare its fingerprint with one supplied by the instructor through a trusted channel before accepting. If SSH later warns that the key changed, stop and verify the change; do not delete the old key just to silence the warning.

No SSH client? Use [browser registration](https://lf2607.kolamayermakers.org/register/) and [browser SSH](https://lf2607.kolamayermakers.org/ssh/).

## 2. Find out where you are

A **terminal** displays text. **SSH** connects you to another computer. The **shell** interprets commands there. After login, your commands run on the classroom server—not your laptop.

```bash
whoami
hostname
date
uptime
pwd
```

Check your username, machine name, time, and current directory. `uptime` shows how long the machine has been running and its load averages. `pwd` prints an absolute path, such as `/home/username`.

The prompt returns when the shell is ready for another command. Do not copy the prompt as part of a command.

## 3. Move around

| Path | Meaning |
|---|---|
| `/` | Filesystem root |
| `~` | Your home directory |
| `.` | Current directory |
| `..` | Parent directory |

```bash
cd ~
pwd
ls -la
cd /etc
pwd
cd ..
pwd
cd ~
```

`cd` changes directory; `ls` lists entries. `-l` adds details, and `-a` includes names starting with `.`. In this listing, `.` and `..` are not extra personal files.

## 4. Read before editing

```bash
cat /etc/os-release
head -n 5 /etc/services
tail -n 5 /etc/services
less /etc/services
```

`cat` prints the file, `head` its beginning, and `tail` its end. In `less`, use Space to advance, `/ssh` to search, and `q` to quit. Press `Ctrl-C` to interrupt a running command.

Find an option rather than guessing it:

```bash
man ls
```

Search for `-S` by typing `/-S`, then Enter. What does it sort by? Press `q` to return. If available, `tldr ls` gives shorter examples and `bat /etc/os-release` adds readable highlighting.

## 5. Find your course and first page

**Classroom shell:**

```bash
cd /docs
ls
less README.md
build-website
ls -l ~/public_html/index.html
```

Open `https://lf2607.kolamayermakers.org/~username/` in your laptop browser, replacing `username`. The build creates your starter source in `~/src` and publishes HTML in `~/public_html`.

**At home:** use the home guide's build command and local preview instead. `/docs` and `build-website` are classroom tools, not standard Linux commands.

When asking for help, include your command, exact error, and intended result. Never share passwords, private keys, or tokens.

## Check yourself

- Which computer runs `hostname` after SSH login?
- Where does `cd ..` take you from `/etc`?
- What is the difference between `cat`, `head`, and `less`?
- What does `ls -S` sort by?

[Compare your answers](../../guides/self-study-answers.md#s1-first-contact). For more detail: [Terminal](../../concepts/terminal.md), [Path](../../concepts/path.md), and [Reading Files](../../concepts/reading-files.md).

## If you get stuck

| Problem | Next step |
|---|---|
| SSH says `Permission denied` | Check the username before `@`; distinguish an account password from a key passphrase. |
| Registration starts again | You connected as `new`; use your personal username. |
| A file is missing | Run `pwd`, then list its parent directory. |
| You are lost | `cd ~` returns home; `pwd` confirms it. |
