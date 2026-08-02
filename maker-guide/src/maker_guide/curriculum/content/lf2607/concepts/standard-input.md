# Standard Input

## Core Idea

Standard input is where commands read text when no filename is supplied.

Three common sources feed stdin:

- Your keyboard.
- A pipe from another command.
- A redirected file.

## Practice Alone

Type input into `read`, then pipe text into commands that read stdin.

```bash
printf 'Type your name: '
read -r name
printf 'Hello, %s\n' "$name"
```

Pipe text into a command:

```bash
printf 'one\ntwo\nthree\n' | wc -l
```

Redirect a file into stdin:

```bash
wc -l < /etc/services
```

## Watch Out

- A command may appear to hang because it is waiting for stdin. Press `Ctrl-C` if you need to stop it.
- `read` should usually use `-r` so backslashes are not treated specially.
- A pipe connects stdout from the left command to stdin of the right command.

## Done When

You can explain why pipes and `read` both depend on stdin.

## Docs Pointers

- Read [read](../commands/read.md), [pipes](pipes.md), [stream redirection](stream-redirection.md), and [I/O](io.md).
