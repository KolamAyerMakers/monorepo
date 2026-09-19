# Bash Functions

## Core Idea

A Bash function gives a name to a group of shell commands that run in the current shell.

Use functions to name repeated command sequences, either in an interactive shell or inside an executable script.

## Shape

Use a new or confirmed disposable `~/function-demo` directory, preserving any existing files. Check that Caddy is installed and port `8000` is unused as shown in the [Caddy card](../commands/caddy.md); choose another unused unprivileged port for this standalone demo if necessary.

```bash
mkdir -p "$HOME/function-demo"
printf '<h1>Demo</h1>\n' > "$HOME/function-demo/index.html"

serve() {
  caddy file-server --listen 127.0.0.1:8000 --root "$HOME/function-demo" --access-log
}
```

The first two commands create a demo page. The function definition names the body but does not execute it. Type `serve` to start the foreground HTTP server; press `Ctrl-C` to stop it. No configuration file is needed. The explicit root prevents a failed `cd` from leaving the server exposing the caller's directory instead; it is not a symlink sandbox. Do not use `caddy stop` or `caddy reload`: `file-server` disables the admin API and those commands might target another process.

## Arguments

Functions receive arguments as `$1`, `$2`, and `"$@"`, just like scripts.

```bash
page() {
  if [[ "$#" -lt 1 ]]; then
    printf 'usage: page NAME\n' >&2
    return 1
  fi

  micro "$HOME/function-demo/$1.html"
}
```

With the demo directory above in place, `page about` opens `about.html` in Micro. Use `return` inside a function. Use `exit` only when you want to end the whole shell or script.

## Return Status Versus Output

Functions have two different channels:

- Output: text printed to stdout.
- Return status: success or failure number used by `if`, `&&`, and scripts.

```bash
has_homepage() {
  [[ -f "$HOME/function-demo/index.html" ]]
}

if has_homepage; then
  printf 'homepage exists\n'
fi
```

This function prints nothing. Its status is the answer.

## Functions Versus Aliases

Aliases are text shortcuts. Functions are small programs.

Alias:

```bash
alias gs='git status'
```

Function:

```bash
gacp() {
  git add "$@"
  git commit
  git push
}
```

Use aliases for fixed abbreviations. Use functions when you need arguments, tests, variables, or several commands.

## Service Example

After creating and running `clock-note.service` with the [systemd timer card](../commands/systemd-timer.md), you can group its status and log commands:

```bash
status() {
  systemctl --user status clock-note.service
  journalctl --user -u clock-note.service --no-pager -n 20
}
```

This turns a repeated service check into one command you can inspect and improve. A oneshot service normally becomes inactive after it finishes successfully.

## Watch Out

- Quote function arguments.
- Functions run in the current shell, so `cd` inside a function can leave you in a new directory.
- A failed `cd` does not stop the remaining commands. Prefer a program's explicit directory option when serving files.
- Use `command name` if a function accidentally shadows a real command.

## Docs Pointers

- Run `man bash` and search for `SHELL FUNCTIONS`.
- Read [shell scripting](shell-scripting.md), [script arguments](script-arguments.md), [quoting](quoting.md), [variables](variables.md), and [systemd user services](systemd-user-services.md).
