# if, then, else, fi

## Use

```bash
path=/etc/hostname
if [[ -e "$path" ]]; then
  printf 'exists\n'
else
  printf 'missing\n'
fi
```

## What It Does

`if` runs one branch when a test or command succeeds and another branch when it fails. `then`, `else`, and `fi` are part of the same Bash compound command.

## Command Success

```bash
if curl -I --max-time 10 https://example.org; then
  printf 'A response arrived; inspect its HTTP status.\n'
else
  printf 'The request failed; inspect the curl error.\n'
fi
```

Bash does not require a numeric comparison. It branches on exit status: `0` means success, nonzero means failure.

Without curl's `-f` option, an HTTP `404` response normally still gives command status `0`. To require `200`, capture the HTTP code and compare it explicitly.

## File Test

```bash
if [[ -f /etc/hostname ]]; then
  printf 'hostname file exists\n'
fi
```

`[[ ]]` is Bash's safer test syntax for strings, files, and patterns.

## One-Line Form

```bash
if [[ -d /etc ]]; then printf 'directory exists\n'; fi
```

Use this only when it remains readable. Multi-line form is better for learning and for scripts.

## Watch Out

- Every `if` needs a matching `fi`.
- Quote variables inside tests.
- Use `elif` for another condition; do not stack confusing nested `if` blocks too early.
- Put `; then` on the same line if you write a one-liner.

## Docs Pointers

- Run `help if` and `help [[`.
- Read [conditionals](../concepts/conditionals.md), [control flow](../concepts/control-flow.md), [quoting](../concepts/quoting.md), and [one-liners](../concepts/oneliner.md).
