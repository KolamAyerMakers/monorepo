# if, then, else, fi

## Use

```bash
if [[ -e "$1" ]]; then
  printf 'exists\n'
else
  printf 'missing\n'
fi
```

## What It Does

`if` runs one branch when a test or command succeeds and another branch when it fails. `then`, `else`, and `fi` are part of the same Bash compound command.

## Command Success

```bash
if curl -fsS https://example.org >/dev/null; then
  printf 'up\n'
else
  printf 'down\n'
fi
```

Bash does not require a numeric comparison. It branches on exit status: `0` means success, nonzero means failure.

## File Test

```bash
if [[ -f ~/src/pages/index.md ]]; then
  printf 'homepage source exists\n'
fi
```

`[[ ]]` is Bash's safer test syntax for strings, files, and patterns.

## One-Line Form

```bash
if [[ -d ~/src ]]; then printf 'source exists\n'; fi
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
