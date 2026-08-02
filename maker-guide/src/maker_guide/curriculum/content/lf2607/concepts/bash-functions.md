# Bash Functions

## Core Idea

A Bash function gives a name to a group of shell commands that run in the current shell.

Use functions when you repeat a command sequence but do not need a separate executable script yet.

## Shape

```bash
serve() {
  cd "$HOME/public_html"
  python3 -m http.server "$((10000 + $(id -u)))" --bind 127.0.0.1
}
```

The function name is `serve`. The body runs when you type `serve`, and the foreground server keeps running until you press `Ctrl-C`.

## Arguments

Functions receive arguments as `$1`, `$2`, and `"$@"`, just like scripts.

```bash
page() {
  if [[ "$#" -lt 1 ]]; then
    printf 'usage: page NAME\n' >&2
    return 1
  fi

  micro "$HOME/src/pages/$1.md"
}
```

Use `return` inside a function. Use `exit` only when you want to end the whole shell or script.

## Return Status Versus Output

Functions have two different channels:

- Output: text printed to stdout.
- Return status: success or failure number used by `if`, `&&`, and scripts.

```bash
is_site_source() {
  [[ -f "$HOME/src/pages/index.md" ]]
}

if is_site_source; then
  printf 'source exists\n'
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

## Course Example

```bash
status() {
  systemctl --user status site.service
  journalctl --user -u site.service --no-pager -n 20
}
```

This turns a repeated service check into one command you can inspect and improve.

## Watch Out

- Quote function arguments.
- Functions run in the current shell, so `cd` inside a function can leave you in a new directory.
- Use `command name` if a function accidentally shadows a real command.

## Docs Pointers

- Run `man bash` and search for `SHELL FUNCTIONS`.
- Read [shell scripting](shell-scripting.md), [script arguments](script-arguments.md), [quoting](quoting.md), [variables](variables.md), and [systemd user services](systemd-user-services.md).
