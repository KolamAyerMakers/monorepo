# Docs Navigation Guide

The classroom docs are files. Learn to move through them the same way you move through your home directory.

## Start Here

```bash
glow -p /docs/README.md
```

That page is the course map. Command cards, concept cards, and general guides are available from the start. Released session and quest links appear in `/docs/README.md` after mentors publish them.

## Read A Link

Markdown links look like this:

```markdown
[SSH command card](../commands/ssh.md)
```

The part in parentheses is the file path. Open it with `glow -p`:

```bash
glow -p /docs/commands/ssh.md
```

If a link starts with `/docs`, it is an absolute path. You can open it from anywhere.

## Move Through The Docs

```bash
cd /docs
pwd
ls
```

Useful places:

- `/docs/README.md`: course map and released coursework.
- `/docs/commands/README.md`: command card index.
- `/docs/concepts/README.md`: concept card index.
- `/docs/guides/`: platform, password, IRC, scoring, and docs navigation guides.

Do not guess a session or quest path. Open `/docs/README.md`; released sessions and quests appear there.

Open files with absolute `/docs` paths so the command works from anywhere:

```bash
glow -p /docs/concepts/shell.md
```

Go back to the course map:

```bash
glow -p /docs/README.md
```

## Find A File

List every Markdown file:

```bash
find /docs -name '*.md' | sort
```

Find filenames that mention a topic:

```bash
find /docs -iname '*ssh*'
```

Search inside the docs:

```bash
grep -Rni 'ssh key' /docs
```

Read the matching file with `glow -p`.

## Use Glow Without Getting Stuck

- Scroll with the arrow keys, `Space`, and `b`.
- Search inside the open file with `/`, then type the word and press `Enter`.
- Jump to the next match with `n`.
- Quit with `q`.

If `glow -p` feels too fancy, use `less`:

```bash
less /docs/README.md
```

Quit `less` with `q`.

## Before Asking For Help

Do this first:

1. Open the course map: `glow -p /docs/README.md`.
2. If a session is listed there, open its guide from that link.
3. Search the docs for the command, concept, or error text.
4. Read one linked command card or concept card.
5. Ask the guide or IRC with the command you ran, the file you read, and the exact error.

Good help request:

```text
I read /docs/README.md and /docs/commands/ssh.md.
I ran: ssh myhandle@lf2607.kolamayermakers.org
The error is: Permission denied.
What should I check next?
```
